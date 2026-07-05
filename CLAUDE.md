# CLAUDE.md — Almar DDT Photo Manager (prototype)

Context for agents working in this repo. Read this first, then the files in `docs/`.

## What this is

A **clickable UI prototype** for **Almar Consulting**'s "DDT Photo Manager" — a tool
that helps a building-inspection team turn a folder of technical-visit photos into the
photographic section (**"Section 11 · Photographic Report"**) of a **DDT** report.

The product ships as **one bundled HTML file** with no build step:

- `DDT Photo Manager v3 - Standalone.html` — ~5 MB, **compiled/bundled artifact** (distributable).

An **editable, decompiled form of the same app** now lives in `src/` (see below), with
extract/repack tooling in `tools/`. It is a design prototype, not production software: the
"AI" steps are scripted `setTimeout` animations and the dataset is hardcoded.

**Network note:** photos, fonts, the logo, and the `dc-runtime` engine are embedded, **but
React 18.3.1 / ReactDOM 18.3.1 (and Babel 7.29.0 if needed) are fetched from `unpkg.com` at
runtime.** So the file needs internet on first paint — it is *not* fully offline.

There is no package.json and no git repo here.

## The catch: the HTML is a compiled bundle, not editable source

The `.html` file is only ~187 physical lines but three of them are enormous:

| Line | `<script>` type | Content |
|------|-----------------|---------|
| 176  | `__bundler/manifest`     | JSON of 48 base64+gzip assets (36 photos, 10 fonts, 1 logo, the runtime JS) |
| 180  | `__bundler/ext_resources`| maps photo ids (`p05`…) → asset UUIDs → `window.__resources` |
| 184  | `__bundler/template`     | JSON-escaped string: the actual **app HTML + app source** |

A small loader script (top of the file) unpacks the manifest into blob URLs at runtime,
substitutes UUIDs in the template, and boots the app with Babel-in-the-browser.

**You cannot meaningfully hand-edit this file in place.** The app lives inside the
JSON-escaped `template` string. This has already been decompiled for you:

- **`src/`** — the editable app: readable `index.html` (template + logic) plus real
  `assets/` (photos, fonts, logo) and `vendor/dc-runtime.js`. **Edit here.** See `src/README.md`.
- **`tools/extract.py`** — standalone bundle → `src/` (already run; re-run to re-sync).
- **`tools/build_standalone.py`** — `src/` → distributable standalone (round-trip verified
  byte-identical for code edits).

See `docs/ARCHITECTURE.md` for the bundle format and `docs/APP.md` for what the app does.

## Golden rules for editing

1. **Edit in `src/index.html`, not the giant standalone lines.** Repack with
   `tools/build_standalone.py` when you need the single-file deliverable.
2. **Preserve the bundle contract.** The repack re-escapes the template into the JSON
   `template` script (`</script>` → `<\/script>`) and maps local asset paths back to UUIDs.
   Don't hand-touch the loader, manifest, or `ext_resources` unless you're adding assets.
3. **Confirm before overwriting `DDT Photo Manager v3 - Standalone.html`** — it's the only
   copy and there's no git history. `build_standalone.py` writes a new file by default.
4. **The app is a scripted prototype.** Keep flows deterministic; don't wire real ML,
   uploads, or network calls unless explicitly asked.

## Verifying a change

Serve `src/` and open it (browser blocks `file://` asset loads):

```bash
cd src && python3 -m http.server 8000   # → http://localhost:8000/index.html
```

You should see the 3-step wizard (Upload → Group → Report). There is no test suite; use the
browser-automation tools to click through and screenshot. Needs internet (React from unpkg).

## Pointers

- `src/README.md` — how to run and edit the decompiled app; repack instructions.
- `docs/ARCHITECTURE.md` — bundle format, the `dc-runtime` templating engine, extract/repack tooling.
- `docs/APP.md` — screens, state machine, data model, design tokens, template directives.
- `tools/extract.py`, `tools/build_standalone.py` — the decompile / recompile scripts.
