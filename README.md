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

It also generates a navigation **index page**, and — for ≥2 related papers — a **comparison page** with a lineage diagram and side-by-side table.

Reports are 中文 prose with English file/dir names; charts combine figures extracted from the PDF with redrawn Mermaid / SVG diagrams. Original figures are pulled with a bundled **caption-anchored extractor** (`scripts/extract_figures.py`) that crops each figure at its true boundary and saves its full original caption alongside — far cleaner than `pdfimages` (fragments) or whole-page `pdftoppm` (caption bleed). The skill never clones or runs code — the reproduction guide is *organized reference*, with commands quoted from the README/docs.

## Layout

```
SKILL.md                 # skill definition + workflow
reference/
  workflow.md            # detailed per-section guidance
  orchestration.md       # multi-agent fan-out / cluster patterns
scripts/
  extract_figures.py     # caption-anchored PDF figure + caption extractor
templates/
  index.html             # navigation index scaffold
  report.html            # per-paper report scaffold
  comparison.html        # comparison-page scaffold
  style.css              # shared light-mode styling
```

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/a1henu/paper-reading-skill.git ~/.claude/skills/paper-reading
```

The figure extractor needs [PyMuPDF](https://pymupdf.readthedocs.io/) (`pip install pymupdf`); without it the skill falls back to `pdftoppm` page renders or redrawn diagrams.

Then ask Claude to "解读 / 整理 this paper" (or pass a PDF / arXiv link / title) and the skill activates.

## Usage

Single paper runs a deep pipeline (scout → specialist fan-out → synthesize → adversarial verify → pedagogy critic); 2–4 papers fan out one agent per paper; ≥5 papers (or "集群 / cluster / 全面 / ultracode") orchestrate via a workflow. Say "快速 / 省 / quick" for a single inline pass.

## License

MIT — see [LICENSE](LICENSE).
