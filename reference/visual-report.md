# Illustrated report contract

Illustrations should answer a reader's question, close to the paragraph that asks
it. Use the report template's `.visual-panel`, `.visual-heading`, `.figure-guide`
and `.figure-source`; keep the visual vocabulary consistent across papers.

## Plan before drafting

For an ordinary empirical methods paper, plan these roles (usually 4–6 distinct
visuals; adapt to evidence and paper type, do not impose an image quota):

| Reader's question | Preferred visual | Placement |
|---|---|---|
| What is the whole idea? | Best original architecture/teaser figure | Five-minute read |
| How does input become output? | Redrawn Mermaid / SVG data flow | Method overview |
| What actually happens to one example? | Step diagram with concrete intermediate states | Walkthrough |
| Which result supports the claim? | Source table + redrawn comparison chart | Experiments |
| What does success or failure look like? | Original qualitative samples; failure cases if reported | Visual results |
| How does this relate to prior work? | Labeled lineage / comparison diagram | Related work |

Do not repeat one architecture image as both the core figure and method illustration
unless each view teaches a distinct point. Long methods should interleave explanatory
diagrams and prose, rather than placing all the pictures in a gallery at the end.

## Explain and attribute every visual

- Label provenance: **论文原图**, **据原表重绘**, or **讲解示意**. A diagram made for this
  report must never look like empirical evidence. Teaching inputs/intermediate values
  that were not actually run must say **教学示例，非实际运行结果**.
- Write a descriptive alt text. For inline SVG use `role="img"`, an accessible title
  and description (unique IDs). Mermaid has a nearby prose equivalent / caption.
- Each caption says **what to look at → what it shows → what it cannot establish**.
  The `.figure-guide` can point to a panel, arrow or pair of rows; avoid "效果很好".
- Every extracted figure links to its figure number and PDF page (1-based), with the
  full original caption in `details.orig-cap`. Verify caption anchors and page text
  as well as viewing the image; the extractor is heuristic, not proof of correctness.
- Every quantitative redraw names table/figure/page, evaluation setting, baseline,
  metric direction and units. Keep source values in an adjacent table or a data
  sidecar. Do not mix incompatible datasets/protocols, invent missing values, truncate
  bar axes to exaggerate differences, or fabricate uncertainty intervals.
- A case-study paper may have no numerical benchmark. Use a qualitative comparison
  and an evidence/limitations table in place of headline improvement numbers.
- Preserve original figures in their aspect ratio; do not crop away legends/axes.
  Use readable labels, stable method colors, and patterns/text as well as color.

## Reader experience

- Keep the index compact: three columns on wide desktops, two on smaller screens,
  one on phones, with 160px cover thumbnails and 20px card titles. Always display
  the complete official title with natural wrapping; never clamp or abbreviate it.
  The report itself keeps the wider text and image layout described below.
- Summary → core visual → explanation → evidence → limits. Keep reference links and
  tags near the title, with compact navigation that does not cover the text.
- Use a broad reading column (up to 1180px) and 20px default body text. Scale figure
  captions/tables with the text, and reserve a separate desktop TOC column so wider
  figures cannot collide with navigation. Focus mode keeps the broad column. On
  phones reduce side padding instead of shrinking text; tables and long formulas
  scroll internally, and long identifiers/links wrap within the text column. Reader
  controls allow 16–26px text and retain an explicitly saved size preference.
- Images open in a keyboard-accessible dialog (Enter/Space; Escape to close), with
  an original-image link for full resolution. Avoid nesting an image button in an
  anchor; let shared `site.js` add zoom behavior to the image.
- Tables scroll inside their container on phones. The mobile TOC is expandable;
  desktop TOC highlights the current section. Preserve visible keyboard focus.
- Code-copy falls back to selecting text when clipboard permissions are unavailable.
  Print mode expands details and hides controls; the on-screen view is restored.
- Use local CSS/JS/MathJax/Mermaid, no web fonts/CDN dependency. Large images lazy-load,
  except the core figure. No server is needed to open the site locally.

## Delivery gate

Run `build_library.py <topic> --check`. In a browser, verify a desktop and phone
viewport: real images loaded, Mermaid rendered, equations rendered where applicable,
no horizontal page overflow, TOC targets visible, zoom/escape/focus return, search +
two tags + reset + exports. Inspect screenshots. Automated structural checks do
not prove a crop, numeric transcription or scientific conclusion is correct; report
those checks separately and fix factual issues against the paper.
