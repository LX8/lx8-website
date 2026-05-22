import re

path = "/Users/alexeiferreira/Website/products/index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all internal .html links with trailing slashes
content = re.sub(r'href="/([a-z0-9_-]+)\.html(#[a-z0-9_-]+)?"', lambda m: f'href="/{m.group(1)}/{m.group(2) or ""}"', content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
