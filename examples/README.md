# Reading-library preview

The preview lives outside the skill repository. On this installation its index is
`/mnt/user-ssd/baichenxu/reading-library/index.html` ([open in browser](http://s-20260601154539-r653m-j57r1.bcecn-bj-cloudml.xiaomi.srv/view/mnt/user-ssd/baichenxu/reading-library/index.html)).
It is built from three existing Chinese reading reports. Source reports remain
unchanged. The preview adds the
new visual hierarchy, canonical tags, image source links, a teaching diagram and
a chart redrawn from the existing report's human-evaluation table. Scientific
claims and repository availability retain the original notes' verification dates;
this UI task did not reread all source papers.

`preview-selection.json` records the selected papers and reviewed tags. Unknown
legacy reading dates stay null. `preview-additions/` contains two explicitly
attributed illustration fragments used only for this preview.

To reproduce into a NEW directory (BeautifulSoup is required):

```bash
python3 scripts/preview_existing.py \
  --source /mnt/user-ssd/baichenxu/gen_agent/papers/reports \
  --selection examples/preview-selection.json \
  --output /path/to/new-preview
```

The helper copies the selected HTML and referenced figures/evidence only, uses
local vendor libraries, and runs the library builder plus resource validation.
It deliberately rejects an existing output directory. Bulk migration of old
custom indexes/reading routes should follow review of this preview.

To refresh templates/catalogs for this existing external preview and run acceptance:

```bash
python3 scripts/build_library.py /mnt/user-ssd/baichenxu/reading-library
python3 scripts/build_library.py /mnt/user-ssd/baichenxu/reading-library --check
PAPER_READING_SITE=/mnt/user-ssd/baichenxu/reading-library python3 -m pytest tests/test_browser.py -q
```

Keep generated libraries, images, catalogs and their backups outside this checkout;
only this recipe, reviewed selection and illustration source snippets belong here.
