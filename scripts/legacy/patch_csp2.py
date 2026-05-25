import os

directory = "/Users/alexeiferreira/Lx8Labs/internal/Website"
old_script_src = "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net;"
new_script_src = "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://www.gstatic.com;"

count = 0
for root, dirs, files in os.walk(directory):
    if '.git' in root or '.github' in root:
        continue
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if old_script_src in content:
                new_content = content.replace(old_script_src, new_script_src)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1

print(f"Patched script-src in {count} HTML files to allow gstatic.")
