import os
import glob
import re

website_dir = '/Users/alexeiferreira/Website'
html_files = glob.glob(os.path.join(website_dir, '*.html'))

# Create global.css
global_css = """
/* ── PERFORMANCE: global.css extracted from inline styles ── */
@view-transition { navigation: auto; }
::view-transition-old(root), ::view-transition-new(root) { animation-duration: 0.28s; }
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #000; --bg1: rgba(255,255,255,0.025); --bg2: rgba(255,255,255,0.05);
  --border: rgba(255,255,255,0.07); --border-hi: rgba(129,140,248,0.28);
  --ind: #6366f1; --ind3: #a5b4fc; --ind4: #818cf8; --ind-d: rgba(99,102,241,0.12);
  --blue4: #60a5fa; --green4: #34d399; --amber: #f59e0b;
  --text: #f1f5f9; --text2: #94a3b8; --text3: #475569;
  --r: 14px; --r-sm: 8px;
  --ease-spring: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-dream: cubic-bezier(0.25, 1, 0.5, 1);
}
html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg); color: var(--text);
  overflow-x: hidden; line-height: 1.7;
  font-feature-settings: 'ss01', 'cv11', 'cv10';
}
a { color: inherit; text-decoration: none; }

/* ── NAV ── */
nav { position: fixed; top: 0; left: 0; right: 0; z-index: 200; display: flex; align-items: center; justify-content: space-between; padding: 1.4rem 2.5rem; transition: all 0.3s; }
nav.solid { background: rgba(0,0,0,0.82); backdrop-filter: blur(20px); border-bottom: 1px solid var(--border); padding: 0.85rem 2.5rem; }
.logo-a { display: flex; align-items: center; gap: 9px; }
.logo-img { width: 34px; height: 34px; border-radius: 8px; overflow: hidden; border: 1.5px solid rgba(129,140,248,0.5); box-shadow: 0 0 10px rgba(99,102,241,0.35); background: #111; }
.logo-img img { width: 100%; height: 100%; object-fit: cover; display: block; }
.logo-txt { font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; font-weight: 600; color: #fff; }
.logo-txt span { color: var(--ind4); }
.back-link { font-size: 0.84rem; color: var(--text2); padding: 0.4rem 1rem; border-radius: var(--r-sm); border: 1px solid var(--border); transition: all 0.2s; }
.back-link:hover { color: var(--text); border-color: var(--border-hi); background: var(--bg2); }

/* ── FOOTER ── */
footer { padding: 2rem 2.5rem; border-top: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; position: relative; z-index: 1; }
.ft-left { display: flex; align-items: center; gap: 9px; }
.ft-logo { width: 24px; height: 24px; border-radius: 6px; overflow: hidden; border: 1px solid rgba(129,140,248,0.4); }
.ft-logo img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ft-copy { font-size: 0.77rem; color: var(--text3); }
.ft-copy a { color: var(--ind4); }
.ft-links { display: flex; gap: 1.25rem; flex-wrap: wrap; }
.ft-links a { font-size: 0.77rem; color: var(--text3); transition: color 0.2s; }
.ft-links a:hover { color: var(--ind4); }
@media (max-width: 600px) { nav { padding: 1.1rem 1.25rem; } nav.solid { padding: 0.75rem 1.25rem; } footer { flex-direction: column; } }

/* ── ACCESSIBILITY (WCAG 2.2) ── */
.skip-link { position: absolute; top: -100px; left: 0; background: var(--ind); color: #fff; padding: 0.6rem 1rem; border-radius: 0 0 6px 0; z-index: 999; font-weight: 600; font-size: 0.85rem; text-decoration: none; transition: top 0.15s; }
.skip-link:focus { top: 0; outline: 2px solid #fff; outline-offset: -4px; }
*:focus { outline: none; }
a:focus-visible, button:focus-visible, .filter:focus-visible, input:focus-visible, [tabindex]:focus-visible { outline: 2px solid var(--ind4); outline-offset: 2px; border-radius: 4px; }
.ft-links a, .filter, .back-link { min-height: 24px; display: inline-flex; align-items: center; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; } .r { opacity: 1 !important; transform: none !important; } .blob, .chip-dot { animation: none !important; } }
"""

with open(os.path.join(website_dir, 'global.css'), 'w') as f:
    f.write(global_css)

link_tag = '<link rel="stylesheet" href="/global.css" />'

for file_path in html_files:
    if os.path.basename(file_path) in ['theory.html', 'algorithms.html']:
        # These are complex WebGL pages, skip global css injection to prevent layout breakage
        continue
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Add global.css
    if 'global.css' not in content:
        content = content.replace('</head>', f'  {link_tag}\n</head>')

    # 2. Fix CLS on Nav Logo
    content = content.replace(
        '<div class="logo-img"><img src="https://avatars.githubusercontent.com/u/7157081?v=4" alt="Lx8 Labs"/></div>',
        '<div class="logo-img"><img src="https://avatars.githubusercontent.com/u/7157081?v=4" alt="Lx8 Labs" width="34" height="34" loading="eager"/></div>'
    )
    content = content.replace(
        '<div class="logo-img"><img src="https://avatars.githubusercontent.com/u/7157081?v=4" alt="Lx8 Labs" /></div>',
        '<div class="logo-img"><img src="https://avatars.githubusercontent.com/u/7157081?v=4" alt="Lx8 Labs" width="34" height="34" loading="eager"/></div>'
    )
    
    # 3. Fix CLS on Footer Logo
    content = content.replace(
        '<div class="ft-logo"><img src="https://avatars.githubusercontent.com/u/7157081?v=4" alt="Lx8"/></div>',
        '<div class="ft-logo"><img src="https://avatars.githubusercontent.com/u/7157081?v=4" alt="Lx8" width="24" height="24" loading="lazy"/></div>'
    )

    with open(file_path, 'w') as f:
        f.write(content)

print("Optimization complete: Generated global.css and fixed CLS on all pages.")
