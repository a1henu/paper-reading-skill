---
name: paper-reading
description: Read one or more research papers (PDF / arXiv link / title) and produce in-depth Chinese explainer reports as standalone HTML files — covering intro, motivation, related-work lineage, equation-by-equation method walkthrough, experiments and visualized results, plus a reproduction guide and a full sweep of code repos / checkpoints / datasets. Generates a separate index page, per-paper report pages, and (for ≥2 related papers) a comparison page. Use when the user asks to read/解读/整理 a paper or papers.
---

# Paper Reading

Turn papers into图文并茂 Chinese explainer websites + reproduction guides.

## Output language & naming (hard rules)

- **All file and directory names: English**, kebab-case (e.g. `attention-is-all-you-need`).
- **All report prose: 中文**. Keep technical terms / proper nouns in English where natural (e.g. "我们用 **cross-attention** 把 encoder 输出注入 decoder").
- Equations rendered with MathJax; never paraphrase a formula into prose-only — always show the LaTeX too.

## North star — a self-contained report

The report must let the reader **grasp the whole paper by reading it alone, smoothly, top to bottom** — opening the PDF only when they *choose* to dig deeper on one point. Every design choice below serves that goal: intuition before math, every symbol defined, a concrete walked example, smooth transitions, anticipated questions, and heavy detail tucked into collapsible blocks so the main line stays readable. See `reference/workflow.md` §"North star" for the full principles and the comprehension-aid block guide.

## Configured defaults (this install)

- **Charts**: combine extracted original figures with redrawn code charts. Extract key original figures from the PDF where feasible; redraw lineage/timeline/comparison/perf curves as Mermaid / inline SVG.
- **Resource search**: search broadly (GitHub, HuggingFace, project page, datasets, blogs) and aggregate links into the metadata bar + reproduction guide. **Never clone, run, or execute code** — the reproduction guide is *organized reference* (commands quoted from the README/docs), not something you test by running. The only local commands allowed are the bundled figure extractor (`scripts/extract_figures.py`) and, as a fallback, `pdftoppm` for whole-page renders.
- **Output layout**: per-topic folder `./<topic>/` in the current working directory.

## Output structure

```
./<topic>/                          # topic = short english slug, ask user if ambiguous
├── index.html                      # navigation index — links every report + comparison
├── assets/
│   ├── style.css                   # shared styling (copied from skill templates)
│   └── <paper-slug>/               # extracted figures per paper
├── reports/
│   └── <paper-slug>.html           # one self-contained report per paper
└── comparisons/
    └── <comparison-slug>.html      # only when ≥2 related papers
```

**Always separate report from index** — `index.html` is pure navigation; reports live under `reports/`. The index is regenerated/updated each run so it lists everything in the topic folder.

## Execution mode — pick by paper count & intent

The work parallelizes across papers AND, for a single paper, across **specialist lenses**. Multi-agent collaboration on one paper raises both accuracy (a dedicated verifier) and digestibility (a dedicated pedagogy critic) — so it is the default for single papers too, unless the user asks for "快速 / 省 / quick".

| Situation | Mode | Mechanism |
|---|---|---|
| 1 paper, user wants quick/省 | **Inline** | Do all phases yourself, single pass. |
| 1 paper (default) | **Single-paper deep pipeline** | Scout → specialist fan-out (`Agent` tool) → synthesize → adversarial verify → pedagogy critic. See `reference/orchestration.md` §Mode C. |
| 2–4 papers | **Fan-out** | One subagent **per paper** via the `Agent` tool, all launched in a single message so they run concurrently. |
| ≥5 papers, OR user asks for "集群 / cluster / 加速 / thorough / 全面 / ultracode" | **Agent cluster** | Orchestrate with the `Workflow` tool — pipeline each paper through sweep→read→report, optionally add an adversarial fact-check stage, then synthesize. |

Invoking this skill **is** the user's opt-in to multi-agent orchestration — the user explicitly requested that runs use multiple agents / an agent cluster. So launch subagents (and the `Workflow` tool when in Cluster mode) without asking again.

### Single-paper deep pipeline (default for 1 paper)

The goal: help the reader understand the gist fast, correctly, and get hands-on quickly. Decompose by **specialist lens**, not by PDF chunk, so each facet goes deep — but anchor everyone to one thesis to keep the report coherent.

1. **Scout / framing** (you or one agent): quick read of abstract + intro + figures + conclusion. Produce a **shared brief**: one-sentence thesis, the gap it fills, section map, list of key equations & figures, the single most important figure, candidate repo/checkpoint/dataset links to chase. Every specialist receives this brief so sections converge on the same thesis.
2. **Specialist fan-out** (parallel `Agent` calls in one message, each gets the brief + paper):
   - `motivation` — intro & the gap; write a生活化类比 `.intuition` so a newcomer feels the pain point.
   - `bigpicture` — the method总览: 2-3 段大白话 + 一句话 core idea + a data-flow flowchart, before any equation.
   - `lineage` — related-work development logic via web research + Mermaid timeline (told as a story).
   - `method` — the careful one: a `.notation` symbol table, then per-module `intuition → eq-card (是什么/逐符号/为什么/直觉) → optional dig block → bridge`. Equation-by-equation.
   - `walkthrough` — run one tiny concrete input end-to-end through the method with real intermediate values.
   - `experiments` — result tables + redrawn charts + a `.keynum-row` of the 1-3 headline numbers; say what to look at.
   - `resources+repro` — sweep GitHub/HF/datasets, read repo README + issues, **organize** the setup/train/inference commands as a copy-pasteable Quick Start (quote them from the README, do **not** run or clone).
   - `figures` — extract key figures with the bundled `scripts/extract_figures.py` (caption-anchored, gets exact figure boundaries — NOT pdfimages/pdftoppm), **view every extracted PNG**, then select + write 中文 captions that *interpret* the figure.
   - `faq+limits+glossary` — the 2-4 questions a reader naturally hits, an honest局限与讨论, and a术语表.

   Each returns its section's HTML fragment (or structured content) — not a whole file.
3. **Synthesis** (you): assemble fragments into `reports/<paper-slug>.html` from the template. Write the TL;DR, the **「5 分钟速读」** box, the **核心一张图**, per-section **要点**, and the **`.bridge` transitions** that connect sections into one smooth read; remove duplication.
4. **Adversarial verify** (parallel skeptics, distinct lenses): math-lens (equations & symbol explanations correct vs paper) · numbers-lens (every result number matches the paper's tables; no invented SOTA) · links-lens (every metadata/repro link resolves to the right artifact). Apply fixes inline.
5. **Pedagogy / usability critic** (one agent): read the final HTML as a newcomer — **can you follow the whole main line without opening the PDF?** Flag any equation lacking a preceding `.intuition`, any undefined symbol, missing「为什么」, weak walkthrough, or a place where you'd be forced back to the paper. Also check the Quick Start is **complete and copy-pasteable** (reads right against the README — not run/executed). Apply its suggestions (or loop the relevant specialist once).

**Orchestrator responsibilities** (you, the main agent — always, never delegated):
- Phase 0 (scope, slugs, topic name) — must finish *before* any fan-out so every subagent knows its `<paper-slug>` and the shared `<topic>` dir.
- Create the directory skeleton and copy `templates/style.css` → `<topic>/assets/style.css` **once, up front**, so subagents only write their own files (no races).
- Synthesis, applying verify-fixes and pedagogy-fixes (single-paper mode).
- After all per-paper subagents return (multi-paper modes): build the **comparison page** (Phase 4) and **index** (Phase 5) from their returned metadata — synthesis needs the global view, so it is never delegated to a per-paper agent.

**Per-paper subagent contract** (Fan-out & Cluster modes) — give each subagent:
- Its paper source, assigned `<paper-slug>`, the absolute `<topic>` dir, and paths to `templates/report.html` + `templates/style.css`.
- The hard rules (中文 prose, English filenames, sticky metadata bar, MathJax equations, combine extracted+redrawn figures) **and the self-contained principle**: intuition before math, a notation table, a concrete walkthrough, smooth bridges, FAQ + limits + glossary, heavy detail in `dig` blocks. (See `reference/workflow.md` block guide.)
- Instruction to do Phase 1–3 for *its* paper only: write `reports/<paper-slug>.html` and figures under `assets/<paper-slug>/`.
- Instruction to **return a structured metadata record** (not prose) so you can build the comparison + index without re-reading the papers. Required fields: `slug, title, authors, venue_year, one_line_summary_zh, domain_tags, key_contribution_zh, datasets, key_metrics, links{arxiv,code,checkpoints,project,dataset}, relation_hints` (how it relates to the other papers in the batch).

Subagents write disjoint files (`reports/<slug>.html`, `assets/<slug>/…`), so no worktree isolation is needed. See `reference/orchestration.md` for the ready-to-run `Workflow` script and `Agent`-tool fan-out pattern.

## Workflow

Use TaskCreate to track progress when handling multiple papers. Run the phases below.

### Phase 0 — Intake & scope
1. Identify each paper source: local PDF path, arXiv ID/URL, or title.
   - For local PDFs: use the `Read` tool with `pages` to read the PDF directly (max 20 pages/request; page through long papers).
   - For arXiv/URL/title: `WebSearch` / `WebFetch` to locate the paper, abstract, and PDF.
2. Decide the `<topic>` slug. If multiple papers and the topic is unclear, ask the user once for a short english topic name.
3. Assign each paper a kebab-case `<paper-slug>` (usually first-author-year-keyword or the common short name, e.g. `vaswani-2017-transformer`).

### Phase 1 — Resource sweep (per paper)
Search broadly and collect into a metadata record. Use `WebSearch` + `WebFetch`:
- Official **code repo** (GitHub/GitLab) — prefer authors' repo; note stars & official-vs-reimplementation.
- **Checkpoints / weights** (HuggingFace, model zoo, Google Drive links in README).
- **Project page** / blog / video.
- **Datasets** used.
- **arXiv / DOI / conference** (venue + year), authors, affiliations.
- Citation count if easily found.
Record every URL — these populate the metadata bar (requirement #4) and the reproduction guide.

### Phase 2 — Deep read (per paper)
Read the full paper. Extract and understand:
- **Intro & Motivation**: 要解决什么问题、为什么重要、现有方法的不足 (the gap).
- **Related work lineage**: 这篇文章在领域中的位置；前序工作 → 本文 → 后续影响的发展逻辑。Research the lineage via web search if the paper's own related-work section is thin. Render as a **timeline / lineage diagram** (Mermaid).
- **Method**: walk through the architecture and **every key equation**. For each formula: show the LaTeX, then 中文 explain每个符号的含义、为什么这样设计、直觉是什么。
- **Experiments**: setup (datasets, baselines, metrics, compute), key result tables, ablations. Reproduce the **key result tables** as HTML tables and **redraw key trends** as charts.
- **Figures**: extract the paper's key figures (architecture diagram, main results) into `assets/<paper-slug>/` and embed; redraw conceptual/lineage/comparison figures as code charts.

To extract figures from a PDF, **use the bundled caption-anchored extractor** — it locates each "Figure N" caption and crops the exact figure region (clustering the graphics above the caption within its column), which gets the boundaries right where `pdfimages` (fragments) and `pdftoppm` (whole-page, caption bleed) get them wrong:

```bash
python3 ~/.claude/skills/paper-reading/scripts/extract_figures.py "paper.pdf" assets/<slug> --dpi 200
```

It writes `fig<N>_p<page>.png` + a `fig<N>_p<page>.txt` caption sidecar for each figure, plus a `manifest.json` (with the **full untruncated caption** per figure). Then **view every extracted PNG** (Read tool) to confirm the crop is complete and clean, select the ones the report needs, write a 中文 figcaption interpreting each, and embed the figure's original caption right after it inside a collapsed `<details class="orig-cap">📄 原文 caption</details>` (the manifest's `caption` / `.txt` sidecar gives the text; styled in `style.css`). For figures marked `no-gfx`/`too-small`, re-run with `--full-pages`, view the page, and crop by hand. See `reference/workflow.md` §"Figure handling" for the full procedure. If PyMuPDF is missing, fall back to `pdftoppm -png -r 200 -f <pg> -l <pg>` and crop manually, or redraw and note "原图未精确抽取".

### Phase 3 — Generate per-paper report
Use `templates/report.html` as the structure. One self-contained HTML file per paper at `reports/<paper-slug>.html`. The guiding test: **a reader should follow the whole main line without opening the PDF**. Must contain, top to bottom:
1. **Metadata bar** (sticky, at the very top) — title, authors, affiliation, venue/year, and clickable buttons for: arXiv/PDF, code repo, checkpoints, project page, dataset. (Requirement #4.)
2. **5 分钟速读** — 一句话 / 痛点 / 做法 / 效果 / 价值 + a `.keynum-row` of headline numbers + 核心一张图.
3. **TL;DR** — 3-5 句中文速览。
4. **问题与动机** — with a生活化 `.intuition` analogy and a concretely-named gap.
5. **相关工作与发展脉络** — told as a story, with a Mermaid timeline.
6. **方法总览** (`#bigpicture`) — 2-3 段大白话 + 一句话 core idea + data-flow flowchart, BEFORE equations.
7. **符号表** (`.notation`) — every symbol with 含义 + shape, so the reader never gets lost.
8. **方法详解** — per module: `intuition → eq-card (是什么/逐符号/为什么这样设计/直觉) → optional <details class="dig"> → .bridge`.
9. **走一遍例子** (`#walkthrough`) — one tiny concrete input run end-to-end with real intermediate values.
10. **实验** — say what to look at first, then tables + redrawn charts; ablations can go in a `dig` block.
11. **效果可视化** — visualize the paper's results/effect, captions that point out what's good.
12. **局限与讨论** — 适用边界 / 代价 / 作者承认的不足 / 开放问题.
13. **常见疑问 (FAQ)** — the 2-4 questions a reader naturally hits.
14. **复现指南 (Reproduction guide)** — Quick Start + environment & deps, repo structure, data prep, train/inference commands, compute/VRAM需求, known pitfalls, aggregated resource links. (Requirement #3.)
15. **术语表 (Glossary)** — jargon/缩写 used in the report.

Keep the **main line smooth**: intuition before math, heavy detail folded into `dig` blocks, `.bridge` sentences between sections. See `reference/workflow.md` for the comprehension-aid block guide.

### Phase 4 — Comparison page (only if ≥2 related papers)
If two or more papers share a domain or logical relationship, generate `comparisons/<comparison-slug>.html` from `templates/comparison.html`:
- 讲解它们之间的关系：演进 / 互补 / 竞争。
- A **lineage/evolution diagram** showing how they connect.
- A **side-by-side comparison table**: 方法、核心贡献、数据集、关键指标、算力。
- 中文 narrative on the development logic与取舍。

### Phase 5 — Index
Generate/update `index.html` from `templates/index.html`:
- Card grid linking each paper report and any comparison page.
- Each card shows title, one-line中文 summary, venue/year, and quick links.
- Keep it pure navigation — separate from reports (requirement #6).

### Phase 6 — Finish
- Copy `templates/style.css` to `<topic>/assets/style.css` (all HTML links to `../assets/style.css` or `assets/style.css`).
- Tell the user the output path and which file to open first (the index).
- All HTML must be self-contained enough to open via `file://` (use CDN for MathJax/Mermaid, relative path for style.css).

## HTML rules

- **Light mode only.** All pages use the light palette in `style.css`; never introduce dark backgrounds. Initialize Mermaid with `theme: 'neutral'` (light) — not `'dark'`.
- Load MathJax (`https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js`) and Mermaid (`https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`) from CDN.
- Use the shared `style.css`. Keep reports readable: max-width content column, clear section headers, and the `.toc-float` sidebar (auto-hidden on narrow screens) for navigation.
- Embed extracted figures with `<figure><img><figcaption>` and a 中文 caption explaining the figure.
- See `reference/workflow.md` for detailed per-section guidance, `reference/orchestration.md` for multi-agent fan-out / cluster patterns, and `templates/` for the HTML scaffolds.
