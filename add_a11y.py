import os
import glob

html_files = glob.glob('/Users/alexeiferreira/Lx8Labs/internal/Website/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<script src="/a11y.js"></script>' not in content:
        # We replace the body tag. Some might have body classes, but here we see exactly <body>
        content = content.replace('<body>', '<body>\n<script src="/a11y.js"></script>')
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
print("Updated all HTML files.")
