"""
Compress all 5 section images to WebP at sane resolution + quality,
then emit a JSON manifest with {name, width, height, aspect, base64}.
"""
import base64
import io
import json
import re
import os
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))

# (source file, max width px, webp quality)
SOURCES = [
    ("banner.png",            1920, 78),
    ("a-diamond-today.png",   1920, 80),
    ("every-moment.svg",      1920, 80),
    ("made-slowly.svg",       1920, 80),
    ("experience-avalia.png", 1920, 80),
]

def extract_png_from_svg(path):
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    m = re.search(r'xlink:href="data:image/png;base64,([^"]+)"', data)
    if not m:
        raise RuntimeError(f"No embedded PNG found in {path}")
    return base64.b64decode(m.group(1))

def load_image(path):
    if path.lower().endswith(".svg"):
        raw = extract_png_from_svg(path)
        return Image.open(io.BytesIO(raw))
    return Image.open(path)

def to_webp_b64(img, max_w, quality):
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
    if img.mode == "RGBA":
        # keep alpha
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=quality, method=6)
    else:
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=quality, method=6)
    raw = buf.getvalue()
    return img.width, img.height, len(raw), base64.b64encode(raw).decode("ascii")

results = []
total_b64 = 0
for fname, max_w, q in SOURCES:
    path = os.path.join(ROOT, fname)
    img = load_image(path)
    orig_size = os.path.getsize(path)
    w, h, raw_bytes, b64 = to_webp_b64(img, max_w, q)
    total_b64 += len(b64)
    print(f"{fname}: {orig_size/1024/1024:.2f}MB -> webp {w}x{h} {raw_bytes/1024:.1f}KB (b64 {len(b64)/1024:.1f}KB)")
    results.append({
        "name": fname,
        "width": w,
        "height": h,
        "aspect": round(w / h, 6),
        "b64": b64,
    })

print(f"\nTotal base64 payload: {total_b64/1024/1024:.2f} MB")

with open(os.path.join(ROOT, "_images.json"), "w", encoding="utf-8") as f:
    json.dump(results, f)
print("wrote _images.json")
