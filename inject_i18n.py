import os
import glob

html_files = glob.glob('/Users/alexeiferreira/Website/**/*.html', recursive=True)

scripts = '<script src="/i18n/translations.js"></script>\n<script src="/i18n/engine.js"></script>\n'

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '/i18n/engine.js' not in content:
        content = content.replace('<script src="/a11y.js"></script>', scripts + '<script src="/a11y.js"></script>')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

print("Injected i18n scripts.")
