#!/usr/bin/env python3
"""Extract the compiled standalone HTML bundle into an editable source tree under src/.

Usage:  python3 tools/extract.py ["DDT Photo Manager v3 - Standalone.html"] [src]

Produces:
  src/index.html          -- runnable, UUIDs rewritten to local asset paths (edit this)
  src/app.js              -- the component logic, mirrored out of index.html for reference
  src/vendor/dc-runtime.js-- the (generated) rendering engine, do not edit
  src/assets/photos/*.jpg  src/assets/fonts/*.woff2  src/assets/logo.png
"""
import json, base64, gzip, os, sys, re, html

SRC_HTML = sys.argv[1] if len(sys.argv) > 1 else "DDT Photo Manager v3 - Standalone.html"
OUT      = sys.argv[2] if len(sys.argv) > 2 else "src"

lines = open(SRC_HTML, encoding="utf-8").readlines()

def tag_content(marker):
    """Return the JSON text inside <script type="__bundler/<marker>">…</script>."""
    ti = next(i for i, l in enumerate(lines)
              if l.lstrip().startswith("<script") and f"__bundler/{marker}" in l)
    return next(lines[i] for i in range(ti + 1, ti + 4) if lines[i].strip())

manifest = json.loads(tag_content("manifest"))
extres   = json.loads(tag_content("ext_resources"))
template = json.loads(tag_content("template"))

uuid2id = {e["uuid"]: e["id"] for e in extres}   # photo blobs -> pNN

def asset_bytes(uuid):
    e = manifest[uuid]
    data = base64.b64decode(e["data"])
    return gzip.decompress(data) if e.get("compressed") else data

os.makedirs(f"{OUT}/assets/photos", exist_ok=True)
os.makedirs(f"{OUT}/assets/fonts",  exist_ok=True)
os.makedirs(f"{OUT}/vendor",        exist_ok=True)

# map every asset uuid -> the relative path we will write it to
uuid2path = {}
for uuid, e in manifest.items():
    mime = e.get("mime", "")
    if mime == "text/javascript":
        path = "vendor/dc-runtime.js"
    elif mime == "image/jpeg":
        path = f"assets/photos/{uuid2id.get(uuid, uuid)}.jpg"
    elif mime == "font/woff2":
        path = f"assets/fonts/{uuid}.woff2"
    elif mime == "image/png":
        path = "assets/logo.png"
    else:
        path = f"assets/{uuid}"
    uuid2path[uuid] = path
    with open(f"{OUT}/{path}", "wb") as fh:
        fh.write(asset_bytes(uuid))

# rewrite the template: every asset UUID -> its local relative path
doc = template
for uuid, path in uuid2path.items():
    doc = doc.replace(uuid, path)

with open(f"{OUT}/index.html", "w", encoding="utf-8") as fh:
    fh.write(doc)

# mirror the component logic out for convenient reading/diffing
m = re.search(r'data-dc-script=""[^>]*>(.*?)</script>', doc, re.S)
if m:
    with open(f"{OUT}/app.js", "w", encoding="utf-8") as fh:
        fh.write(html.unescape(m.group(1)).strip() + "\n")

print(f"Extracted {len(manifest)} assets into {OUT}/")
print(f"  photos: {sum(1 for e in manifest.values() if e.get('mime')=='image/jpeg')}"
      f"  fonts: {sum(1 for e in manifest.values() if e.get('mime')=='font/woff2')}")
print(f"Edit {OUT}/index.html (contains the <x-dc> template + the component logic).")
