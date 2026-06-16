# Workflow reference — paper-reading

Detailed guidance to keep report quality high. SKILL.md has the phase overview; this is the depth.

## North star: the report must be self-contained

The reader should grasp the **whole paper by reading the report alone, smoothly, top to bottom** — opening the original PDF *only* when they choose to dig deeper on one point. Optimize for that. A report that forces the reader back to the paper to follow the main line has failed, even if it is "accurate". Concretely:

- **Intuition before math, always.** Before any non-trivial equation or module, put a `.intuition` block (一个类比 / 一个生活化场景 / 一句大白话) explaining *what it's trying to do and why* — no symbols. Then show the math. A reader who skips every equation should still understand the method from the intuition blocks alone.
- **Never leave a symbol undefined.** Put a `.notation` table before the method section listing every symbol (含义 + 维度/shape). In each `eq-card`, still name the symbols inline — don't make the reader scroll.
- **Smooth flow > completeness in-line.** Keep the main reading line short and motivated; push derivations, proofs, hyperparameter tables, and edge cases into `<details class="dig">` "深入（可跳过）" blocks. The main line reads like a story; the details are there when wanted.
- **Connect the sections.** Use `.bridge` transitions ("上一步得到了 X，但还差 Y，于是…") so each section flows into the next instead of reading like disconnected notes.
- **Make it concrete.** Include a `#walkthrough` that runs one tiny concrete input end-to-end through the method, with actual intermediate values — this is often what finally makes an abstract method click.
- **Anticipate questions.** The `#faq` section answers what a reader naturally wonders at that point ("和 XX 有什么区别？" "为什么不用更简单的做法？" "这个假设现实成立吗？"). These are exactly the questions that otherwise send someone back to the paper.
- **Be honest about edges.** The `#limits` section states适用边界、代价、作者承认的不足、开放问题 — readers trust a report that says where the method breaks.

## Reading depth

A good report makes the user understand the paper without reading it. That means:
- **Don't summarize the abstract** — explain the *idea*. Why does it work? What's the key insight?
- **Every equation gets unpacked with the eq-card 三段式**: 是什么 / 逐符号 / 为什么这样设计 / 直觉. If an equation is a loss, say what it pushes up/down and why. Never show a formula without the LaTeX *and* the 中文 unpacking.
- **Motivation must name the gap concretely**: not "previous methods have limitations" but "previous KD methods需要 teacher logits，但闭源模型只给文本输出，所以无法用".
- **Lineage is a story**, not a list: A 提出 X → B 发现 X 在 Y 场景失效 → 本文用 Z 解决 → 启发了 W.
- **A method总览 before details**: open the method with a `#bigpicture` section — 2-3 段大白话 + 一句话 core idea + 一张数据流 flowchart — so the reader has the global map before diving into per-module equations.

## Comprehension aids — when to use each block

The report template ships reusable blocks. Reach for them like this:

| Block | Use it for | Don't |
|---|---|---|
| `.intuition` | before every hard equation/module; the core-idea one-liner | restate the formula in words — give the *why* / analogy |
| `.eq-card` | one per key equation, 三段式 unpacking | dump multiple equations in one card |
| `.notation` | the symbol table before §method | skip symbols that "seem obvious" |
| `<details class="dig">` | proofs, derivations, ablation extras, hyperparams | hide anything needed to follow the main line |
| `.bridge` | between consecutive method steps / sections | over-use; one per real transition |
| `.walkthrough` | one concrete end-to-end example with real values | leave it abstract ("then we compute the loss") |
| `.keynum-row` | the 1-3 numbers the audience must remember | list every metric — pick the headline ones |
| `.faq` | the 2-4 questions a reader hits at that point | invent questions nobody would ask |
| `.glossary` | jargon/缩写 used across the report | duplicate the notation table (symbols vs terms) |

## Figure handling (combine extracted + redrawn)

Extract original figures for: architecture diagrams, qualitative result samples, main quantitative plots that are hard to redraw.
Redraw as Mermaid/SVG for: timelines, lineage graphs, method-comparison schematics, simple bar/line trends from result tables.

PDF figure extraction commands (check availability with `which pdfimages pdftoppm`):
```bash
# extract all embedded raster images
pdfimages -png paper.pdf assets/<slug>/fig
# OR rasterize a specific page (when figure is vector / mixed)
pdftoppm -png -r 150 -f 3 -l 3 paper.pdf assets/<slug>/page3
```
Then crop/select the relevant ones. If neither tool exists, redraw the figure and add a 中文 note: "原图未抽取，以下为重绘示意图".

Always write a 中文 `<figcaption>` that *interprets* the figure, not just labels it.

## Mermaid patterns

Timeline (lineage):
```
timeline
    title 知识蒸馏发展脉络
    2015 : Hinton KD (soft targets)
    2019 : DistilBERT
    2023 : MiniLLM (reverse KLD)
```
Evolution graph (comparison):
```
graph LR
    A[Hinton 2015] -->|序列级| B[Seq-KD]
    B -->|纠正 exposure bias| C[本文]
```
Method flow:
```
flowchart TB
    x[输入] --> enc[Encoder] --> z[表征] --> dec[Decoder] --> y[输出]
```

## Result tables

Reproduce the paper's key table faithfully. Use `class="num"` on numeric cells, `class="best"` on the winning number. Add a 中文 sentence before the table saying what to look at.

## Reproduction guide quality

The guide should let the user actually start. Include:
- Exact `git clone` + env setup (conda/pip, python version, key deps & versions if README pins them).
- Where weights/checkpoints live and how to download.
- Minimal train command AND minimal inference/eval command.
- Real compute needs (GPU count, VRAM, training time) — pull from paper or README.
- Known pitfalls (CUDA/version conflicts, dataset preprocessing gotchas) found in repo issues.
- If no official code exists, say so clearly and link the best reimplementation, marked as unofficial.

## Resource sweep checklist (per paper)

- [ ] arXiv abs + PDF URL
- [ ] Official code repo (GitHub) — note ⭐ and official/unofficial
- [ ] Checkpoints / weights (HF, drive, model zoo)
- [ ] Project / demo page
- [ ] Datasets used (+ links)
- [ ] Venue + year, authors, affiliations
- [ ] (nice) citation count, related blog/video

Populate `disabled` class on metadata-bar links that genuinely don't exist — don't leave dead links.

## Multi-paper handling

- Pick the execution mode by paper count (see SKILL.md table): 1 → inline, 2–4 → fan-out with the `Agent` tool, ≥5 or "集群/cluster/thorough" → agent cluster with the `Workflow` tool. Full patterns and ready-to-run script in `reference/orchestration.md`.
- Orchestrator does Phase 0 + dir skeleton + `style.css` copy *before* fan-out; each subagent owns one paper (Phase 1–3) and returns a structured metadata record; orchestrator builds comparison + index from those records.
- Subagents write disjoint files (`reports/<slug>.html`, `assets/<slug>/`), so no worktree isolation is needed.
- Build a TaskCreate list to track progress: one task per paper, plus comparison + index.
- Decide relatedness from the returned `relation_hints`: same task/domain, citing each other, or sharing a method family → make a comparison page (split into multiple if the batch forms separate clusters). Unrelated one-offs → skip comparison, just index them.
- Reuse the topic-level `assets/style.css`; per-paper figures go in `assets/<slug>/`.

## Self-check before finishing

- index.html links resolve to every report + comparison.
- Every report has the sticky metadata bar at the very top with working links.
- All prose中文; equations shown as LaTeX; figures have中文 captions.
- File/dir names all English kebab-case.
- **Self-contained check** — can a reader follow the whole main line without the PDF? Every hard equation has a preceding `.intuition`; every symbol is in the `.notation` table; there's a `#bigpicture` before details, a `#walkthrough` with real values, a `#faq`, and a `#glossary`. Heavy detail is in `dig` blocks, not the main line.
- Tell the user: output path + "先打开 `<topic>/index.html`".
