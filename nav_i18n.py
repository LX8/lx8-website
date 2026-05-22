import os
import glob
import re

html_files = glob.glob('/Users/alexeiferreira/Website/**/*.html', recursive=True)

nav_map = {
    'Products': 'nav.products',
    'Shop': 'nav.shop',
    'Learn': 'nav.learn',
    'Research': 'nav.research',
    'Log': 'nav.log',
    'Studio': 'nav.studio',
    'Work With Us': 'nav.work',
    'Courses': 'nav.learn' # Some pages might have "Courses" instead of "Learn"
}

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # Replace nav links like <a href="..." class="nl">Text</a>
    # We will use regex to find `<a ... class="nl...">Text</a>` and add data-i18n
    for text, key in nav_map.items():
        # Match <a href="..." class="nl">Text</a> or <a href="..." class="nl nl-cta">Text</a>
        # using regex sub. We want to avoid matching ones already containing data-i18n
        pattern = re.compile(rf'(<a[^>]*?class="nl[^>]*?)(>)\s*{text}\s*(</a>)')
        def replacer(match):
            if 'data-i18n' in match.group(1):
                return match.group(0)
            return f'{match.group(1)} data-i18n="{key}"{match.group(2)}{text}{match.group(3)}'
        
        new_content = pattern.sub(replacer, content)
        if new_content != content:
            content = new_content
            modified = True

    if modified:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

print("Nav links tagged with data-i18n in all files.")
