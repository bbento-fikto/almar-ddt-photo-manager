# src/ — editable sources

This tree is the **decompiled, editable form** of `../DDT Photo Manager v3 - Standalone.html`.
It was produced by `../tools/extract.py` and round-trips losslessly back to a standalone
bundle via `../tools/build_standalone.py`.

```
src/
  index.html          ← EDIT THIS. The <x-dc> template markup + the component logic
                        (class Component extends DCLogic). ~90 KB, readable.
  vendor/
    dc-runtime.js      ← the rendering engine (GENERATED upstream — do not edit)
  assets/
    photos/pNN.jpg     ← 36 real photos, referenced in code as photo n → pNN
    fonts/*.woff2      ← Hanken Grotesk + JetBrains Mono
    logo.png           ← Almar Consulting logo
```

## Run it

`index.html` references assets with relative paths, so serve the folder over HTTP
(the browser blocks `file://` module/asset loads, and Chrome-extension automation can't open
`file://`):

```bash
cd src && python3 -m http.server 8000
# open http://localhost:8000/index.html
```

**Requires internet on first paint:** `dc-runtime.js` fetches React 18.3.1, ReactDOM 18.3.1,
and (if needed) Babel 7.29.0 from `unpkg.com`. Everything else (photos, fonts, logo, engine)
is local. Verified working — renders the full Upload → Group → Report wizard.

## Edit it

Everything you'd change lives in `index.html`:

- **Markup** — inside `<x-dc>…</x-dc>`, using `{{ }}`, `<sc-if>`, `<sc-for>`
  (see `../docs/APP.md` → template directives).
- **Logic / data** — the `class Component extends DCLogic` in the
  `<script type="text/x-dc" data-dc-script>` block: `state`, the `build*()`/`group*()` data
  methods, and `renderVals()` (the view-model). The runtime requires this script to be
  **inline** (it reads `.textContent`), so it can't be split into its own file.

## Ship it (repack to the distributable single file)

```bash
python3 ../tools/build_standalone.py src/index.html "DDT Photo Manager - rebuilt.html"
```

This reuses the original bundle as a scaffold and swaps in your edited template, mapping
local asset paths back to bundle UUIDs. It repacks **code** edits only — if you add or
replace a photo/font, the manifest must be regenerated (see `../docs/ARCHITECTURE.md`).

> Provenance note: the running app's header reads "TDD · Madrid — Prepared by Fikto" for the
> demo property "María de Molina 50". This is a design prototype; all data is hardcoded.
