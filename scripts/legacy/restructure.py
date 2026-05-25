import os
import shutil
import re

# Base directory
base_dir = "/Users/alexeiferreira/Lx8Labs/internal/Website"

# Files to convert
pages = [
    "tupa", "aimem", "research", "shop", "courses", 
    "team", "changelog", "products", "login", "admin", 
    "about", "privacy", "impressum", "now", "unity"
]

# Step 1: Restructure files
for page in pages:
    file_path = os.path.join(base_dir, f"{page}.html")
    if os.path.exists(file_path):
        dir_path = os.path.join(base_dir, page)
        os.makedirs(dir_path, exist_ok=True)
        dest_path = os.path.join(dir_path, "index.html")
        shutil.move(file_path, dest_path)
        print(f"Moved {page}.html -> {page}/index.html")

# Step 2: Update links in all HTML files
def update_links(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for page in pages:
        # Match href="/page.html" or href="page.html"
        pattern1 = f'href="/{page}.html"'
        replace1 = f'href="/{page}/"'
        content = content.replace(pattern1, replace1)
        
        pattern2 = f'href="{page}.html"'
        replace2 = f'href="/{page}/"'
        content = content.replace(pattern2, replace2)
        
        pattern3 = f'href="/{page}.html#'
        replace3 = f'href="/{page}/#'
        content = content.replace(pattern3, replace3)
        
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated links in {filepath}")

for root, dirs, files in os.walk(base_dir):
    # Ignore hidden dirs or script dirs
    if '.gemini' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.html'):
            update_links(os.path.join(root, file))

print("Restructuring complete.")
