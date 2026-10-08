from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_library", ROOT / "scripts/build_library.py")
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)


def add_paper(topic: Path, slug: str = "one", **updates) -> dict:
    (topic / "reports").mkdir(exist_ok=True)
    (topic / "metadata").mkdir(exist_ok=True)
    record = {
        "schema_version": 1, "slug": slug, "title": "A paper", "authors": ["An Author"],
        "year": 2026, "venue": "arXiv", "summary_zh": "一篇具体的论文阅读笔记。",
        "tags": ["multimodal", "t2i", "agent"], "keywords": ["生成", "图像", "智能体"],
        "read_at": "2026-10-08", "cover": None, "links": {}, **updates,
    }
    (topic / "metadata" / f"{slug}.json").write_text(json.dumps(record, ensure_ascii=False))
    aliases = json.loads((ROOT / "reference/taxonomy.json").read_text())["aliases"]
    embedded = {**record, "tags": list(dict.fromkeys(aliases.get(t.lower(), t.lower()) for t in record["tags"]))}
    (topic / "reports" / f"{slug}.html").write_text('<!doctype html><html><head><title>Paper</title></head><body><h1 id="intro">正文</h1><a href="../index.html">索引</a><script type="application/json" id="paper-metadata">' + library.script_json(embedded) + '</script></body></html>')
    return record


def build(topic: Path, **kwargs):
    return library.build(topic, None, None, kwargs.get("check", False), kwargs.get("replace_index", False))


def test_build_preserves_old_papers_and_is_idempotent(tmp_path):
    add_paper(tmp_path)
    original = (tmp_path / "reports/one.html").read_bytes()
    assert build(tmp_path)["papers"] == 1
    assert build(tmp_path, check=True)["status"] == "ok"
    index = tmp_path / "index.html"
    before = index.stat().st_mtime_ns
    build(tmp_path)
    assert index.stat().st_mtime_ns == before
    assert not list(tmp_path.glob("*.bak.*"))
    add_paper(tmp_path, "two", read_at="2026-10-07")
    build(tmp_path)
    assert (tmp_path / "reports/one.html").read_bytes() == original
    assert list(tmp_path.glob("index.html.bak.*"))
    papers = json.loads((tmp_path / "catalog.json").read_text())["papers"]
    assert [p["slug"] for p in papers] == ["one", "two"]
    assert papers[0]["tags"] == ["multimodal", "image-generation", "llm-agent"]


def test_escaping_exports_and_custom_metadata(tmp_path):
    add_paper(tmp_path, title='</script><script>alert("x")</script>', summary_zh='=HYPERLINK("evil")', notes={"value": 2})
    build(tmp_path)
    html = (tmp_path / "index.html").read_text()
    assert '</script><script>alert("x")</script>' not in html
    assert r"\u003c/script\u003e" in html
    catalog = json.loads((tmp_path / "catalog.json").read_text())
    assert catalog["papers"][0]["notes"] == {"value": 2}
    csv = (tmp_path / "catalog.csv").read_text()
    assert "'=HYPERLINK" in csv
    assert csv.startswith("\ufeff")


@pytest.mark.parametrize("updates", [
    {"tags": ["a", "b"]}, {"tags": ["t2i", "text-to-image", "image-generation"]},
    {"tags": ["a", "b", "含空 格"]}, {"keywords": ["one"]},
    {"links": {"code": "javascript:alert(1)"}}, {"cover": "../outside.png"},
    {"read_at": "2026-02-30"}, {"read_at": "20261008"}, {"year": True},
])
def test_invalid_metadata_fails_before_writing(tmp_path, updates):
    add_paper(tmp_path, **updates)
    with pytest.raises(ValueError):
        build(tmp_path)
    assert not (tmp_path / "index.html").exists()


def test_unindexed_reports_and_legacy_index_are_not_silently_lost(tmp_path):
    add_paper(tmp_path)
    (tmp_path / "reports/orphan.html").write_text("Existing report")
    with pytest.raises(ValueError, match="missing metadata"):
        build(tmp_path)
    add_paper(tmp_path, "orphan")
    (tmp_path / "index.html").write_text("Custom navigation")
    with pytest.raises(ValueError, match="unmanaged"):
        build(tmp_path)
    assert (tmp_path / "index.html").read_text() == "Custom navigation"
    build(tmp_path, replace_index=True)
    assert next(tmp_path.glob("index.html.bak.*")).read_text() == "Custom navigation"


def test_missing_assets_anchors_and_stale_catalog(tmp_path):
    add_paper(tmp_path)
    page = tmp_path / "reports/one.html"
    page.write_text('<img src="../assets/no.png" alt="图"><a href="#missing">章节</a>')
    with pytest.raises(ValueError, match="missing relative resource"):
        build(tmp_path)
    add_paper(tmp_path)
    build(tmp_path)
    add_paper(tmp_path, title="Changed title")
    with pytest.raises(ValueError, match="stale"):
        build(tmp_path, check=True)


def test_comparison_links_are_preserved(tmp_path):
    add_paper(tmp_path)
    (tmp_path / "comparisons").mkdir()
    (tmp_path / "comparisons/routes.html").write_text('<title>路径对比</title><a href="../reports/one.html#intro">Paper</a>')
    build(tmp_path)
    assert 'href="comparisons/routes.html"' in (tmp_path / "index.html").read_text()
    assert build(tmp_path, check=True)["pages_checked"] == 3


def test_unknown_legacy_read_date_is_not_invented(tmp_path):
    add_paper(tmp_path, read_at=None)
    build(tmp_path)
    assert "阅读日期未记录" in (tmp_path / "index.html").read_text()
    assert json.loads((tmp_path / "catalog.json").read_text())["papers"][0]["read_at"] is None


def test_stale_report_tags_fail_before_publishing(tmp_path):
    record = add_paper(tmp_path)
    record["tags"] = ["multimodal", "graphic-design", "llm-agent"]
    (tmp_path / "metadata/one.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="embedded"):
        build(tmp_path)
    assert not (tmp_path / "index.html").exists()
