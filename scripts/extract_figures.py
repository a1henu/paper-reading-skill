#!/usr/bin/env python3
"""
extract_figures.py — precise figure extraction for paper-reading reports.

Why this exists
---------------
ML papers compose each figure from many small image tiles + vector drawings,
laid out around the text. Two naive approaches both fail:
  * `pdfimages` dumps raw embedded XObjects → you get dozens of fragments for one
    figure, and *nothing* for vector-only diagrams (architecture flowcharts).
  * `pdftoppm` rasterises a whole page → captions and neighbouring figures /
    body text bleed into the crop.

This tool is caption-anchored. For every "Figure N" caption it:
  1. collects every graphic (image tile + vector-drawing rect) in the caption's
     column, above the caption and below any earlier caption in the same column;
  2. clusters those graphics upward from the caption by vertical whitespace gaps,
     so the cluster directly above the caption == the figure body;
  3. crops the cluster's bounding box (text labels inside the figure are kept
     because they fall inside the graphics bbox; captions/paragraphs are not,
     because we cluster graphics, not text).

Tables are detected but skipped for image extraction (reproduce them as HTML).

Usage
-----
  python3 extract_figures.py <paper.pdf> <outdir> [--dpi 200] [--gap 30] [--full-pages]

Outputs
-------
  <outdir>/fig<N>_p<page>.png         one PNG per detected figure
  <outdir>/fig<N>_p<page>.txt         the figure's FULL original caption (sidecar)
  <outdir>/page<N>.png                full-page renders (only with --full-pages)
  <outdir>/manifest.json              list of {page, fig, status, file, caption_file,
                                       rect, caption}  — caption is the complete,
                                       untruncated caption text

Workflow: run this first, then VIEW every PNG (Read tool) and the manifest, and
embed only the figures that matter — using the FULL caption text (manifest
`caption` field, or the `.txt` sidecar) to write an interpretive 中文 figcaption.
Use --full-pages as a fallback to eyeball anything the detector marked
`no-gfx` / `too-small`, then crop by hand with crop_region() if needed.

Requires PyMuPDF (`pip install pymupdf`).
"""
import sys, re, json, os, argparse
import fitz

CAP_RE = re.compile(r'^\s*(Figure|Fig\.?|Table)\s*(\d+)', re.I)


def spans_text(b):
    return "".join(s["text"] for l in b.get("lines", []) for s in l.get("spans", []))


def block_font(b):
    """Median-ish font size of a text block (0 if empty)."""
    sizes = [s["size"] for l in b.get("lines", []) for s in l.get("spans", [])]
    return round(sum(sizes) / len(sizes), 1) if sizes else 0.0


def gather_caption(cap_block, blocks, cap_boxes):
    """Assemble a figure's FULL caption.

    A caption's first line ("Figure N. ...") lives in `cap_block`, but long
    captions wrap into one or more continuation blocks directly below it. We
    absorb those continuation blocks while they (a) sit immediately under the
    running caption, (b) overlap its horizontal span, (c) share roughly its font
    size (captions are typically set smaller than body text), and (d) are not
    themselves another caption. Returns the concatenated, whitespace-normalised
    caption string.
    """
    cb = cap_block["bbox"]
    cap_sz = block_font(cap_block)
    parts = [spans_text(cap_block)]
    bottom = cb[3]
    # candidate continuation blocks below the caption, in this column, top-down
    below = sorted(
        (b for b in blocks
         if b["bbox"][1] >= cb[3] - 2
         and min(b["bbox"][2], cb[2]) - max(b["bbox"][0], cb[0]) > 10),
        key=lambda b: b["bbox"][1])
    for b in below:
        if b["bbox"] in cap_boxes and b is not cap_block:   # next figure's caption
            break
        if CAP_RE.match(spans_text(b)):                     # another caption starts
            break
        if b["bbox"][1] - bottom > 6:                       # vertical gap → caption ended
            break
        sz = block_font(b)
        if cap_sz and sz and abs(sz - cap_sz) > 0.8:        # font jump → body text
            break
        parts.append(spans_text(b))
        bottom = b["bbox"][3]
    return re.sub(r'\s+', ' ', " ".join(parts)).strip()


def xoverlap(a, b, tol=2):
    """Horizontal overlap of two (x0,y0,x1,y1) boxes exceeds `tol` points."""
    return min(a[2], b[2]) - max(a[0], b[0]) > tol


def crop_region(pdf, page, rect, out, dpi=200):
    """Manual fallback: crop an explicit rect (x0,y0,x1,y1, PDF points) from a 1-based page."""
    doc = fitz.open(pdf)
    pg = doc[page - 1]
    clip = fitz.Rect(*rect) & pg.rect
    pg.get_pixmap(clip=clip, dpi=dpi).save(out)
    return out


def extract(pdf, outdir, dpi=200, gap=30, full_pages=False):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf)
    results = []
    for pno, pg in enumerate(doc):
        W, H = pg.rect.width, pg.rect.height
        HEADER, FOOTER = 0.05 * H, 0.96 * H
        blocks = [b for b in pg.get_text("dict")["blocks"] if b.get("type", 0) == 0]

        caps = []
        for b in blocks:
            m = CAP_RE.match(spans_text(b))
            if m:
                caps.append((m.group(1).lower().startswith("t"),  # is_table
                             int(m.group(2)), b))                  # keep block ref
        if not caps:
            if full_pages:
                pg.get_pixmap(dpi=dpi).save(f"{outdir}/page{pno+1}.png")
            continue

        # graphics: image tiles + non-trivial vector drawing rects,
        # minus full-page backgrounds and header/footer margins
        gfx = []
        for im in pg.get_image_info():
            gfx.append(tuple(im["bbox"]))
        for dr in pg.get_drawings():
            r = dr["rect"]
            if r.width > 3 and r.height > 3:
                gfx.append((r.x0, r.y0, r.x1, r.y1))

        def keep(g):
            w, h = g[2] - g[0], g[3] - g[1]
            if w > 0.95 * W and h > 0.85 * H:        # full-page background rect
                return False
            if g[3] <= HEADER or g[1] >= FOOTER:     # header / footer margin
                return False
            return True
        gfx = [g for g in gfx if keep(g)]
        cap_boxes = [c[2]["bbox"] for c in caps]

        for is_tbl, fignum, cap_block in caps:
            cbb = cap_block["bbox"]
            full_caption = gather_caption(cap_block, blocks, cap_boxes)
            if is_tbl:                                # tables → HTML, not images
                continue
            cx0, cy0, cx1, cy1 = cbb
            col = (cx0, cx1)
            cand = [g for g in gfx
                    if g[3] <= cy0 + 4 and xoverlap(g, (col[0], 0, col[1], 0), tol=15)]
            # don't reach across an earlier caption higher up THIS column
            prev_cap = max([cb[1] for cb in cap_boxes
                            if cb is not cbb and cb[1] < cy0 - 5
                            and xoverlap(cb, (col[0], 0, col[1], 0), tol=15)],
                           default=HEADER)
            cand = [g for g in cand if g[1] >= prev_cap - 1]
            if not cand:
                results.append({"page": pno + 1, "fig": fignum, "status": "no-gfx",
                                "caption": full_caption})
                continue

            # cluster upward from the caption; a whitespace gap > `gap` ends the figure
            cand.sort(key=lambda g: -g[3])
            cluster = [cand[0]]
            top = cand[0][1]
            for g in cand[1:]:
                if g[3] >= top - gap:
                    cluster.append(g)
                    top = min(top, g[1])
                else:
                    break

            x0 = min(g[0] for g in cluster); x1 = max(g[2] for g in cluster)
            y0 = min(g[1] for g in cluster); y1 = cy0 - 2
            pad = 5
            clip = fitz.Rect(max(pg.rect.x0, x0 - pad), max(pg.rect.y0, y0 - pad),
                             min(pg.rect.x1, x1 + pad), min(pg.rect.y1, y1 + pad))
            if clip.width < 40 or clip.height < 30:
                results.append({"page": pno + 1, "fig": fignum, "status": "too-small",
                                "rect": [round(v, 1) for v in clip], "caption": full_caption})
                continue
            stem = f"fig{fignum}_p{pno+1}"
            pg.get_pixmap(clip=clip, dpi=dpi).save(f"{outdir}/{stem}.png")
            with open(f"{outdir}/{stem}.txt", "w") as cf:        # caption sidecar
                cf.write(full_caption + "\n")
            results.append({"page": pno + 1, "fig": fignum, "status": "ok",
                            "file": f"{stem}.png", "caption_file": f"{stem}.txt",
                            "rect": [round(v, 1) for v in clip], "caption": full_caption})

        if full_pages:
            pg.get_pixmap(dpi=dpi).save(f"{outdir}/page{pno+1}.png")

    with open(f"{outdir}/manifest.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Caption-anchored PDF figure extractor")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--gap", type=int, default=30,
                    help="vertical whitespace (pt) that separates a figure from content above it")
    ap.add_argument("--full-pages", action="store_true",
                    help="also dump full-page renders as a verification fallback")
    a = ap.parse_args()
    extract(a.pdf, a.outdir, dpi=a.dpi, gap=a.gap, full_pages=a.full_pages)
