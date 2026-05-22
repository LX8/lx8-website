import re

with open('/Users/alexeiferreira/Website/algorithms/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update #app-container back to full width layout
old_app_css = """    #app-container {
      max-width: 940px;
      margin: 6rem auto 4rem;
      aspect-ratio: 1 / 1;
      height: auto;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 40px 100px rgba(0,0,0,0.6);
      position: relative;
      z-index: 10;
    }"""
new_app_css = """    #app-container {
      max-width: 1400px;
      margin: 4rem auto;
      height: 80vh;
      min-height: 600px;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 40px 100px rgba(0,0,0,0.6);
      position: relative;
      z-index: 10;
    }"""
if old_app_css in content:
    content = content.replace(old_app_css, new_app_css)

# 2. Update #app layout and #sidebar
# The old sidebar is width: 210px
old_sidebar_css = """    #sidebar {
      width: 210px; min-width: 210px; height: 100%;
      background: #06060e; border-right: 1px solid #18183a;
      display: flex; flex-direction: column; overflow-y: auto;
      scrollbar-width: thin; scrollbar-color: #2a2a50 transparent;
    }"""
new_sidebar_css = """    #sidebar {
      width: 320px; min-width: 320px; height: 100%;
      background: rgba(6, 6, 14, 0.95); border-right: 1px solid #18183a;
      display: flex; flex-direction: column;
      position: relative;
    }
    
    #timeline-wrap {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem 1rem;
      scrollbar-width: none;
    }
    #timeline-wrap::-webkit-scrollbar { display: none; }
    
    .tl-node {
      display: flex; gap: 1rem; position: relative; padding-bottom: 2rem; cursor: pointer;
      opacity: 0.6; transition: opacity 0.3s, transform 0.3s;
    }
    .tl-node:hover { opacity: 1; transform: translateX(5px); }
    .tl-node.active { opacity: 1; }
    
    .tl-line {
      width: 2px; background: #18183a; position: absolute; left: 24px; top: 24px; bottom: 0;
    }
    .tl-node:last-child .tl-line { display: none; }
    
    .tl-year {
      width: 48px; font-family: 'Space Grotesk', monospace; font-size: 0.75rem; color: #818cf8;
      text-align: right; font-weight: 700; flex-shrink: 0; padding-top: 3px;
    }
    
    .tl-dot {
      width: 12px; height: 12px; border-radius: 50%; background: #06060e;
      border: 2px solid #3a3a6a; position: relative; z-index: 2; margin-top: 4px;
      transition: all 0.3s;
    }
    .tl-node:hover .tl-dot { border-color: #fbbf24; background: #fbbf24; box-shadow: 0 0 10px rgba(251,191,36,0.5); }
    .tl-node.active .tl-dot { border-color: #10b981; background: #10b981; box-shadow: 0 0 15px rgba(16,185,129,0.5); }
    
    .tl-content { flex: 1; }
    .tl-name { font-weight: 600; color: #e2e8f0; font-size: 0.9rem; margin-bottom: 0.25rem; }
    .tl-creator { font-size: 0.7rem; color: #5c5c8a; font-family: 'Space Grotesk', sans-serif; }
"""
if old_sidebar_css in content:
    content = content.replace(old_sidebar_css, new_sidebar_css)

# 3. Restructure Right Panel (Info)
old_vp_css = """    #vp-panel {
      width: 260px; min-width: 260px; height: 100%;
      background: #06060e; border-left: 1px solid #18183a;
      display: flex; flex-direction: column;
    }"""
new_vp_css = """    #vp-panel {
      width: 340px; min-width: 340px; height: 100%;
      background: rgba(6, 6, 14, 0.95); border-left: 1px solid #18183a;
      display: flex; flex-direction: column; overflow-y: auto; padding: 2rem 1.5rem;
    }
    .hist-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; color: #fff; font-weight: 700; margin-bottom: 0.5rem; }
    .hist-meta { font-family: 'Space Grotesk', monospace; font-size: 0.8rem; color: #fbbf24; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #18183a; }
    
    .hist-section { margin-bottom: 1.5rem; }
    .hist-lbl { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: #6366f1; margin-bottom: 0.5rem; font-weight: 700; }
    .hist-txt { font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; }
    
    .vp-header { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #3a3a6a; margin-top: 2rem; margin-bottom: 1rem; font-weight: 700; border-bottom: 1px solid #18183a; padding-bottom: 0.5rem; }
"""
if old_vp_css in content:
    content = content.replace(old_vp_css, new_vp_css)

# 4. Update #main and Canvas for Square
old_main_css = """    #main { flex: 1; display: flex; flex-direction: column; height: 100%; min-width: 0; }
    #canvas-wrap { flex: 1; position: relative; overflow: hidden; }
    #three-canvas { display: block; width: 100%; height: 100%; }"""
new_main_css = """    #main { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-width: 0; background: #0a0a1a; padding: 2rem; overflow-y: auto; }
    #canvas-wrap { width: 100%; max-width: 500px; aspect-ratio: 1/1; position: relative; overflow: hidden; border-radius: 16px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.05); background: #000; flex-shrink: 0; }
    #three-canvas { display: block; width: 100%; height: 100%; }
    #code-panel { width: 100%; max-width: 500px; margin-top: 1.5rem; flex-shrink: 0; }"""
if old_main_css in content:
    content = content.replace(old_main_css, new_main_css)

# 5. HTML Layout restructuring
old_html_sidebar = """  <aside id="sidebar">
    <div class="sb-logo">⚗ Al-Khwarizmi's Lab</div>
    
    <div style="padding: 0.85rem; background: rgba(99,102,241,0.05); border-bottom: 1px solid #18183a; font-size: 0.72rem; color: #818cf8; line-height: 1.5;">
      <strong>The origin of "Algorithm"</strong><br>
      The term stems from the Latinization of the name of Muhammad ibn Musa al-Khwarizmi, a 9th-century polymath whose work established the foundations of algebra and computational logic.<br>
      <a href="/shop/" style="color: #fbbf24; text-decoration: none; border-bottom: 1px dotted #fbbf24; margin-top: 6px; display: inline-block;">Want to know more? Check the book →</a>
    </div>

    <!-- Search -->
    <div class="sb-search" id="sb-search-wrap">
      <span class="sb-search-icon">⌕</span>
      <input id="sb-search" type="text" placeholder="Filter algorithms (⌘ K)…" autocomplete="off" spellcheck="false"/>
      <button type="button" class="sb-search-clear" id="sb-search-clear" aria-label="Clear">✕</button>
    </div>

    <!-- View toggle -->
    <div class="view-toggle">
      <button type="button" class="vt-btn active" id="vt-chrono" data-view="chrono">List</button>
      <button type="button" class="vt-btn" id="vt-cat" data-view="cat">Category</button>
      <button type="button" class="vt-btn" id="vt-time" data-view="time">Timeline</button>
    </div>

    <div id="sb-list"><!-- populated by JS --></div>

    <div class="algo-info" id="algo-info">
      <div class="algo-info-name" id="info-name">Bubble Sort</div>
      <div class="info-meta">
        <span class="info-year" id="info-year">1956</span>
        <span class="info-creator" id="info-creator">Edward Friend</span>
      </div>
      <div class="cx-row"><span class="cx-lbl">Time</span><span class="cx-val" id="info-time">O(n²)</span></div>
      <div class="cx-row"><span class="cx-lbl">Space</span><span class="cx-val" id="info-space">O(1)</span></div>
      <div class="cx-row"><span class="cx-lbl">Stable</span><span class="cx-val" id="info-stable">Yes</span></div>
      <div class="algo-desc" id="info-desc">Adjacent-pair swaps bubble the largest element to the end each pass.</div>
      <div class="algo-history" id="info-history">First analysed in Friend's 1956 paper...</div>
    </div>
  </aside>"""

new_html_sidebar = """  <aside id="sidebar">
    <div class="sb-logo">⚗ Chronology of Algorithms</div>
    
    <div class="sb-search" id="sb-search-wrap" style="border-bottom: 1px solid #18183a;">
      <span class="sb-search-icon">⌕</span>
      <input id="sb-search" type="text" placeholder="Search history..." autocomplete="off" spellcheck="false"/>
      <button type="button" class="sb-search-clear" id="sb-search-clear" aria-label="Clear">✕</button>
    </div>

    <div id="timeline-wrap">
        <div id="sb-list"></div>
    </div>
  </aside>"""
if "id=\"sidebar\"" in content:
    # Use regex because exact match might fail due to whitespace
    content = re.sub(r'<aside id="sidebar">.*?</aside>', new_html_sidebar, content, flags=re.DOTALL)

old_html_vp = """  <!-- ── RIGHT PANEL (Variables) ── -->
  <aside id="vp-panel">
    <div class="vp-header">Variables</div>
    <div class="vp-list" id="vp-list">
      <div class="vp-empty">Run an algorithm to see live variables.</div>
    </div>
  </aside>"""

new_html_vp = """  <!-- ── RIGHT PANEL (History & Variables) ── -->
  <aside id="vp-panel">
    <div class="hist-title" id="info-name">Algorithm Name</div>
    <div class="hist-meta"><span id="info-year">Year</span> • <span id="info-creator">Creator</span></div>
    
    <div class="hist-section">
      <div class="hist-lbl">Why it was created</div>
      <div class="hist-txt" id="info-desc">Description of the algorithm's purpose.</div>
    </div>
    
    <div class="hist-section">
      <div class="hist-lbl">Historical Context</div>
      <div class="hist-txt" id="info-history">Global historical situation and origins.</div>
    </div>

    <div class="hist-section" style="display:flex; gap: 1rem; margin-top: 1.5rem; background: rgba(99,102,241,0.05); padding: 1rem; border-radius: 8px;">
      <div><div class="hist-lbl" style="font-size:0.55rem;">Time</div><div class="hist-txt" id="info-time" style="font-family:'Space Grotesk', monospace; color:#a5b4fc;">O(n)</div></div>
      <div><div class="hist-lbl" style="font-size:0.55rem;">Space</div><div class="hist-txt" id="info-space" style="font-family:'Space Grotesk', monospace; color:#a5b4fc;">O(1)</div></div>
      <div><div class="hist-lbl" style="font-size:0.55rem;">Stable</div><div class="hist-txt" id="info-stable" style="font-family:'Space Grotesk', monospace; color:#a5b4fc;">Yes</div></div>
    </div>

    <div class="vp-header">Live Variables</div>
    <div class="vp-list" id="vp-list">
      <div class="vp-empty">Run to trace.</div>
    </div>
  </aside>"""
if 'id="vp-panel"' in content:
    content = re.sub(r'<!-- ── RIGHT PANEL \(Variables\) ── -->\s*<aside id="vp-panel">.*?</aside>', new_html_vp, content, flags=re.DOTALL)

# 6. Rewrite JavaScript logic for Timeline Rendering
old_js_render = """function renderSidebar() {
  const q = searchInput.value.toLowerCase().trim();
  let html = '';
  const entries = Object.entries(INFO).filter(([k,v]) => v.name.toLowerCase().includes(q) || v.creator.toLowerCase().includes(q));

  if (viewMode === 'chrono') {
    const sorted = entries.sort((a,b) => a[1].year - b[1].year);
    sorted.forEach(([k,v]) => {
      const act = (k === curAlgo) ? 'active' : '';
      html += `<button class="sb-btn ${act}" onclick="loadAlgo('${k}')">
        <span class="sb-btn-name">${v.name}</span>
        <span class="sb-btn-yr">${v.year<0 ? Math.abs(v.year)+' BC' : v.year}</span>
      </button>`;
    });
  } else if (viewMode === 'cat') {
    const byCat = {};
    entries.forEach(([k,v]) => {
      if(!byCat[v.cat]) byCat[v.cat] = [];
      byCat[v.cat].push([k,v]);
    });
    const order = ['sort','search','graph','tree','math','dp','string','ds'];
    order.forEach(c => {
      if(byCat[c]) {
        html += `<div class="sb-section"><div class="sb-section-title">${c}</div>`;
        byCat[c].forEach(([k,v]) => {
          const act = (k === curAlgo) ? 'active' : '';
          html += `<button class="sb-btn ${act}" onclick="loadAlgo('${k}')"><span class="sb-btn-name">${v.name}</span></button>`;
        });
        html += `</div>`;
      }
    });
  } else if (viewMode === 'time') {
    html += renderTimelineSVG(entries);
  }
  
  sbList.innerHTML = html;
}"""

new_js_render = """function renderSidebar() {
  const q = searchInput.value.toLowerCase().trim();
  let html = '';
  const entries = Object.entries(INFO).filter(([k,v]) => v.name.toLowerCase().includes(q) || v.creator.toLowerCase().includes(q) || v.history.toLowerCase().includes(q));

  // Always Chronological Timeline
  const sorted = entries.sort((a,b) => a[1].year - b[1].year);
  sorted.forEach(([k,v]) => {
    const act = (k === curAlgo) ? 'active' : '';
    const yrStr = v.year < 0 ? Math.abs(v.year) + ' BC' : v.year;
    html += `
      <div class="tl-node ${act}" onclick="loadAlgo('${k}')" id="tl-node-${k}">
        <div class="tl-line"></div>
        <div class="tl-year">${yrStr}</div>
        <div class="tl-dot"></div>
        <div class="tl-content">
          <div class="tl-name">${v.name}</div>
          <div class="tl-creator">${v.creator}</div>
        </div>
      </div>
    `;
  });
  sbList.innerHTML = html;
}"""

if "function renderSidebar()" in content:
    content = re.sub(r'function renderSidebar\(\)\s*{.*?sbList\.innerHTML = html;\n}', new_js_render, content, flags=re.DOTALL)

# Let's ensure toggleView is removed or neutralized since we removed the buttons
toggle_re = r'function setViewMode\(m\)\s*{.*?renderSidebar\(\);\s*}'
content = re.sub(toggle_re, 'function setViewMode(m) { viewMode = m; renderSidebar(); }', content, flags=re.DOTALL)

with open('/Users/alexeiferreira/Website/algorithms/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Rewrote layout and timeline rendering.")
