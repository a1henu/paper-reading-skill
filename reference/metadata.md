# Metadata and tags

Each completed report owns `metadata/<slug>.json`. These sidecars are the durable
source of truth; `catalog.json`, `catalog.csv` and `index.html` are derived views.
Metadata is not browser storage. Favorites are browser-local and included in UI exports.

## Required record

```json
{
  "schema_version": 1,
  "slug": "example-paper",
  "title": "Paper title",
  "authors": ["First Author", "Second Author"],
  "year": 2026,
  "venue": "arXiv",
  "summary_zh": "说明具体问题、做法与意义的一句话。",
  "tags": ["multimodal", "image-generation", "llm-agent"],
  "keywords": ["多模态生成", "工具调用", "可编辑画布"],
  "read_at": "2026-10-08",
  "cover": "assets/example-paper/fig2_p3.png",
  "links": {"arxiv": "https://arxiv.org/abs/0000.00000", "code": null}
}
```

The URL/title above are schema examples; replace them with verified values. `title`
must contain the complete official paper title, including its subtitle. Keep a
short project/model name in the slug or keywords; do not substitute it for the title.
Cards, search and exports all use this full title, with natural wrapping in the UI.
`year` and `cover` may be null; venue can be empty if unknown. `authors` is always an array,
not a comma-joined string. `read_at` is the actual date the paper was read, not its
publication date or the date the site was rebuilt. For a legacy report without a
reliable date, use null and add `read_date_note`; it sorts after dated reports.
Stable slug = stable identity;
do not make a new record every time the same paper is reread.

Additional fields (`key_contribution_zh`, `datasets`, `key_metrics`, `relation_hints`,
`visuals`, `source_report`, `tagging_basis`) are preserved by the builder. Use these
for provenance and later archiving; do not put credentials or full request logs here.

## Assign useful tags after reading

1. Read the paper's problem, method and experiments. Choose **3–8 tags** that describe
   its central contribution; a method appearing only in related work is not a tag.
2. Reuse tags in the topic's existing sidecars and `taxonomy.json`. Prefer one domain,
   one task and one method where applicable; an artifact tag such as `dataset` or
   `survey` is appropriate when it describes what the paper contributes.
3. Canonical tags are lowercase English kebab-case. The bundled alias map normalizes
   `t2i` → `image-generation`, `rl` → `reinforcement-learning`, etc. Do not emit both
   an alias and its canonical tag. New precise tags are allowed; the starter taxonomy
   is not a closed vocabulary. Do not add vague tags like `interesting` / `paper`.
4. Add **3–8 keywords**, allowing 中文、English、proper names and abbreviations. These
   preserve the user's likely search wording, e.g. tags `llm-agent`, `editable-design`
   with keywords `智能体`, `HTML/CSS`, `可编辑海报`, `设计回放`.
5. Inspect the final tags against the actual report, save the sidecar and mirror it
   in `<script type="application/json" id="paper-metadata">`. Serialize `<` as
   `\u003c` (use `build_library.script_json`) so paper text cannot close the script.
   Render tags as ordinary links too, for navigation without JS.
6. Rebuild and check the whole topic after each read. The builder deliberately refuses
   to regenerate a directory containing reports without metadata, so older reports
   cannot silently disappear. For a migration, inspect and tag them explicitly;
   label tags based only on existing notes as `tagging_basis: "existing-report"`.

## Portability and maintenance

- `cover` and report resources must be relative files inside the topic. Use null if
  no meaningful figure is available; do not reference a nonexistent placeholder.
- `links` values are verified HTTP(S) URLs or null. Missing resources stay missing.
- Keep dates and tags in JSON; directory names are not the only archive index.
- The browser search checks title, authors, summary, venue, year, tags and keywords.
  Space-separated search terms and multiple tags both use intersection. Sorting is
  explicit date/year/title order, without a relevance scoring algorithm.
- UI exports contain the currently filtered papers; footer downloads contain the
  full built catalog. CSV cells are escaped and formula-like text is neutralized.
- JSON/CSV exports are portable data. This static UI does not write tag edits back
  to disk or synchronize favorites across browsers; edit the sidecar, mirror it in
  the report's embedded metadata, and rebuild. The builder rejects divergent tags
  so report links cannot point at nonexistent filters.
