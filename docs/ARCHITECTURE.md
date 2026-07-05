# Architecture — the bundle format & runtime

This file explains how `DDT Photo Manager v3 - Standalone.html` is put together and how to
safely take it apart and rebuild it. Read `CLAUDE.md` first for the high-level picture.

## Physical layout of the file

~187 lines. Almost everything interesting is on a handful of very long lines. Get an
accurate map before touching anything:

```bash
python3 - <<'PY'
f='DDT Photo Manager v3 - Standalone.html'
for i,l in enumerate(open(f)):
    if len(l) > 300 or l.strip().startswith('<script'):
        print(i, len(l), repr(l[:70]))
PY
```

Structure (0-indexed line numbers — re-check them, they can shift after an edit):

- **lines ~38–173** — the **loader** `<script>`. Plain, human-readable. Unpacks assets,
  rewrites the template, injects `window.__resources`, boots Babel. Don't edit casually.
- **line ~176** — `<script type="__bundler/manifest">` → one big JSON object
  `{ uuid: { mime, compressed, data(base64) } }`, 48 entries.
- **line ~180** — `<script type="__bundler/ext_resources">` → JSON array
  `[{ id:"p05", uuid:"…" }]`. The loader turns this into
  `window.__resources = { p05: "blob:…" }`.
- **line ~184** — `<script type="__bundler/template">` → a **JSON-encoded string** holding
  the real app HTML. This is where the app source lives.

### How the loader boots (what runs at page load)

1. `JSON.parse` the manifest; for each asset base64-decode and, if `compressed`,
   `DecompressionStream('gzip')` → `Blob` → `URL.createObjectURL`.
2. `JSON.parse` the template string; replace every asset UUID with its blob URL.
3. Strip `integrity`/`crossorigin` attrs; inject `window.__resources` right after `<head>`.
4. Parse the template into a document, swap in the root, re-create `<script>` tags so they
   execute. `text/babel` scripts get transformed by **Babel standalone**.

## Inside the template: the `dc-runtime` component system

The decoded template is an HTML document containing:

- `<script src="618b08dd-…">` — the **`dc-runtime`** engine (an embedded asset; JS compiled
  "from dc-runtime/src/*.ts"). It reads a `<x-dc>` element as the markup template and a
  `<script type="text/x-dc" data-dc-script>` as the component logic, and renders with
  `window.React` / `window.ReactDOM`. **`dc-runtime` lazy-loads React 18.3.1, ReactDOM
  18.3.1, and (on demand) Babel 7.29.0 from `unpkg.com` with SRI hashes** — so the app is
  *not* fully offline; it needs network on first paint. These are the only non-embedded deps.
- `<x-dc>…</x-dc>` — the **markup template** using a small directive language (below).
- `<script type="text/x-dc" data-dc-script>` — a single `class Component extends DCLogic`
  with React-style `state` + `setState`, and a `renderVals()` method that returns the
  view-model object the template binds to.

### Template directive language (used inside `<x-dc>`)

| Directive | Meaning |
|-----------|---------|
| `{{ expr }}` | interpolate a value from `renderVals()` (text, style values, or handlers) |
| `onclick="{{ handler }}"` | bind an event to a function from the view-model |
| `disabled="{{ bool }}"` | bind an attribute to a boolean |
| `<sc-if value="{{ cond }}">…</sc-if>` | conditional block |
| `<sc-for list="{{ arr }}" as="p">…</sc-for>` | list rendering; `{{ p.field }}` inside |
| `hint-placeholder-*` | **design-tool preview hints only** (e.g. `hint-placeholder-count="28"`, `hint-placeholder-val="{{ false }}"`). They tell the static previewer how to render before state exists; they do not affect runtime. Keep them plausible when editing. |

Everything is inline-styled; colors come from CSS custom properties defined on one wrapper
`<div style="--ink:…;--navy:…;…">` (see `docs/APP.md` → Design tokens).

## Extract → edit → repack

This is already scripted and round-trip verified (byte-identical template for code edits).
Prefer the tools over ad-hoc snippets.

### 1. Extract → editable `src/` tree

```bash
python3 tools/extract.py            # DDT …Standalone.html  →  src/
```

Decodes all 48 assets to real files (`src/assets/…`, `src/vendor/dc-runtime.js`) and writes
`src/index.html` with every asset UUID rewritten to a local relative path. **Edit
`src/index.html`** — it holds both the `<x-dc>` markup and the `class Component` logic (the
runtime requires the logic inline, so it can't be a separate file). See `src/README.md`.

Run it (browser blocks `file://` asset loads):

```bash
cd src && python3 -m http.server 8000   # → http://localhost:8000/index.html
```

### 2. Repack `src/` → distributable standalone

```bash
python3 tools/build_standalone.py src/index.html "DDT Photo Manager - rebuilt.html"
```

Uses the original bundle as a scaffold, maps local asset paths back to UUIDs, and re-encodes
the template as the JSON `template` script (escaping `</script>` → `<\/script>`). It repacks
**code** edits; **new/replaced binary assets need the manifest regenerated** (§3).

Under the hood the template is one JSON string, so re-encoding is `json.dumps(...)` plus the
`</script>` escape. The build script does exactly this against the original file's scaffold.

### 3. Working with the embedded assets (photos, fonts, logo)

- Photo `pNN` → look up its UUID in `ext_resources`, then the base64 in `manifest`.
- To decode one asset for inspection:

```bash
python3 - <<'PY'
import json, base64, gzip
lines=open('DDT Photo Manager v3 - Standalone.html').readlines()
mi=next(i for i,l in enumerate(lines) if 'type="__bundler/manifest"' in l)+1
m=json.loads(lines[mi])
uuid='618b08dd-79ef-4ef3-9608-bd329c1e666b'          # the dc-runtime JS
d=base64.b64decode(m[uuid]['data'])
if m[uuid]['compressed']: d=gzip.decompress(d)
open('dc-runtime.js','wb').write(d)
PY
```

Adding a new photo means: create the asset entry in `manifest` (base64 of gzip, set
`compressed`/`mime`), add an `{id,uuid}` to `ext_resources`, and reference it as `pNN` in
the app. This is fiddly — only do it if the task truly needs new imagery.

## Gotchas

- **Line indices shift** after any edit that changes line count. Always re-find script tags
  by their `type="__bundler/…"` marker, never by hardcoded line number.
- **`Date.now`/`Math.random`** are fine in the browser app, but note the runtime relies on
  `window.React`, `window.ReactDOM`, and Babel already being loaded (they're bundled assets).
- **Partial offline**: embedded assets resolve to blob URLs, but React/ReactDOM/Babel come
  from `unpkg.com` at runtime (see above). The bundle needs network on first paint; the
  editable `src/` version needs it too.
- **Single copy**: there is no VCS. Back up before destructive edits; `build_standalone.py`
  writes a new output file rather than overwriting the original.
