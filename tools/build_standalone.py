#!/usr/bin/env python3
"""Repack the editable src/ tree back into a distributable standalone HTML bundle.

Usage: python3 tools/build_standalone.py [src/index.html] [out.html]

Strategy: the original standalone is the scaffold. We only swap the app template
(the <x-dc> markup + component logic) that you edit in src/index.html, mapping local
asset paths (assets/photos/pNN.jpg, vendor/dc-runtime.js, ...) back to their bundle
UUIDs. The embedded assets themselves are copied through unchanged.

Limitation: this repacks CODE edits, not new/changed binary assets. If you add or
replace a photo/font, the manifest must also be regenerated (see docs/ARCHITECTURE.md).
"""
import json, base64, gzip, sys

ORIGINAL = "DDT Photo Manager v3 - Standalone.html"
EDITED   = sys.argv[1] if len(sys.argv) > 1 else "src/index.html"
OUT      = sys.argv[2] if len(sys.argv) > 2 else "DDT Photo Manager - rebuilt.html"

lines = open(ORIGINAL, encoding="utf-8").readlines()

def tag_line(marker):
    ti = next(i for i, l in enumerate(lines)
              if l.lstrip().startswith("<script") and f"__bundler/{marker}" in l)
    return next(i for i in range(ti + 1, ti + 4) if lines[i].strip())

manifest = json.loads(lines[tag_line("manifest")])
extres   = json.loads(lines[tag_line("ext_resources")])
uuid2id  = {e["uuid"]: e["id"] for e in extres}

# same uuid -> local path mapping the extractor used
uuid2path = {}
for uuid, e in manifest.items():
    mime = e.get("mime", "")
    if mime == "text/javascript": uuid2path[uuid] = "vendor/dc-runtime.js"
    elif mime == "image/jpeg":    uuid2path[uuid] = f"assets/photos/{uuid2id.get(uuid, uuid)}.jpg"
    elif mime == "font/woff2":    uuid2path[uuid] = f"assets/fonts/{uuid}.woff2"
    elif mime == "image/png":     uuid2path[uuid] = "assets/logo.png"
    else:                         uuid2path[uuid] = f"assets/{uuid}"

# reverse the rewrite: local path -> uuid (longest paths first to avoid prefixes)
doc = open(EDITED, encoding="utf-8").read()
for uuid, path in sorted(uuid2path.items(), key=lambda kv: -len(kv[1])):
    doc = doc.replace(path, uuid)

# re-encode as the bundler template string (escape </script> so the tag survives)
ti = tag_line("template")
lines[ti] = json.dumps(doc).replace("</script>", "<\\/script>") + "\n"

open(OUT, "w", encoding="utf-8").writelines(lines)
print(f"Wrote {OUT} ({len(open(OUT).read()):,} bytes) from {EDITED}")
