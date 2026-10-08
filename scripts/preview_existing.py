#!/usr/bin/env python3
"""Create an isolated UI preview from selected existing reports without editing sources.

Usage:
  python3 scripts/preview_existing.py --source /path/to/old/site \
      --selection examples/preview-selection.json --output /path/to/new/preview

Requires BeautifulSoup (bs4). Selection is an array of reviewed metadata records;
read dates must come from the source reading record, never the preview timestamp.
The output must be new. This is a preview helper, not an in-place bulk migration.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from build_library import build, script_json

ROOT = Path(__file__).resolve().parents[1]


def preview(source: Path, selection: Path, output: Path) -> None:
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise ValueError(f"Output already exists; choose a new preview directory: {output}")
    records = json.loads(selection.read_text())
    if not isinstance(records, list) or not records:
        raise ValueError("Selection must be a non-empty array of reviewed metadata")
    for record in records:
        slug = record["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"Invalid slug: {slug}")
        if not (source / "reports" / f"{slug}.html").is_file():
            raise ValueError(f"Missing source report: {slug}")
    template = BeautifulSoup((ROOT / "templates/report.html").read_text(), "html.parser")
    (output / "reports").mkdir(parents=True)
    (output / "metadata").mkdir()
    for record in records:
        slug = record["slug"]
        original = source / "reports" / f"{slug}.html"
        soup = BeautifulSoup(original.read_text(), "html.parser")
        main = soup.select_one("main")
        header = soup.select_one(".meta-bar")
        if main is None or header is None:
            raise ValueError(f"{slug}: expected main and .meta-bar")
        record = {**record, "tagging_basis": "existing-report", "source_report": str(original)}
        for script in soup.select("script"):
            if script.get("src") or "mermaid" in script.get_text():
                script.decompose()
        for src, asynchronous in [
            ("../assets/vendor/mathjax/tex-mml-chtml.js", True),
            ("../assets/vendor/mermaid.min.js", False),
            ("../assets/site.js", False),
        ]:
            script = soup.new_tag("script", src=src)
            script["async" if asynchronous else "defer"] = ""
            soup.head.append(script)
        for name in ["reader-topbar", "reading-progress", "skip-link"]:
            element = template.select_one("." + name)
            soup.body.insert(0, BeautifulSoup(str(element), "html.parser"))
        soup.body["class"] = list(dict.fromkeys(soup.body.get("class", []) + ["report-page"]))
        main["id"] = "report-main"
        for a in header.select(".back-to-index"):
            a.decompose()
        label = soup.new_tag("span", attrs={"class": "eyebrow"})
        label.string = "PAPER NOTES · " + record["venue"] + " " + str(record["year"])
        header.insert(0, label)
        lede = soup.new_tag("p", attrs={"class": "report-lede"})
        lede.string = record["summary_zh"]
        header.h1.insert_after(lede)
        tags = soup.new_tag("div", attrs={"class": "report-tags", "aria-label": "文章标签"})
        for tag in record["tags"]:
            a = soup.new_tag("a", href="../index.html?tag=" + tag, attrs={"class": "tag"})
            a.string = tag; tags.append(a)
        header.append(tags)
        keywords = soup.new_tag("meta", attrs={"name": "keywords", "content": ", ".join(record["keywords"])})
        soup.head.append(keywords)
        mobile = BeautifulSoup(str(template.select_one(".mobile-toc")), "html.parser")
        main.insert_before(mobile)
        note = soup.new_tag("p", attrs={"class": "source preview-note"})
        note.string = "版式预览 · 沿用原阅读笔记的内容与核对时点；本次新增标签，未重新核验论文数值和开源状态。"
        main.insert(0, note)
        arxiv = record["links"]["arxiv"]
        pdf = arxiv.replace("/abs/", "/pdf/")
        figures = []
        for i, figure in enumerate(main.select("figure"), 1):
            image = figure.find("img")
            if image is None:
                continue
            ancestor = image.parent
            if ancestor.name == "a":
                ancestor.unwrap()
            rel = urlsplit(image["src"])
            if rel.scheme or rel.netloc:
                raise ValueError(f"{slug}: preview expects local images: {image['src']}")
            image_source = (original.parent / unquote(rel.path)).resolve()
            if not image_source.is_relative_to(source / "assets") or not image_source.is_file():
                raise ValueError(f"{slug}: invalid image path {image_source}")
            target = output / image_source.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_source, target)
            image["loading"] = "eager" if i == 1 else "lazy"
            image["decoding"] = "async"
            figure["class"] = list(dict.fromkeys(figure.get("class", []) + ["visual-panel"]))
            title = soup.new_tag("div", attrs={"class": "visual-heading"})
            title.string = "核心一张图" if i == 1 else f"图像证据 / {i:02d}"
            badge = soup.new_tag("span", attrs={"class": "visual-kind"}); badge.string = "论文原图"
            title.append(badge); figure.insert(0, title)
            match = re.search(r"fig(\d+)", image_source.name)
            number = match.group(1) if match else str(i)
            manifest_path = image_source.parent / "manifest.json"
            page = None
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text())
                candidates = [r for r in manifest if str(r.get("fig")) == number and r.get("file")]
                exact = [r for r in candidates if image_source.name in (r.get("file"), r.get("corrected_file"))]
                candidates = exact or candidates
                pages = {r["page"] for r in candidates}
                if len(pages) == 1:
                    page = pages.pop()
            source_url = pdf + (f"#page={page}" if page else "")
            source_line = soup.new_tag("div", attrs={"class": "figure-source"})
            link = soup.new_tag("a", href=source_url, target="_blank", rel="noopener")
            link.string = f"来源：原文 Figure {number}" + (f" · PDF 第 {page} 页" if page else " · 见原阅读笔记图注")
            source_line.append(link); figure.append(source_line)
            figures.append({"kind": "original", "file": str(target.relative_to(output)), "source": source_url, "figure": number, "page": page})
        speedread = soup.select_one("#speedread")
        if speedread and speedread.find("figure"):
            core = speedread.find("figure").extract()
            speedread.insert(0, core)
        addition_path = selection.parent / "preview-additions" / f"{slug}.html"
        if addition_path.exists():
            additions = BeautifulSoup(addition_path.read_text(), "html.parser")
            for addition in list(additions.select("figure[data-preview-section]")):
                section = soup.find(id=addition["data-preview-section"])
                if section is None:
                    raise ValueError(f"{slug}: missing section for preview illustration")
                kind = addition.get("data-visual-kind", "explanation")
                del addition["data-preview-section"]
                section.append(addition.extract())
                figures.append({"kind": kind, "source": "existing-report", "purpose": "preview illustration"})
        # Small evidence sidecars remain local. Original PDFs outside the site become arXiv links.
        for a in soup.select("a[href]"):
            href = a["href"]
            url = urlsplit(href)
            if "disabled" in a.get("class", []):
                del a["href"]; a["aria-disabled"] = "true"
                continue
            if a.get("target") == "_blank":
                a["rel"] = "noopener"
            if url.scheme or url.netloc or not url.path or url.path == "../index.html":
                continue
            asset = (original.parent / unquote(url.path)).resolve()
            if asset.is_relative_to(source / "assets") and asset.is_file():
                dest = output / asset.relative_to(source)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.copy2(asset, dest)
            elif asset.suffix.lower() == ".pdf":
                a["href"] = pdf; a.string = "原文 PDF"
            else:
                raise ValueError(f"{slug}: unhandled local link {href}; review it before migrating")
        record["visuals"] = figures
        metadata = soup.new_tag("script", attrs={"type": "application/json", "id": "paper-metadata"})
        metadata.string = script_json(record); soup.body.append(metadata)
        (output / "metadata" / f"{slug}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        (output / "reports" / f"{slug}.html").write_text(str(soup))
        print(f"Previewed {slug}: {len(figures)} figures", flush=True)
    print(build(output, "视觉生成与智能体", f"从一个想法到可编辑的作品。{len(records)} 篇既有阅读笔记，体验新版图文阅读与标签归档。", False, False))
    print(build(output, None, None, True, False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    preview(args.source, args.selection, args.output)


if __name__ == "__main__":
    main()
