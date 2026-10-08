#!/usr/bin/env python3
"""Build a static paper library from metadata/*.json; no network or LLM calls.

Usage:
  python3 scripts/build_library.py /path/to/topic --title "我的论文库"
  python3 scripts/build_library.py /path/to/topic --check
Existing reports and metadata are never rewritten. Changed generated files get
timestamped backups. Unmanaged legacy indexes require --replace-index.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
from collections import Counter
from datetime import date, datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKER = "paper-reading:managed-index"
FIELDS = ["slug", "title", "year", "venue", "authors", "summary_zh", "tags", "keywords", "read_at", "report"]


def script_json(value: object) -> str:
    """JSON safe to embed in a script element, including untrusted paper titles."""
    return json.dumps(value, ensure_ascii=False, indent=2).replace("<", r"\u003c").replace(">", r"\u003e").replace("&", r"\u0026")


def text_field(record: dict, name: str, required: bool = True) -> str:
    value = record.get(name, "")
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f"{name}: expected a non-empty string")
    return value.strip()


def string_list(record: dict, name: str, low: int, high: int = 1000) -> list[str]:
    value = record.get(name)
    if not isinstance(value, list) or any(not isinstance(s, str) or not s.strip() for s in value):
        raise ValueError(f"{name}: expected an array of non-empty strings")
    values = list(dict.fromkeys(s.strip() for s in value))
    if not low <= len(values) <= high:
        raise ValueError(f"{name}: expected {low}–{high} distinct entries, got {len(values)}")
    return values


def local_file(topic: Path, path: str) -> Path:
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or "\\" in path or parsed.path.startswith("/"):
        raise ValueError(f"expected a relative local asset path: {path}")
    result = (topic / unquote(parsed.path)).resolve()
    if not result.is_relative_to(topic.resolve()) or not result.is_file():
        raise ValueError(f"missing file or path outside topic: {path}")
    return result


def load_record(path: Path, topic: Path, aliases: dict[str, str]) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("metadata must be a JSON object")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if "read_at" not in raw:
        raise ValueError("read_at is required; use null only for an unknown legacy date")
    slug = text_field(raw, "slug")
    if not SLUG.fullmatch(slug) or path.stem != slug:
        raise ValueError("slug must be kebab-case and match the metadata filename")
    tags = [aliases.get(s.lower(), s.lower()) for s in string_list(raw, "tags", 3, 8)]
    tags = list(dict.fromkeys(tags))
    if len(tags) < 3 or any(not SLUG.fullmatch(t) for t in tags):
        raise ValueError("tags must contain 3–8 distinct canonical kebab-case tags")
    record = dict(raw)  # Preserve reproduction/evidence/custom fields for later archiving.
    record.update({
        "slug": slug, "title": text_field(raw, "title"),
        "summary_zh": text_field(raw, "summary_zh"),
        "venue": text_field(raw, "venue", required=False),
        "authors": string_list(raw, "authors", 1),
        "tags": tags, "keywords": string_list(raw, "keywords", 3, 8),
        "read_at": raw.get("read_at"),
        "report": f"reports/{slug}.html",
    })
    year = raw.get("year")
    if year is not None and (type(year) is not int or not 1800 <= year <= 2200):
        raise ValueError("year must be an integer (1800–2200) or null")
    record["year"] = year
    if record["read_at"] is not None:
        if not isinstance(record["read_at"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", record["read_at"]):
            raise ValueError("read_at must be YYYY-MM-DD, or null for an unknown legacy date")
        date.fromisoformat(record["read_at"])
    local_file(topic, record["report"])
    cover = raw.get("cover")
    if cover is not None:
        if not isinstance(cover, str):
            raise ValueError("cover must be a relative path or null")
        local_file(topic, cover)
    record["cover"] = cover
    links = raw.get("links", {})
    if not isinstance(links, dict):
        raise ValueError("links must be an object")
    for name, link in links.items():
        if link is not None and (not isinstance(link, str) or urlsplit(link).scheme not in ("https", "http") or not urlsplit(link).netloc):
            raise ValueError(f"links.{name} must be an http(s) URL or null")
    record["links"] = links
    return record


def csv_text(papers: list[dict]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(FIELDS)
    for paper in papers:
        cells = []
        for name in FIELDS:
            v = paper.get(name)
            s = "; ".join(v) if isinstance(v, list) else str(v) if v is not None else ""
            cells.append("'" + s if re.match(r"^\s*[=+@-]", s) else s)
        writer.writerow(cells)
    return "\ufeff" + output.getvalue()


def render_card(p: dict) -> str:
    title, slug, report = (escape(p[k], quote=True) for k in ("title", "slug", "report"))
    if p["cover"]:
        cover = f'<img src="{escape(p["cover"], quote=True)}" alt="{title} · 核心图" loading="lazy" decoding="async">'
    else:
        cover = '<div class="cover-placeholder"><b>论文笔记</b><span>READ / THINK / CONNECT</span></div>'
    tags = "".join(f'<button type="button" class="tag" data-tag="{escape(t)}" aria-pressed="false">{escape(t)}</button>' for t in p["tags"])
    venue = escape(" · ".join(str(v) for v in [p["venue"], p["year"]] if v))
    read_date = escape(p["read_at"]) + " · 阅读记录" if p["read_at"] else "阅读日期未记录"
    return f'''<article class="paper-card" data-paper-slug="{slug}">
  <a class="paper-cover" href="{report}" aria-label="阅读：{title}">{cover}</a>
  <div class="paper-card-body">
    <div class="paper-meta"><span>{venue}</span><button type="button" class="favorite-button js-only" data-favorite="{slug}" data-title="{title}" aria-pressed="false" aria-label="收藏：{title}">☆</button></div>
    <h2><a href="{report}">{title}</a></h2>
    <p class="paper-summary">{escape(p["summary_zh"])}</p>
    <div class="paper-tags">{tags}</div>
    <div class="paper-footer"><span>{read_date}</span><a href="{report}">打开笔记 ↗</a></div>
  </div>
</article>'''


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[str] = []
        self.ids: list[str] = []
        self.image_alts: list[str | None] = []
        self.title = ""
        self.in_title = False
        self.in_metadata = False
        self.metadata_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.append(attr["id"])
        if tag == "title":
            self.in_title = True
        if tag == "script" and attr.get("id") == "paper-metadata":
            self.in_metadata = True
        if tag in ("script", "img", "source") and attr.get("src"):
            self.refs.append(attr["src"])
        if tag in ("a", "link") and attr.get("href"):
            self.refs.append(attr["href"])
        if tag == "img":
            self.image_alts.append(attr.get("alt"))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script":
            self.in_metadata = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.in_metadata:
            self.metadata_text += data


def check_report_metadata(topic: Path, papers: list[dict]) -> list[str]:
    errors = []
    for paper in papers:
        page = PageParser()
        page.feed((topic / paper["report"]).read_text(encoding="utf-8"))
        try:
            embedded = json.loads(page.metadata_text)
        except ValueError:
            errors.append(f'{paper["report"]}: missing/invalid #paper-metadata JSON')
            continue
        if not isinstance(embedded, dict) or any(embedded.get(k) != paper[k] for k in ("slug", "tags", "keywords", "read_at")):
            errors.append(f'{paper["report"]}: embedded slug/tags/keywords/read_at differ from canonical metadata; regenerate the report metadata block')
    return errors


def check_pages(topic: Path, files: list[Path], *, skip_generated: bool = False) -> list[str]:
    errors: list[str] = []
    for file in files:
        text = file.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        name = file.relative_to(topic)
        if re.search(r"\{\{[^{}\n]{0,120}\}\}", text):
            errors.append(f"{name}: unresolved template placeholder")
        if len(parser.ids) != len(set(parser.ids)):
            errors.append(f"{name}: duplicate element IDs")
        if any(not alt for alt in parser.image_alts):
            errors.append(f"{name}: image missing meaningful alt text")
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                if url.scheme.lower() in ("javascript", "vbscript"):
                    errors.append(f"{name}: unsafe link scheme")
                continue
            if url.path.startswith("/"):
                errors.append(f"{name}: non-portable absolute local link {ref}")
                continue
            target = (file.parent / unquote(url.path)).resolve() if url.path else file
            if skip_generated and (target == topic / "index.html" or target.is_relative_to(topic / "assets")):
                # Missing figures still fail below; only shared builder-owned files are deferred.
                relative = target.relative_to(topic)
                if str(relative) in ("index.html", "assets/style.css", "assets/site.js") or str(relative).startswith("assets/vendor/"):
                    continue
            if not target.is_file():
                errors.append(f"{name}: missing relative resource {ref}")
            elif url.fragment and target.suffix == ".html":
                dest = parser if target == file else PageParser()
                if target != file:
                    dest.feed(target.read_text(encoding="utf-8"))
                if unquote(url.fragment) not in dest.ids:
                    errors.append(f"{name}: missing anchor {ref}")
    return errors


def write_generated(path: Path, data: bytes) -> None:
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        shutil.copy2(path, path.with_name(path.name + ".bak." + stamp))
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build(topic: Path, title: str | None, description: str | None, check: bool, replace_index: bool) -> dict:
    topic = topic.resolve()
    paths = sorted((topic / "metadata").glob("*.json"))
    if not paths:
        raise ValueError("no metadata/*.json files; create one metadata record per report first")
    taxonomy = json.loads((ROOT / "reference" / "taxonomy.json").read_text())
    papers = []
    for path in paths:
        try:
            papers.append(load_record(path, topic, taxonomy["aliases"]))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{path.name}: {exc}") from exc
    indexed = {p["report"] for p in papers}
    orphans = {str(p.relative_to(topic)) for p in (topic / "reports").glob("*.html")} - indexed
    if orphans:
        raise ValueError("reports missing metadata (refusing to drop them from the index): " + ", ".join(sorted(orphans)))
    config_path = topic / "library.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError("library.json must be an object")
    config = {"title": title or config.get("title", topic.name), "description": description if description is not None else config.get("description", "收藏值得反复阅读的论文，记录方法、证据与下一步问题。")}
    if any(not isinstance(value, str) for value in config.values()):
        raise ValueError("library title and description must be strings")
    papers.sort(key=lambda p: (p["read_at"] or "", p["slug"]), reverse=True)
    catalog = {"schema_version": 1, **config, "papers": papers}
    pages = [topic / p["report"] for p in papers] + sorted((topic / "comparisons").glob("*.html"))
    if check:
        errors = check_pages(topic, [topic / "index.html", *pages]) + check_report_metadata(topic, papers)
        disk = json.loads((topic / "catalog.json").read_text())
        if disk != catalog:
            errors.append("catalog.json is stale; rebuild from metadata")
        if errors:
            raise ValueError("\n".join(errors))
        return {"papers": len(papers), "pages_checked": len(pages) + 1, "status": "ok"}
    index = topic / "index.html"
    if index.exists() and MARKER not in index.read_text() and not replace_index:
        raise ValueError("existing index is unmanaged; inspect it first, then use --replace-index to back up and replace")
    errors = check_pages(topic, pages, skip_generated=True) + check_report_metadata(topic, papers)
    if errors:
        raise ValueError("\n".join(errors))
    counts = Counter(t for p in papers for t in p["tags"])
    tag_html = "".join(f'<button type="button" class="tag-filter" data-tag="{escape(t)}" aria-pressed="false">{escape(t)} <span>{n}</span></button>' for t, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])))
    comparisons = []
    for path in sorted((topic / "comparisons").glob("*.html")):
        parsed = PageParser()
        parsed.feed(path.read_text())
        comparisons.append(f'<a href="{escape(str(path.relative_to(topic)), quote=True)}">{escape(parsed.title or path.stem)} ↗</a>')
    replacements = {
        "TITLE": escape(config["title"]), "DESCRIPTION": escape(config["description"]),
        "COUNT": str(len(papers)), "TAG_FILTERS": tag_html,
        "CARDS": "\n".join(render_card(p) for p in papers),
        "COMPARISONS": '<section class="comparison-links"><h2>串起来读 · 论文对比</h2>' + "".join(comparisons) + "</section>" if comparisons else "",
        "CATALOG_JSON": script_json(catalog),
    }
    template = (ROOT / "templates" / "index.html").read_text()
    html = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: replacements[m[1]], template)
    outputs = {
        "library.json": json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        "catalog.json": json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        "catalog.csv": csv_text(papers),
        "index.html": html,
    }
    for name, text in outputs.items():
        write_generated(topic / name, text.encode("utf-8"))
    for name in ("style.css", "site.js"):
        write_generated(topic / "assets" / name, (ROOT / "templates" / name).read_bytes())
    vendor = ROOT / "templates" / "vendor"
    for path in sorted(vendor.rglob("*")):
        if path.is_file():
            write_generated(topic / "assets" / "vendor" / path.relative_to(vendor), path.read_bytes())
    return {"papers": len(papers), "tags": len(counts), "index": str(index), "status": "built"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("topic", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--check", action="store_true", help="Validate generated pages, relative links, anchors, and catalog freshness without writing")
    parser.add_argument("--replace-index", action="store_true", help="Back up and replace a reviewed legacy index")
    args = parser.parse_args()
    try:
        result = build(args.topic, args.title, args.description, args.check, args.replace_index)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
