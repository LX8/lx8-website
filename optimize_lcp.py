import os
import glob
import re

html_files = glob.glob('/Users/alexeiferreira/Website/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add fetchpriority to the navbar logo which is eager
    content = content.replace('loading="eager"', 'loading="eager" fetchpriority="high" decoding="async"')
    
    # Add decoding="async" to footer logo
    content = content.replace('loading="lazy"', 'loading="lazy" decoding="async"')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Added fetchpriority and decoding optimizations to all HTML files.")
