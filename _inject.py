"""
Inject base64 webp data URIs into avalia.html:
- replace the 5 <section><img src="..."></section> blocks
  with <section><div class="sX" role="img" aria-label="..."></div></section>
- append CSS rules at the end of the <style> block with aspect-ratio + bg-image.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "avalia.html")

with open(os.path.join(ROOT, "_images.json"), "r", encoding="utf-8") as f:
    manifest = json.load(f)

# map source filename -> {class, ...}
slug_map = {
    "banner.png":            "sa",
    "a-diamond-today.png":   "sb",
    "every-moment.svg":      "sc",
    "Gemini_Generated_Image_k9z7jik9z7jik9z7 (1).png":       "sd",
    "experience-avalia.png": "se",
}

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

# Build CSS rules (one per section)
css_rules = []
for item in manifest:
    slug = slug_map[item["name"]]
    css_rules.append(
        f"  .{slug}{{width:100%;aspect-ratio:{item['width']}/{item['height']};"
        f"background:url(data:image/webp;base64,{item['b64']}) center/cover no-repeat;}}"
    )
css_block = "\n  /* section media */\n" + "\n".join(css_rules) + "\n"

# Insert before closing </style>
html = html.replace("</style>", css_block + "</style>", 1)

# Replace each <img src="X" alt="Y" class="..."/> with a div using the slug
def replace_img(html, src, slug):
    # tolerant regex: <img ... src="src" ... alt="..." ... class="..." ... />
    pattern = re.compile(
        r'<img\s+src="' + re.escape(src) + r'"\s+alt="([^"]*)"\s+class="[^"]*"\s*/>',
        re.IGNORECASE,
    )
    def sub(m):
        alt = m.group(1)
        return f'<div class="{slug}" role="img" aria-label="{alt}"></div>'
    new_html, n = pattern.subn(sub, html)
    if n != 1:
        raise RuntimeError(f"Expected 1 replacement for {src}, got {n}")
    return new_html

for src, slug in slug_map.items():
    html = replace_img(html, src, slug)

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Updated {HTML}")
print(f"Final size: {os.path.getsize(HTML)/1024:.1f} KB")
