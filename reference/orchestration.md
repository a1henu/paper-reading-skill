# Orchestration reference — multi-agent paper-reading

How to parallelize multi-paper runs. SKILL.md picks the mode; this file gives the concrete patterns.

The unit of parallelism is **one paper = one agent** doing Phase 1–3 (resource sweep → deep read → write report + extract figures). Synthesis (comparison + index) is always done by the orchestrator after fan-out, because it needs the global view.

---

## Setup the orchestrator does BEFORE any fan-out

```bash
mkdir -p <topic>/assets <topic>/reports <topic>/comparisons
cp ~/.claude/skills/paper-reading/templates/style.css <topic>/assets/style.css
```
Then decide slugs for every paper. Subagents only ever write `reports/<slug>.html` and `assets/<slug>/…`, so their writes never collide — no worktree isolation needed.

---

## Mode A — Fan-out (2–4 papers) via the Agent tool

Launch all per-paper agents **in a single message** (multiple `Agent` tool calls in one response) so they run concurrently. Use `subagent_type: "general-purpose"` (it has web + file + bash tools for sweep, extraction, and writing).

Prompt skeleton for each agent:

```
You are writing ONE paper's explainer report for a paper-reading batch.

Paper source: <pdf path | arxiv url | title>
Assigned slug: <paper-slug>
Topic dir (absolute): <abs>/<topic>
Templates: ~/.claude/skills/paper-reading/templates/report.html (structure),
           style.css is already copied to <topic>/assets/style.css — link it as ../assets/style.css
Reference: ~/.claude/skills/paper-reading/reference/workflow.md (read this for depth/quality bar)

Do Phase 1–3 for THIS paper only:
1. Resource sweep: official code repo (note ⭐ + official/unofficial), checkpoints/weights,
   project page, datasets, venue/year, authors, affiliations. Record every URL.
2. Deep read the full paper (Read tool with pages= for PDFs; WebFetch for arxiv).
3. Write <topic>/reports/<paper-slug>.html from the report template. Extract key figures
   with `pdfimages`/`pdftoppm` into <topic>/assets/<paper-slug>/; redraw lineage/comparison
   as Mermaid. Sticky metadata bar at top with all links. Prose 中文, equations in MathJax LaTeX,
   filenames English.

HARD RULES: report prose 中文 (terms English OK); every key equation shown as LaTeX then
explained symbol-by-symbol; figures get 中文 <figcaption>; mark dead metadata links class="disabled".

RETURN (this is your final output — raw JSON, not prose), so the orchestrator can build the
comparison + index without re-reading:
{slug, title, authors, venue_year, one_line_summary_zh, domain_tags:[...],
 key_contribution_zh, datasets:[...], key_metrics:{...},
 links:{arxiv,code,checkpoints,project,dataset},
 relation_hints:"how this relates to the other papers in the batch"}
```

After all agents return: you (orchestrator) build the comparison page (if related) and the index from the returned JSON records.

---

## Mode B — Agent cluster (≥5 papers, or "集群/cluster/thorough/全面/ultracode") via the Workflow tool

Pipeline each paper through stages so a fast paper isn't blocked by a slow one. Optionally add an adversarial fact-check stage to raise accuracy. Invoking this skill is the opt-in, so calling `Workflow` here is authorized.

```js
export const meta = {
  name: 'paper-reading-cluster',
  description: 'Read N papers in parallel: sweep+read+report per paper, fact-check, return metadata',
  phases: [
    { title: 'Report', detail: 'per-paper sweep + deep read + write HTML report' },
    { title: 'Verify', detail: 'adversarially fact-check each report against the paper' },
  ],
}

// args = { topic, templatesDir, papers: [{slug, source}, ...] }
const { topic, templatesDir, papers } = args

const META_SCHEMA = {
  type: 'object',
  required: ['slug','title','venue_year','one_line_summary_zh','links'],
  properties: {
    slug: {type:'string'}, title: {type:'string'}, authors: {type:'string'},
    venue_year: {type:'string'}, one_line_summary_zh: {type:'string'},
    domain_tags: {type:'array', items:{type:'string'}},
    key_contribution_zh: {type:'string'},
    datasets: {type:'array', items:{type:'string'}},
    key_metrics: {type:'object'},
    links: {type:'object'},
    relation_hints: {type:'string'},
  },
}

const records = await pipeline(
  papers,
  // Stage 1: one agent fully owns one paper's report
  (p) => agent(
    `Write the paper-reading report for "${p.source}" (slug ${p.slug}) into ${topic}/reports/${p.slug}.html.
     Templates at ${templatesDir}. style.css already at ${topic}/assets/style.css (link ../assets/style.css).
     Do resource sweep + deep read + figure extraction (pdfimages/pdftoppm into ${topic}/assets/${p.slug}/).
     Rules: 中文 prose, English filenames, sticky metadata bar with all links, equations as MathJax LaTeX,
     figures with 中文 captions. Read ~/.claude/skills/paper-reading/reference/workflow.md for the quality bar.
     Return the structured metadata record.`,
    { label: `report:${p.slug}`, phase: 'Report', schema: META_SCHEMA }
  ),
  // Stage 2: adversarial fact-check — fixes inline, returns the (possibly corrected) record
  (rec, p) => rec && agent(
    `Adversarially verify ${topic}/reports/${p.slug}.html against the source paper "${p.source}".
     Check: equations transcribed correctly, result numbers match the paper's tables, no hallucinated
     claims/links, metadata links resolve. FIX any errors directly in the HTML file.
     Return the corrected metadata record (same schema).`,
    { label: `verify:${p.slug}`, phase: 'Verify', schema: META_SCHEMA }
  ),
)

return { records: records.filter(Boolean) }
```

For very large or low-importance batches, drop Stage 2 to save tokens. For a "be exhaustive" request, add a third stage: a completeness critic per paper ("what did the report miss — an ablation, a limitation, a key baseline?") and loop the report agent on its findings.

After the workflow returns, the orchestrator reads `records` and builds the comparison + index — same as Mode A.

---

## Mode C — Single-paper deep pipeline (default for 1 paper)

For ONE paper, parallelize across **specialist lenses** instead of across papers. This raises accuracy (a dedicated verifier) and digestibility (a dedicated pedagogy critic) — the two things a single inline pass does worst. Decompose by lens, not by PDF chunk, and anchor everyone to one shared brief so the report stays coherent.

**Step 1 — Scout (you or one agent).** Quick read of abstract + intro + figures + conclusion. Produce a shared brief: one-sentence thesis, the gap, section map, key equations & figures, the single most important figure, candidate links. This brief is pasted into every specialist's prompt.

**Step 2 — Specialist fan-out.** Launch these in ONE message (`Agent` tool, `general-purpose`), each receiving the brief + paper source. Each returns its section as an HTML fragment + any extracted figure paths — NOT a whole file:

| lens | owns | tools-heavy on |
|---|---|---|
| `motivation` | Intro & the gap, the 5-min speed-read bullets | reading |
| `lineage` | related-work development logic + Mermaid timeline | web search |
| `method` | equation-by-equation walkthrough (the careful one) | reading + MathJax |
| `experiments` | result tables + redrawn charts | reading + tables |
| `resources+repro` | sweep GitHub/HF/datasets, read README+issues, organize setup/train/inference commands into a copy-pasteable Quick Start (quote from README — never run/clone) | web |
| `figures` | extract key figures (pdfimages/pdftoppm) + 中文 captions | bash |

**Step 3 — Synthesis (you).** Assemble fragments into `reports/<slug>.html` from the template. Write TL;DR + 「5 分钟速读」 + 核心一张图 + per-section 要点. Smooth transitions, kill duplication.

**Step 4 — Adversarial verify.** Launch 3 skeptics in parallel, distinct lenses, each fixes inline:
- math-lens: every equation & symbol explanation correct vs the paper.
- numbers-lens: every result number matches the paper's tables; no invented SOTA.
- links-lens: every metadata/repro link resolves to the right artifact.

**Step 5 — Pedagogy / usability critic (one agent).** Read the final HTML as a newcomer: flag comprehension gaps, weak intuitions, missing "why"; check the Quick Start is complete and copy-pasteable (reads right against the README — not run/executed). Apply fixes, or loop the relevant specialist once.

Runnable `Workflow` version (Steps 2→4→5; you do Scout + Synthesis around it, or fold Scout into a Step-0 agent):

```js
export const meta = {
  name: 'single-paper-deep',
  description: 'One paper, many specialist agents: scout → lenses → verify → pedagogy critic',
  phases: [
    { title: 'Lenses', detail: 'specialist agents each own one section' },
    { title: 'Verify', detail: '3 adversarial skeptics, distinct lenses' },
    { title: 'Pedagogy', detail: 'newcomer-perspective critic' },
  ],
}

// args = { source, slug, topic, brief }  (brief = the scout's shared framing)
const { source, slug, topic, brief } = args
const FRAG = { type:'object', required:['section','html'],
  properties:{ section:{type:'string'}, html:{type:'string'}, figures:{type:'array',items:{type:'string'}} } }

const LENSES = [
  ['motivation',  'Intro & motivation + the 5-min speed-read bullets'],
  ['lineage',     'related-work development logic; emit a Mermaid timeline'],
  ['method',      'equation-by-equation walkthrough; LaTeX then symbol-by-symbol 中文'],
  ['experiments', 'key result tables as HTML + redrawn trend charts'],
  ['repro',       'sweep GitHub/HF/datasets, read README+issues, organize setup/train/inference commands into a copy-pasteable Quick Start + resource links (quote from README, never run/clone)'],
  ['figures',     'extract key figures via pdfimages/pdftoppm into '+topic+'/assets/'+slug+'/, 中文 captions'],
]

// Step 2: lenses in parallel (barrier — synthesis needs all fragments)
const frags = await parallel(LENSES.map(([key, job]) => () => agent(
  `Paper: ${source}. Shared brief:\n${brief}\n\nYou own the "${key}" lens: ${job}.
   Return ONLY this section as an HTML fragment (中文 prose, terms English OK, MathJax for equations,
   figures with 中文 <figcaption>). Do not write the whole file.`,
  { label: `lens:${key}`, phase: 'Lenses', schema: FRAG })))

// ... you (orchestrator) synthesize frags into reports/<slug>.html here ...
// then Step 4: verify
const VLENS = ['math (equations & symbols vs paper)','numbers (results match paper tables, no invented SOTA)','links (every link resolves to the right artifact)']
await parallel(VLENS.map(v => () => agent(
  `Adversarially verify ${topic}/reports/${slug}.html against "${source}", lens: ${v}. FIX errors inline in the file.`,
  { label: `verify`, phase: 'Verify' })))

// Step 5: pedagogy critic
await agent(
  `Read ${topic}/reports/${slug}.html as a newcomer. Flag comprehension gaps, weak intuitions, missing "why";
   check the Quick Start is complete and copy-pasteable against the README (do NOT run anything). FIX the HTML directly to improve clarity and skimmability.`,
  { label: 'pedagogy', phase: 'Pedagogy' })

return { frags: frags.filter(Boolean) }
```

Note: `parallel()` for lenses is a deliberate barrier — synthesis genuinely needs all fragments before assembling. The fragment agents return HTML the orchestrator stitches; figure files are written to disk directly by the `figures`/`experiments` lenses.

---

## Scaling knobs

- **Concurrency** is capped at ~`min(16, cores-2)` per workflow; passing 30 papers is fine, they queue.
- **Relatedness for comparison**: build a comparison page only when papers share a domain / cite each other / share a method family. Unrelated batch → skip comparison, just index. Use the `relation_hints` field to decide, and group into multiple comparison pages if the batch splits into clusters.
- **Don't delegate synthesis**: comparison + index always done by the orchestrator from returned metadata, never by a per-paper agent.
- **Token budget**: if a `budget` directive is set, scale stages — drop Verify first, then trim figure extraction depth.
