import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Shop Section
shop_section = """
<!-- ── SHOP & CREATIONS ── -->
<section id="shop" class="section">
  <div class="inner">
    <div class="lbl r">Shop & Books</div>
    <h2 class="sh r d1">Physical creations & texts.</h2>
    <p class="sdesc r d2">Hardware kits born from our studio, comprehensive books, and partner collaborations.</p>

    <div class="projects-grid" style="margin-bottom: 2rem;">
      <a href="/shop.html" class="p-card bento r d3" style="grid-column: span 12;">
        <div class="bento-bg" style="background: radial-gradient(circle at top right, rgba(245,158,11,0.1), transparent 70%);"></div>
        <div class="bento-content">
          <div class="p-head">
            <div class="p-icon">⚡</div>
            <div class="p-meta">
              <span class="p-label">Hardware Collaboration</span>
              <h3 class="p-name">Circuitmess Batmobile</h3>
            </div>
          </div>
          <p class="p-desc">Build your own autonomous AI-powered robotic car. Learn microelectronics, coding, and computer vision with our partner Circuitmess.</p>
        </div>
      </a>

      <a href="/shop.html" class="p-card bento r d1" style="grid-column: span 6;">
        <div class="bento-bg" style="background: radial-gradient(circle at top right, rgba(167,139,250,0.1), transparent 70%);"></div>
        <div class="bento-content">
          <div class="p-head">
            <div class="p-icon">📖</div>
            <div class="p-meta">
              <span class="p-label">Book (Publishing Soon)</span>
              <h3 class="p-name">The Bipartite Universe</h3>
            </div>
          </div>
          <p class="p-desc">Our foundational text detailing the interaction between photons and gravity at the quantum scale.</p>
        </div>
      </a>

      <a href="/shop.html" class="p-card bento r d2" style="grid-column: span 6;">
        <div class="bento-bg" style="background: radial-gradient(circle at top right, rgba(96,165,250,0.1), transparent 70%);"></div>
        <div class="bento-content">
          <div class="p-head">
            <div class="p-icon">⎈</div>
            <div class="p-meta">
              <span class="p-label">Kit (In R&D)</span>
              <h3 class="p-name">Aegis Swarm Mini</h3>
            </div>
          </div>
          <p class="p-desc">A 3-node starter kit for exploring local LLM-driven topology adaptation and mesh networking.</p>
        </div>
      </a>
    </div>
    
    <div style="text-align: center;" class="r d3">
      <a href="/shop.html" class="btn btn-p" style="background: var(--bg2); color: var(--text); box-shadow: none; border: 1px solid var(--border);">Browse the Full Shop →</a>
    </div>
  </div>
</section>

<div class="divider"></div>
"""

# Insert shop before projects
content = re.sub(r'(<!-- ── PROJECTS ── -->)', shop_section + r'\1', content)

# 2. Add Media Section
media_section = """
<!-- ── MEDIA & YOUTUBE ── -->
<section id="media" class="section" style="padding-bottom: 0;">
  <div class="inner">
    <div class="lbl r">Media</div>
    <h2 class="sh r d1">Watch & Learn.</h2>
    <p class="sdesc r d2">Video breakdowns of complex engineering patterns, physics visualizations, and studio logs.</p>

    <div class="projects-grid">
      <a href="https://youtube.com/@AlexeiFerreira" target="_blank" class="p-card bento r d3" style="grid-column: span 12; min-height: 200px; display: flex; align-items: center; justify-content: center; text-align: center; border-color: rgba(239, 68, 68, 0.4);">
        <div class="bento-bg" style="background: radial-gradient(circle at center, rgba(239,68,68,0.1), transparent 70%);"></div>
        <div class="bento-content" style="align-items: center;">
          <div class="p-icon" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; font-size: 2rem; width: 64px; height: 64px; margin-bottom: 1rem;">▶</div>
          <h3 class="p-name" style="font-size: 1.5rem;">Lx8 Labs on YouTube</h3>
          <p class="p-desc">Subscribe for high-density engineering tutorials, AI workflows, and physics visualizations.</p>
        </div>
      </a>
    </div>
  </div>
</section>
"""

# Insert media before insights
content = re.sub(r'(<!-- ── INSIGHTS / NEWSLETTER ── -->)', media_section + r'\1', content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html successfully updated with Shop and Media sections.")
