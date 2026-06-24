import os
import re

dir_path = "/Users/alexeiferreira/Lx8Labs/internal/Website"

new_nav_links = """  <div class="nav-links">
    <a href="/products.html" class="nl">Products</a>
    <a href="/shop.html"     class="nl">Shop</a>
    <a href="/courses.html"  class="nl">Learn</a>
    <a href="/research.html" class="nl">Research</a>
    <a href="/changelog.html" class="nl">Log</a>
    <a href="/team.html"     class="nl">Studio</a>
    <a href="/index.html#consulting" class="nl nl-cta">Work With Us</a>
  </div>"""

new_mobile_nav = """<div class="mobile-nav" id="mobile-nav">
  <a href="/products.html" onclick="closeMobileNav()">Products</a>
  <a href="/shop.html" onclick="closeMobileNav()">Shop</a>
  <a href="/courses.html" onclick="closeMobileNav()">Learn</a>
  <a href="/research.html" onclick="closeMobileNav()">Research</a>
  <a href="/changelog.html" onclick="closeMobileNav()">Log</a>
  <a href="/team.html" onclick="closeMobileNav()">Studio</a>
  <a href="/index.html#consulting" class="nl-cta" onclick="closeMobileNav()">Work With Us</a>
</div>"""

new_ft_links = """  <div class="ft-links">
    <a href="/">Home</a>
    <a href="/shop.html">Shop & Books</a>
    <a href="/courses.html">Courses</a>
    <a href="/products.html">Products</a>
    <a href="/research.html">Research</a>
    <a href="/changelog.html">Log</a>
    <a href="/team.html">Studio</a>
    <a href="/index.html#consulting">Consulting</a>
    <a href="https://youtube.com/@AlexeiFerreira" target="_blank" rel="noopener">YouTube ↗</a>
    <a href="https://github.com/LX8" target="_blank" rel="noopener">GitHub ↗</a>
    <a href="https://de.linkedin.com/in/lx8-alexei" target="_blank" rel="noopener">LinkedIn ↗</a>
  </div>"""

for filename in os.listdir(dir_path):
    if not filename.endswith(".html"):
        continue
    filepath = os.path.join(dir_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace nav-links
    content = re.sub(r'  <div class="nav-links">.*?</div>', new_nav_links, content, flags=re.DOTALL)
    
    # Replace mobile-nav
    content = re.sub(r'<div class="mobile-nav" id="mobile-nav">.*?</div>', new_mobile_nav, content, flags=re.DOTALL)
    
    # Replace ft-links
    content = re.sub(r'  <div class="ft-links">.*?</div>', new_ft_links, content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Create shop.html based on courses.html
with open(os.path.join(dir_path, 'courses.html'), 'r', encoding='utf-8') as f:
    courses_content = f.read()

# Replace metadata
shop_content = courses_content.replace("<title>Courses", "<title>Shop & Books")
shop_content = shop_content.replace('content="Engineering courses from Lx8 Labs', 'content="Physical creations, books, and courses from Lx8 Labs')
shop_content = shop_content.replace('href="https://lx8labs.com/courses.html"', 'href="https://lx8labs.com/shop.html"')
shop_content = shop_content.replace('Courses — Lx8 Labs', 'Shop & Books — Lx8 Labs')

# Replace Hero
shop_content = re.sub(r'<div class="chip"><div class="chip-dot"></div>Courses · Hands-on training</div>.*?<h1>Engineering, <span>made teachable.</span></h1>.*?<p class="hero-sub">.*?</p>',
                      '<div class="chip"><div class="chip-dot"></div>Hardware · Books · Courses</div>\n  <h1>Creation, <span>in your hands.</span></h1>\n  <p class="hero-sub">Physical hardware kits born from our studio, comprehensive books on the Bipartite Universe, and premium engineering courses.</p>', 
                      shop_content, flags=re.DOTALL)

# Replace Filters
shop_content = re.sub(r'<div class="filters">.*?</div>',
                      '<div class="filters">\n  <button class="filter active" data-tag="all">All</button>\n  <button class="filter" data-tag="hardware">Hardware</button>\n  <button class="filter" data-tag="books">Books</button>\n  <button class="filter" data-tag="digital">Digital</button>\n</div>',
                      shop_content, flags=re.DOTALL)

# Replace Grid content
shop_grid = """
    <article class="course-card r" data-tag="hardware" style="--c:#f59e0b">
      <div class="c-head">
        <div class="c-ico">⚡</div>
        <div class="c-meta">
          <span class="c-level">Hardware · Kit</span>
          <span class="c-name">Circuitmess Batmobile</span>
        </div>
      </div>
      <p class="c-desc">Build your own autonomous AI-powered robotic car. Learn microelectronics, coding, and computer vision with our partner Circuitmess.</p>
      <div class="c-curr">
        <span class="c-curr-item">Camera & Computer Vision AI module</span>
        <span class="c-curr-item">ESP32 microcontroller</span>
        <span class="c-curr-item">DC motors, Wi-Fi, and autonomous driving algorithms</span>
      </div>
      <div class="c-foot">
        <span class="c-status cs-live">Available via Circuitmess</span>
      </div>
    </article>

    <article class="course-card r d1" data-tag="books" style="--c:#a78bfa">
      <div class="c-head">
        <div class="c-ico">📖</div>
        <div class="c-meta">
          <span class="c-level">Book · Hardcover / Digital</span>
          <span class="c-name">The Bipartite Universe</span>
        </div>
      </div>
      <p class="c-desc">Our foundational text detailing the interaction between photons and gravity, exploring the quantum-scale topologies that emerge near singularities.</p>
      <div class="c-foot">
        <span class="c-status cs-soon">Publishing Soon</span>
      </div>
    </article>

    <article class="course-card r d2" data-tag="hardware" style="--c:#60a5fa">
      <div class="c-head">
        <div class="c-ico">⎈</div>
        <div class="c-meta">
          <span class="c-level">Hardware · Kit</span>
          <span class="c-name">Aegis Swarm Mini</span>
        </div>
      </div>
      <p class="c-desc">A 3-node starter kit for exploring local LLM-driven topology adaptation. Includes mesh networking hardware and open-source control loop software.</p>
      <div class="c-foot">
        <span class="c-status cs-wait">In R&D</span>
      </div>
    </article>
    
    <article class="course-card r d3" data-tag="digital" style="--c:#34d399">
      <div class="c-head">
        <div class="c-ico">💻</div>
        <div class="c-meta">
          <span class="c-level">Digital · Training</span>
          <span class="c-name">Engineering Courses</span>
        </div>
      </div>
      <p class="c-desc">Browse our full catalog of no-fluff engineering courses covering Kubernetes, Cloud Architecture, DevSecOps, and AI in Production.</p>
      <div class="c-foot">
        <a href="/courses.html" class="c-status cs-live" style="text-decoration:none">View Catalog →</a>
      </div>
    </article>
"""

shop_content = re.sub(r'<div class="courses-grid">.*?</div>\n</section>',
                      f'<div class="courses-grid">{shop_grid}</div>\n</section>',
                      shop_content, flags=re.DOTALL)

with open(os.path.join(dir_path, 'shop.html'), 'w', encoding='utf-8') as f:
    f.write(shop_content)

print("IA reorganization and shop creation complete.")
