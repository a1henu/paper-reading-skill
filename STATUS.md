# Paper-reading refresh — 2026-10-08

Current library: `/mnt/user-ssd/baichenxu/reading-library/index.html`.
Latest state: the user subsequently authorized the full historical archive;
98 unique papers and the legacy topic/navigation pages are now in that library.
The earlier sections retain their original validation commands; paths under
`examples/reading-library` were moved outside this repository in the final step.

## Delivered in this iteration

- Updated the report/index/comparison templates and the reading workflow.
- Reports lead with the core figure and use source-labeled original images,
  explanatory diagrams and charts. Shared reader controls support image/SVG zoom,
  font size, focus mode, desktop/mobile contents, code copy and print.
- Every reading now persists 3–8 canonical tags and 3–8 keywords in per-paper JSON.
  A stdlib builder creates the searchable index and JSON/CSV catalogs, preserves
  earlier entries, and checks report metadata consistency and relative resources.
- Isolated preview: `examples/reading-library/index.html` with Editable Visual
  Design, VisionCreator and Paper2Poster; 24 existing original images, two newly
  attributed SVG illustrations, seven distinct archive tags. Paper2Poster already
  contained one inline chart, which is also retained.
- Original report sites were not modified. Existing skill files and the first
  intermediate preview have timestamped backups. No commit/push was made.

## Validation actually run

From this skill's root:

```bash
python3 scripts/build_library.py --help
python3 scripts/preview_existing.py --help
python3 -m py_compile scripts/build_library.py scripts/preview_existing.py
node --check templates/site.js
python3 scripts/build_library.py examples/reading-library
python3 scripts/build_library.py examples/reading-library --check
python3 -m pytest tests/test_library.py tests/test_browser.py -q
git diff --check
```

- 19 tests passed (61.32 seconds). Builder check passed for 3 papers / 4 pages.
- Chromium covered file URLs, search + multi-tag intersection, unknown read dates,
  metadata consistency, safe exports, sorting, persistent favorites, grid/list,
  image/SVG zoom and focus return, TOC, MathJax, Mermaid, print details, no-JS,
  denied localStorage and 390/768/1520-pixel reader viewports.
- Actual configured view URL returned HTTP 200 with bytes identical to the local
  index. HTTP-browser smoke verified index search (3 → 1 → 3), MathJax, Mermaid,
  all 10 VisionCreator original images, and no browser/HTTP resource errors.
- Screenshots in `tests/artifacts/`: desktop/mobile library and report, HTTP index,
  method diagram and evidence chart. Screenshot files are local validation output.

## Scope and next step

This is a frontend/workflow preview using existing notes; scientific conclusions,
numbers and repository availability were not reverified against all original PDFs.
Tags were assigned from the existing reports. Unknown legacy read dates are null,
never inferred from file timestamps or site creation dates.

The user requested a sample first and full refresh later. After preview review,
inventory all requested legacy sites, preserve custom reading routes/comparisons,
prepare metadata for every report, then migrate with backups. Do not use a generic
index replacement until its custom navigation has been accounted for.

## Follow-up: wider, larger reading layout — 2026-10-08

- Increased the default report text from 17px to 20px and the maximum reading
  column from 860px to 1180px. Captions, tables, section headings and contents links
  are larger. Font controls support 16–26px and preserve explicit saved preferences.
- Reserved a separate desktop contents column; focus mode keeps the wide reading
  area centered. Increased the library width to 1680px with two large cards per row,
  larger covers, 24px desktop card titles and 17px summaries. Image dialogs allow
  up to 1600px width.
- Fixed mobile overflow from long inline code/repository links and inline formulas:
  text wraps, while long formulas scroll inside the text column without shrinking.
- Updated the shared templates, reader experience contract and isolated preview.
  Existing report sites remain unchanged; full migration is still outside this step.

Validation actually run from the skill root after the follow-up:

```bash
python3 scripts/build_library.py examples/reading-library
python3 scripts/build_library.py examples/reading-library --check
node --check templates/site.js
python3 -m pytest tests/test_browser.py -q
git diff --check
```

- Browser acceptance: 3 passed in 14.34 seconds. Builder check: 3 papers / 4 pages.
- Additional Playwright geometry checks: all three reports at 390/768/1440px,
  with 20px and 26px text and all details expanded; all 18 combinations fit the
  viewport. Separate desktop checks covered 1280/1340/1341/1520/1920px and verified
  the contents column does not overlap the report.
- Inspected desktop report, body, library and mobile body screenshots in
  `tests/artifacts/wider-*.png`. No new server was started.
- The configured view URLs for the index, sample report and stylesheet returned
  HTTP 200 with bytes identical to the local files.

## Follow-up: compact index and full titles — 2026-10-08

- The user's index preference supersedes the two-large-card layout above: three
  columns above 1200px, two at intermediate widths and one at 620px or below.
  Covers are 160px tall; card titles are 20px with natural wrapping, summaries 15px,
  and padding/footer spacing is reduced. List-view thumbnails are also smaller.
- Restored the complete VisionCreator and Paper2Poster titles from the source
  report headings; VisionCreator was also checked against its local PDF title page.
  Editable Visual Design already had its complete title, confirmed in its PDF.
  Updated the preview selection, sidecars and embedded metadata, then rebuilt the
  index and JSON/CSV catalogs. Future metadata must preserve the complete title.
- Report typography and image sizes retain the wider reading layout. Only the
  isolated preview and shared skill files were updated; originals were preserved.

Validation from the skill root:

```bash
python3 scripts/build_library.py examples/reading-library
python3 scripts/build_library.py examples/reading-library --check
python3 -m pytest tests/test_browser.py -q
git diff --check
```

- Builder: 3 papers / 4 pages passed. Browser suite: 3 passed in 13.15 seconds.
- Additional Chromium checks at 320/390/620/768/1024/1280/1440/1920px: full card
  titles visible without clipping and no horizontal page overflow. Title search
  also matched words from the restored subtitle. Catalog/sidecar/embedded titles
  matched each report's full heading.
- Inspected `tests/artifacts/compact-library-1440.png` and
  `tests/artifacts/compact-library-390.png`. At 1440px, cards measure 363 × 538px.

## External library and Git delivery — 2026-10-08

- Moved the entire generated site from `examples/reading-library` to
  `/mnt/user-ssd/baichenxu/reading-library`. All 82 files, including image assets,
  local vendor dependencies and backups, retained identical SHA-256 checksums.
  The old directory is absent; no copy or symlink remains under dotfiles.
- Updated the skill's output rule, README and preview instructions to keep generated
  libraries outside the skill checkout. Browser tests accept `PAPER_READING_SITE`
  (default `~/reading-library`) so they can validate an external preview.
- Git ignores generated libraries, backups and screenshots. Delivery includes
  reusable skill instructions, templates, builders, tag taxonomy, preview recipe
  and tests. Remote: `origin` → `git@github.com:a1henu/paper-reading-skill.git`,
  branch `main`; fetched remote matched the pre-change local commit `384a09c`.

Validation actually run from the skill root:

```bash
python3 scripts/build_library.py /mnt/user-ssd/baichenxu/reading-library
python3 scripts/build_library.py /mnt/user-ssd/baichenxu/reading-library --check
python3 -m py_compile scripts/build_library.py scripts/preview_existing.py tests/test_browser.py
node --check templates/site.js
PAPER_READING_SITE=/mnt/user-ssd/baichenxu/reading-library python3 -m pytest tests/test_library.py tests/test_browser.py -q
git diff --check
```

- 19 tests passed in 14.41 seconds; builder validated 3 papers / 4 pages.
- The new configured view URL returned HTTP 200 with identical index/CSS bytes.
  A real HTTP-browser check passed search, report navigation, MathJax, Mermaid and
  all 10 VisionCreator original images, with no page or resource errors.
- Active index: [open in browser](http://s-20260601154539-r653m-j57r1.bcecn-bj-cloudml.xiaomi.srv/view/mnt/user-ssd/baichenxu/reading-library/index.html).
- Full migration of legacy reading sites remains outside this sample iteration.

## Historical archive compatibility — 2026-10-08

The subsequent user request authorized inventorying and importing all historical
reports. The external library now holds 98 unique papers, 34 tags, 30 topic entry
points and 47 archived Markdown notes. Original project reports remain in place;
the migration provenance and scripts stay in the library, outside this repository.
Workspace-root `AGENTS.md` requires future paper reports to be synchronized there.
The earlier sample-only scope above is historical.

Reusable changes in this follow-up:

- Added a sidebar shortcut and heading for topic, comparison and learning routes.
- Clamped index summaries to three lines while preserving complete card titles.
- Kept MathJax away from Mermaid source nodes and allowed long numbered display
  formulas to scroll inside the report column, including on phones.
- Bundled the matching MathJax 3.2.2 boldsymbol extension for offline formulas;
  upstream source, byte comparison and checksum are recorded beside the asset.
- Let browser tests validate libraries larger than the three-report preview while
  retaining the original examples for reader and interaction coverage.

Validation actually run from this skill root:

```bash
python3 scripts/build_library.py /mnt/user-ssd/baichenxu/reading-library
python3 scripts/build_library.py /mnt/user-ssd/baichenxu/reading-library --check
PAPER_READING_SITE=/mnt/user-ssd/baichenxu/reading-library python3 -m pytest tests/test_library.py tests/test_browser.py -q
python3 -m py_compile scripts/build_library.py tests/test_browser.py
node --check templates/site.js
node --check templates/vendor/mathjax/input/tex/extensions/boldsymbol.js
git diff --check
```

- 19 tests passed in 32.12 seconds; builder check passed for 98 papers / 129 pages.
- The external archive's validator checked 279 HTML pages / 9,903 local references
  with zero errors; all 133 source reports/chapters retained their original hashes.
- Its Chromium sweep checked all 98 reports with no image, Mermaid, MathJax,
  JavaScript or mobile overflow errors. HTTP smoke verified the real view URL,
  index search, formulas and supplemental-note navigation; served index/CSS/extension
  bytes matched local files. No persistent HTTP server was started.
- Legacy paper claims were not reverified against all original PDFs. The migration
  records identify unavailable source links and keep 94 unknown reading dates null.
