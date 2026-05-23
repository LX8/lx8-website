import os
import shutil

base_dir = "/Users/alexeiferreira/Lx8Labs/internal/Website"
pages = ["theory", "algorithms"]

for page in pages:
    file_path = os.path.join(base_dir, f"{page}.html")
    if os.path.exists(file_path):
        dir_path = os.path.join(base_dir, page)
        os.makedirs(dir_path, exist_ok=True)
        dest_path = os.path.join(dir_path, "index.html")
        shutil.move(file_path, dest_path)
        print(f"Moved {page}.html -> {page}/index.html")

def update_links(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for page in pages:
        content = content.replace(f'href="/{page}.html"', f'href="/{page}/"')
        content = content.replace(f'href="{page}.html"', f'href="/{page}/"')
        content = content.replace(f'href="/{page}.html#', f'href="/{page}/#')
        
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated links in {filepath}")

for root, dirs, files in os.walk(base_dir):
    if '.gemini' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.html'):
            update_links(os.path.join(root, file))

print("Secondary restructuring complete.")
