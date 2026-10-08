# paper-reading

A [Claude Code](https://claude.com/claude-code) skill that turns research papers (PDF / arXiv link / title) into in-depth **Chinese explainer websites** plus reproduction guides.

For each paper it produces a self-contained HTML report covering:

- **Metadata bar** — title, authors, venue/year, and quick links to arXiv/PDF, code, checkpoints, project page, datasets.
- **TL;DR + 5 分钟速读** and the single most important figure.
- **Intro & motivation** — the gap the paper fills.
- **Related-work lineage** — a Mermaid timeline placing the paper in its field.
- **Method** — an equation-by-equation walkthrough (LaTeX via MathJax + 中文 explanation of every symbol).
- **Experiments** — result tables reproduced as HTML, key trends redrawn as charts.
- **可视化效果** and a **复现指南** (environment, repo layout, data prep, train/inference commands, VRAM needs, pitfalls).

It also generates a searchable **reading library** and — for ≥2 related papers — a **comparison page** with a lineage diagram and side-by-side table.

The library has multi-word search (title/author/summary/keywords/tags), tag intersection,
date/year/title sorting, card/list views, browser-local favorites and filtered JSON/CSV
exports. Every read saves **3–8 canonical tags + 3–8 keywords** in an individual JSON
sidecar. Rebuilding the library includes previous readings as well as the new batch.

The light reading interface includes a compact toolbar, scroll-aware contents,
mobile contents, font size controls, focus mode, image/SVG zoom, code copy and print
support. Reports lead with a core image, then explain methods and evidence through
original figures, diagrams and properly sourced charts. Missing data stays missing.

Reports are 中文 prose with English file/dir names. The caption-anchored extractor
(`scripts/extract_figures.py`) estimates figure crops and preserves original captions;
the crops still require visual and caption/page verification. Reading a paper does
not clone or execute its research code. Local report generation and validation run
normally. Reproduction commands quoted from the paper's README are marked unexecuted.

## Layout

```
SKILL.md                 # skill definition + workflow
reference/
  workflow.md            # detailed per-section guidance
  orchestration.md       # multi-agent fan-out / cluster patterns
  visual-report.md       # illustration planning, source attribution, UX acceptance
  metadata.md            # durable metadata, tags and archive contract
  taxonomy.json          # starter vocabulary + aliases; precise new tags are allowed
scripts/
  extract_figures.py     # caption-anchored PDF figure + caption extractor
  build_library.py       # stdlib-only catalog/index builder and local resource checker
  preview_existing.py    # isolated preview of reviewed existing reports (requires bs4)
templates/
  index.html             # navigation index scaffold
  report.html            # per-paper report scaffold
  comparison.html        # comparison-page scaffold
  style.css              # shared light-mode styling
  site.js                # library/reader interactions; no API or CDN calls
  vendor/                # local MathJax + Mermaid, including fonts
examples/
  preview-selection.json # three existing reports and their reviewed tags
  preview-additions/     # attributed method diagram and evidence chart
tests/                   # builder regression + real Chromium acceptance
```

Generated reading libraries live outside the skill checkout and dotfiles. This
repository contains the reusable templates, tools and preview recipe; the user's
reports, figures and catalogs stay in their selected library directory.

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/a1henu/paper-reading-skill.git ~/.claude/skills/paper-reading
```

The figure extractor needs [PyMuPDF](https://pymupdf.readthedocs.io/) (`pip install pymupdf`); without it the skill falls back to `pdftoppm` page renders or redrawn diagrams.

Then ask Claude to "解读 / 整理 this paper" (or pass a PDF / arXiv link / title) and the skill activates.

## Usage

Single paper runs a deep pipeline (scout → specialist fan-out → synthesize → adversarial verify → pedagogy critic); 2–4 papers fan out one agent per paper; ≥5 papers (or "集群 / cluster / 全面 / ultracode") orchestrate via a workflow. Say "快速 / 省 / quick" for a single inline pass.

Respect host tool availability and delegation limits; when tools are unavailable,
perform the same stages sequentially.

## Build and verify a library

After writing `reports/<slug>.html`, figures, and `metadata/<slug>.json` according to
`reference/metadata.md`, run:

```bash
python3 scripts/build_library.py /path/to/topic --title "我的论文库"
python3 scripts/build_library.py /path/to/topic --check
```

The builder writes `index.html`, `library.json`, `catalog.json`, `catalog.csv`, and
copies CSS/JS/local vendor files. It never rewrites report prose or sidecars. Changed
generated files receive timestamped backups; identical builds are no-ops. It rejects
reports missing metadata, invalid tags, unsafe cover paths and broken relative links.
It retains comparison-page links and requires `--replace-index` before backing up
and replacing a legacy custom index. Review old reading routes before migration.

Open the generated index directly; `file://` works without a web server. The catalog
is embedded as escaped JSON so search never depends on a browser fetch. UI exports
contain filtered papers plus local favorites; footer exports contain the full catalog.
Favorites do not sync across browsers. Sidecar tag changes must also be mirrored in
the report's embedded metadata; rerun the builder after updating them.

## Preview and tests

See `examples/README.md` for rebuilding the isolated preview from this installation's
existing reports. No old report site is modified by the preview helper. For an install
without those source reports, use the templates and your own metadata to build a site.

```bash
python3 -m pytest tests/test_library.py -q
PAPER_READING_SITE=/path/to/reading-library python3 -m pytest tests/test_browser.py -q
node --check templates/site.js
```

The browser suite needs Playwright Chromium and a library containing the three
example reports; the library may include any number of additional papers.
`PAPER_READING_SITE` selects its external directory (default: `~/reading-library`).

The browser suite checks search/tag intersection, sorting, favorites, exports,
image/SVG zoom, focus return, TOC, formulas/diagrams, print details, desktop/phone
overflow and no-JS/denied-storage behavior. It saves screenshots under
`tests/artifacts/`. It does not verify scientific claims against the original PDFs.

## License

MIT — see [LICENSE](LICENSE).
