import os
import glob
import re

for file in glob.glob('*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. OpenGraph Image Fix
    content = content.replace('og-image.svg', 'og-image.png')
    
    # 2. Render-Blocking JS Fix
    content = content.replace(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>', 
        '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
    )
    content = content.replace(
        '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>', 
        '<script defer src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>'
    )
    
    # 3. Implicit Buttons Fix
    # Match <button followed by attributes, but not if type= is already there
    content = re.sub(r'<button(?![^>]*type=)([^>]*)>', r'<button type="button"\1>', content)
    
    if content != original:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
