"""Browser acceptance on the isolated, real-report preview. No live web server."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
SITE = Path(os.environ.get("PAPER_READING_SITE", "~/reading-library")).expanduser().resolve()
ARTIFACTS = ROOT / "tests/artifacts"


@pytest.fixture(scope="module")
def browser():
    if not (SITE / "index.html").exists():
        pytest.skip(f"Preview missing at {SITE}; generate it externally and set PAPER_READING_SITE")
    ARTIFACTS.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--run-all-compositor-stages-before-draw", "--disable-new-content-rendering-timeout"])
        yield browser
        browser.close()


def test_search_tags_sort_favorites_exports_and_views(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto((SITE / "index.html").as_uri())
    expect(page.locator(".paper-card:visible")).to_have_count(3)
    page.locator("#paper-search").fill("可编辑 HTML")
    expect(page.locator(".paper-card:visible")).to_have_count(1)
    page.locator("#clear-filters").click()
    page.locator('#tag-filters [data-tag="graphic-design"]').click()
    page.locator('#tag-filters [data-tag="llm-agent"]').click()
    expect(page.locator(".paper-card:visible")).to_have_count(2)
    page.reload()
    expect(page.locator(".paper-card:visible")).to_have_count(2)
    page.locator("#paper-search").fill("no-result-123")
    expect(page.locator("#empty-state")).to_be_visible()
    page.locator("#empty-reset").click()
    page.locator("#paper-search").fill("UTPC")
    expect(page.locator('.paper-card:visible')).to_have_count(1)
    page.locator('[data-favorite="visioncreator"]').click()
    page.locator("#clear-filters").click()
    page.locator('[data-shelf="favorites"]').click()
    expect(page.locator('.paper-card:visible')).to_have_count(1)
    page.reload()
    expect(page.locator('[data-favorite="visioncreator"]')).to_have_attribute("aria-pressed", "true")
    with page.expect_download() as downloaded:
        page.locator('[data-export="json"]').click()
    content = json.loads(Path(downloaded.value.path()).read_text())
    assert len(content["papers"]) == 1 and content["papers"][0]["favorite"] is True
    with page.expect_download() as downloaded:
        page.locator('[data-export="csv"]').click()
    csv = Path(downloaded.value.path()).read_text()
    assert "UTPC" in csv and "Editable Visual Design" not in csv
    page.locator("#clear-filters").click()
    page.locator("#paper-sort").select_option("year")
    assert page.locator(".paper-card").last.get_attribute("data-paper-slug") == "paper2poster"
    page.locator('[data-view="list"]').click()
    expect(page.locator("#paper-grid")).to_have_class("paper-grid is-list")
    page.reload()
    expect(page.locator("#paper-grid")).to_have_class("paper-grid is-list")
    page.locator('[data-view="grid"]').click()
    page.locator("#clear-filters").click()
    page.screenshot(path=str(ARTIFACTS / "library-desktop.png"), full_page=True)
    assert not errors, errors
    context.close()


def test_reader_figures_toc_type_print_and_mobile(browser):
    context = browser.new_context(viewport={"width": 1520, "height": 980})
    page = context.new_page()
    errors, failed = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("requestfailed", lambda req: failed.append(req.url))
    page.goto((SITE / "reports/editable-visual-design.html").as_uri())
    page.wait_for_function("document.querySelectorAll('.mermaid svg').length >= 2")
    expect(page.locator(".report-tags a")).to_have_count(4)
    img = page.locator("#speedread figure img").first
    img.scroll_into_view_if_needed()
    expect(img).to_be_visible()
    img.click()
    expect(page.locator("dialog[open]")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("dialog[open]")).to_have_count(0)
    expect(img).to_be_focused()
    page.locator('[data-action="font-up"]').click()
    assert page.locator("main").evaluate("e=>getComputedStyle(e).fontSize") == "21px"
    page.locator('[data-action="focus"]').click()
    expect(page.locator(".toc-float")).not_to_be_visible()
    page.locator('[data-action="focus"]').click()
    page.locator('.toc-float a[href="#exp"]').click()
    page.wait_for_function("document.querySelector('.toc-float a[href=\"#exp\"]').getAttribute('aria-current') === 'location'")
    assert page.locator("#exp").evaluate("e=>e.getBoundingClientRect().top") >= 55
    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    assert page.locator("main details:not([open])").count() == 0
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.locator("main details:not([open])").count() > 0
    diagram = page.locator('#walkthrough figure > svg')
    diagram.scroll_into_view_if_needed()
    diagram.click()
    expect(page.locator('dialog[open] img')).to_be_visible()
    page.wait_for_function("document.querySelector('dialog img').complete && document.querySelector('dialog img').naturalWidth > 0")
    page.keyboard.press("Escape")
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    page.screenshot(path=str(ARTIFACTS / "report-desktop.png"))
    for width in [390, 768]:
        page.set_viewport_size({"width": width, "height": 844})
        expect(page.locator(".mobile-toc")).to_be_visible()
        page.locator(".mobile-toc summary").click()
        page.locator('.mobile-toc a[href="#method"]').click()
        expect(page.locator(".mobile-toc")).not_to_have_attribute("open", "")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"overflow at {width}"
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(ARTIFACTS / "report-mobile.png"))
    page.goto((SITE / "reports/visioncreator.html").as_uri())
    page.wait_for_selector("mjx-container")
    page.wait_for_function("document.querySelectorAll('.mermaid svg').length >= 2")
    expect(page.locator('#exp figure > svg')).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    # Force lazy images to load before checking the actual image resources.
    page.evaluate("document.querySelectorAll('figure img').forEach(i=>i.loading='eager')")
    page.wait_for_function("[...document.querySelectorAll('figure img')].every(i=>i.complete && i.naturalWidth > 0)")
    assert not errors, errors
    assert not failed, failed
    context.close()


def test_mobile_library_no_js_and_denied_storage(browser):
    context = browser.new_context(viewport={"width": 390, "height": 844})
    context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}})")
    page = context.new_page()
    page.goto((SITE / "index.html").as_uri())
    expect(page.locator('.paper-card:visible')).to_have_count(3)
    page.locator('[data-favorite="paper2poster"]').click()
    expect(page.locator(".toast")).to_contain_text("未允许保存")
    page.locator('[data-shelf="favorites"]').click()
    expect(page.locator('.paper-card:visible')).to_have_count(1)
    page.locator("#clear-filters").click()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    page.screenshot(path=str(ARTIFACTS / "library-mobile.png"), full_page=True)
    context.close()
    offline = browser.new_context(java_script_enabled=False)
    page = offline.new_page()
    page.goto((SITE / "index.html").as_uri())
    expect(page.locator('.paper-card:visible')).to_have_count(3)
    page.locator('h2 a').first.click()
    expect(page.locator("main")).to_be_visible()
    expect(page.locator('.report-tags a')).to_have_count(4)
    offline.close()
