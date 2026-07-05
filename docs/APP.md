# App reference — DDT Photo Manager

What the prototype actually does, its state, and its data. The logic lives in the
`class Component extends DCLogic` inside the template (`docs/ARCHITECTURE.md` explains how to
extract it as `extracted_app.js`). The view-model is produced by `renderVals()` and consumed
by the `<x-dc>` template via `{{ }}` / `<sc-if>` / `<sc-for>` directives.

## Product framing

Almar Consulting inspectors return from a site visit with ~64 photos. The tool triages them
into the **Photographic Report (Section 11)** of a **DDT** report. Core promise, stated in the
UI: *"Suggestions require technical validation by Almar. No photo enters the report without
human approval."* Every AI step is human-gated.

## Screen flow (3-step wizard)

State field `screen` (1→2→3) plus `reviewKey` drives everything. A top stepper
(`stepData()`) shows **01 Upload · 02 Group · 03 Report**; step 3 is locked until all groups
are approved (`allApproved()`).

```
Screen 1  Upload / Clean            → startCleaning() [scripted 5-phase loader ~9s]
Screen 2  Group grid                → openReview(key) → Detail review → approve / assign
                                     → gotoReport() [scripted 5-phase loader, gated] 
Screen 3  Report preview            (final, read-only)
```

### Screen 1 — Upload & de-duplicate
- Shows a folder of 64 photos (`buildGrid()`), highlighting near-duplicates.
- 4 duplicate clusters (`dupDefs()`: `d1..d4`). User picks which shot to keep per cluster and
  resolves it; resolving all collapses the dup card (`dupCardHide`).
- Counters: photos in folder, possible duplicates, removed (`folderStatus`).
- `startCleaning()` runs a fake 5-phase scan animation, then advances to screen 2.

### Screen 2 — Group (grid + detail)
- `buildGroups()` from `groupDefs()`: 6 normal groups + 1 **"Unrecognised"** group.
  Normal group keys: `parking, common, technical, residential, exterior, services`.
  Unknown key: `unrecognised` (`unknown:true`, amber styling).
- Each group card has a suggested main photo, alt thumbnails, an AI caption + reason, and a
  status (Pending review / Approved).
- **Detail review** (`reviewKey` set, view-model `rv`): filmstrip of the group's photos,
  editable caption, "system proposed" reason, and actions:
  - Normal group → **Approve for report** (`approvals[key]=true`), reject, move to another group.
  - Unknown group → **assign each photo** to a real category or remove it
    (`resolvedUnknownFiles[file]=true`); the group clears once all its photos are assigned.
- Report button unlocks only when `allApproved()` (all 6 approved **and** all unknown photos
  resolved). `gotoReport()` plays a second 5-phase loader, then screen 3.

### Screen 3 — Report preview
- `buildReport()` renders **7 sections** (Exterior/access, Reception/common, Parking/storage,
  Technical rooms, Residential units, Services/safety, Detail photos) with 2–3 photos each,
  captions, and Approved / "Verify on site" status. Read-only final preview.

## State shape (`this.state`)

| Field | Purpose |
|-------|---------|
| `screen` | 1/2/3 wizard position |
| `loading`,`loadingPhase` | screen-1 scan animation |
| `reportLoading`,`reportLoadingPhase` | screen-2→3 compile animation |
| `reviewKey` | which group's detail view is open (null = grid) |
| `dupKeep` | `{clusterKey: keptIndex}` chosen photo per dup cluster |
| `dupResolved` | `{clusterKey: true}` resolved dup clusters |
| `dupCardHide` | collapse the dup card once all resolved |
| `resolvedUnknownFiles` | `{file: true}` unknown photos that were assigned/removed |
| `approvals` | `{groupKey: true}` approved groups |
| `selectedFile` | current photo in detail filmstrip |
| `editing` | caption edit mode |
| `caption` | working caption text |
| `moveOpen` | move/assign dropdown open |

## Data model & conventions

- Photos are referenced by integer `n`. Filename is derived: `fileFor(n)` →
  `IMG_${2300 + n*13}` (e.g. n=3 → `IMG_2339`). **Display filenames are computed, not stored.**
- Image URL comes from `photoCss(n)`: `window.__resources['p' + zeroPad(n,2)]` (blob URL from
  the bundle), falling back to `assets/photos/pNN.jpg`. Only a subset of `n` values have real
  embedded images (see `ext_resources`, 36 photos); others fall back.
- Everything is hardcoded — counts (64 photos, 4 dup clusters, 7 groups, 7 report sections),
  captions, and "AI reasons" are literals in `groupDefs()`/`buildReport()`. There is no real
  detection, upload, or persistence.

## Design tokens (CSS custom properties)

Defined on one wrapper `<div style="--…">`. Use these variables, don't hardcode hexes.

| Token | Value | Use |
|-------|-------|-----|
| `--ink` | `#16273b` | primary text |
| `--navy` / `--navy-d` | `#2c4866` / `#1c3149` | primary buttons, headings |
| `--blue` | `#3f6fa8` | accents |
| `--teal` / `--teal-soft` | `#1d7c8c` / `#e4f1f3` | selection, "system proposed", active step |
| `--green` / `--green-soft` | `#2f8a5b` / `#e6f3ec` | approved / done |
| `--amber` / `--amber-soft` | `#b9821a` / `#f8eed8` | pending, unrecognised, warnings |
| `--red` / `--red-soft` | `#bf4f49` / `#f7e7e6` | destructive |
| `--bg` / `--card` | `#f3f6fa` / `#ffffff` | page / surfaces |
| `--line` / `--line2` | `#e3e9f0` / `#eef2f7` | borders |
| `--muted` / `--muted2` | `#637488` / `#8a99ab` | secondary text |

Fonts: **Hanken Grotesk** (UI) and **JetBrains Mono** (codes, filenames, kickers) — both
embedded as woff2 assets.

## When editing behavior

- Group definitions, captions, and report sections: edit `groupDefs()` / `buildReport()`.
- Dup clusters: `dupDefs()`. Grid order/contents: `buildGrid()`'s `ns` array.
- Loader copy/timings: the `phaseDefs` arrays and `phaseDurations`/`phases` in
  `startCleaning()` / `gotoReport()`.
- New view state → add to `state`, expose via `renderVals()`, bind in the `<x-dc>` template
  with `{{ }}` / `<sc-if>` / `<sc-for>`. Remember to repack (`docs/ARCHITECTURE.md`).
