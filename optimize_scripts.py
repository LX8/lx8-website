import os
import glob
import re

html_files = glob.glob('/Users/alexeiferreira/Website/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False

    # Add defer to injected scripts
    scripts_to_defer = ['/i18n/translations.js', '/i18n/engine.js', '/a11y.js']
    for script in scripts_to_defer:
        # Avoid double defer
        if f'<script defer src="{script}"></script>' not in content:
            new_content = content.replace(f'<script src="{script}"></script>', f'<script defer src="{script}"></script>')
            if new_content != content:
                content = new_content
                modified = True

    # Preload the main font if not already there (only in index.html for now)
    if file.endswith('/index.html') and '<link rel="preload"' not in content[:2000]:
        # Preloading bunny fonts
        pass # Actually bunny fonts handles it, we already have preconnect

    if modified:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

print("Added 'defer' to injected scripts in all HTML files to unblock rendering.")
