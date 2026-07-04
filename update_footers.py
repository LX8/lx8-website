import os
import re

base_dir = "/Users/alexeiferreira/Lx8Labs/internal/Website"

svg_social_html = """    <div class="ft-col">
      <div class="ft-col-h">Connect</div>
      <div class="social-grid">
        <a href="https://github.com/LX8" target="_blank" rel="noopener" class="social-icon" aria-label="GitHub">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.38.6.1.82-.26.82-.57v-2c-3.34.73-4.04-1.61-4.04-1.61-.54-1.38-1.33-1.75-1.33-1.75-1.08-.74.08-.72.08-.72 1.2.08 1.83 1.23 1.83 1.23 1.06 1.82 2.78 1.3 3.46.99.11-.77.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.14 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.68.82.57C20.57 21.8 24 17.3 24 12 24 5.37 18.63 0 12 0z"/></svg>
        </a>
        <a href="https://de.linkedin.com/in/lx8-alexei" target="_blank" rel="noopener" class="social-icon" aria-label="LinkedIn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        </a>
        <a href="https://youtube.com/@AlexeiFerreira" target="_blank" rel="noopener" class="social-icon" aria-label="YouTube">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M23.5 6.2c-.2-1-.9-1.7-1.9-1.9C19.9 4 12 4 12 4s-7.9 0-9.6.3c-1 .2-1.7.9-1.9 1.9C.1 8.1 0 12 0 12s.1 3.9.4 5.8c.2 1 .9 1.7 1.9 1.9 1.7.3 9.6.3 9.6.3s7.9 0 9.6-.3c1-.2 1.7-.9 1.9-1.9.4-1.9.4-5.8.4-5.8s0-3.9-.3-5.8zM9.5 15.5V8.5l6.5 3.5-6.5 3.5z"/></svg>
        </a>
      </div>
    </div>"""

social_css = """    .social-grid { display: flex; gap: 12px; flex-wrap: wrap; }
    .social-icon { color: var(--text3); transition: all 0.2s; display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 8px; background: rgba(255,255,255,0.02); border: 1px solid transparent; }
    .social-icon:hover { color: #fff; background: var(--bg2); border-color: var(--border-hi); transform: translateY(-2px); }"""

old_connect_pattern = re.compile(r'<div class="ft-col">\s*<div class="ft-col-h">Connect</div>\s*<a href="[^"]*youtube[^"]*"[^>]*>[^<]*</a>\s*<a href="[^"]*github[^"]*"[^>]*>[^<]*</a>\s*<a href="[^"]*linkedin[^"]*"[^>]*>[^<]*</a>\s*<a href="[^"]*x\.com[^"]*"[^>]*>[^<]*</a>\s*</div>')

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # 1. Replace the old connect column with the SVG version
    if old_connect_pattern.search(content):
        content = old_connect_pattern.sub(svg_social_html, content)
        
        # 2. Add the CSS if missing and if we replaced the HTML
        if '.social-grid' not in content:
            # Inject CSS right before the last closing style tag or inside the CSS block for footer
            content = content.replace('.ft-copy a { color: var(--ind4); }', '.ft-copy a { color: var(--ind4); text-decoration: none; }\n' + social_css)
            # if that didn't work, try other variants
            content = content.replace('.ft-copy a { color: var(--ind4); transition: color 0.2s; }', '.ft-copy a { color: var(--ind4); transition: color 0.2s; }\n' + social_css)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated social footer in {filepath}")

for root, dirs, files in os.walk(base_dir):
    if '.gemini' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.html'):
            update_file(os.path.join(root, file))

print("Global footer update complete.")
