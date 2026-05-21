import os
import re

dir_path = "/Users/alexeiferreira/Website"

new_ft_grid = """  <div class="ft-grid">
    <div class="ft-col">
      <div class="ft-col-h">Studio & Shop</div>
      <a href="/">Home</a>
      <a href="/shop.html">Shop &amp; Books</a>
      <a href="/courses.html">Courses</a>
      <a href="/team.html">Team</a>
      <a href="/about.html">About (founder)</a>
      <a href="/now.html">Now</a>
      <a href="/index.html#consulting">Contact</a>
    </div>
    <div class="ft-col">
      <div class="ft-col-h">Products</div>
      <a href="/tupa.html">Tupã IDE</a>
      <a href="/aimem.html">aimem</a>
      <a href="/algorithms.html">Algorithm Lab</a>
      <a href="/products.html">All products</a>
    </div>
    <div class="ft-col">
      <div class="ft-col-h">Research &amp; writing</div>
      <a href="/theory.html">Light, Gravity &amp; Time</a>
      <a href="/research.html">Research</a>
      <a href="/index.html#insights">Insights</a>
      <a href="/changelog.html">Changelog</a>
      <a href="/feed.xml">RSS feed</a>
    </div>
    <div class="ft-col">
      <div class="ft-col-h">Connect</div>
      <a href="https://youtube.com/@AlexeiFerreira" target="_blank" rel="noopener">YouTube ↗</a>
      <a href="https://github.com/LX8" target="_blank" rel="noopener">GitHub ↗</a>
      <a href="https://de.linkedin.com/in/lx8-alexei" target="_blank" rel="noopener">LinkedIn ↗</a>
      <a href="https://x.com/lx8labs" target="_blank" rel="noopener">X ↗</a>
    </div>
  </div>"""

for filename in ['aimem.html', 'products.html', 'research.html', 'team.html']:
    filepath = os.path.join(dir_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace ft-grid
    content = re.sub(r'  <div class="ft-grid">.*?</div>\n  <div class="ft-bottom">', new_ft_grid + '\n  <div class="ft-bottom">', content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("ft-grid updated.")
