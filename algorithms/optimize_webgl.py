import re

with open('/Users/alexeiferreira/Website/algorithms/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# WebGL Idle Render Optimization
old_loop = "(function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();"
new_loop = """
let needsRender = true;
controls.addEventListener('change', () => { needsRender = true; });
// Also trigger render when hovering elements or resizing
window.addEventListener('resize', () => { needsRender = true; });
document.addEventListener('mousemove', () => { if(!isRunning) needsRender = true; });

(function loop() {
  requestAnimationFrame(loop);
  controls.update();
  // Render if running, or if a manual interaction flagged it
  if (isRunning || needsRender) {
    renderer.render(scene, camera);
    needsRender = false;
  }
})();
"""
content = content.replace(old_loop, new_loop)

# Let's also patch the a11y script in the same go since the user wanted it
# 1. Add aria-live announcer div inside #app-container if not exists
if 'id="live-announcer"' not in content:
    content = content.replace(
        '<div id="app-container">',
        '<div id="app-container">\n    <div id="live-announcer" aria-live="polite" style="position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0;"></div>'
    )

# 2. Update hl function
old_hl = """function hl(line) {
  if (line === lastHl) return;
  if (lastHl >= 0 && codeLineEls[lastHl]) codeLineEls[lastHl].classList.remove('active');
  if (line >= 0 && codeLineEls[line]) {
    codeLineEls[line].classList.add('active');
    codeLineEls[line].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
  lastHl = line;
}"""
new_hl = """function hl(line) {
  if (line === lastHl) return;
  if (lastHl >= 0 && codeLineEls[lastHl]) codeLineEls[lastHl].classList.remove('active');
  if (line >= 0 && codeLineEls[line]) {
    codeLineEls[line].classList.add('active');
    codeLineEls[line].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    
    // Accessibility Screen Reader Announcer
    const announcer = document.getElementById('live-announcer');
    if (announcer) {
        announcer.textContent = codeLineEls[line].textContent.replace(/[;{}]/g, '').trim();
    }
  }
  lastHl = line;
  needsRender = true;
}"""
content = content.replace(old_hl, new_hl)

# 3. Add cognitive focus mode CSS
if '.focus-mode .cl:not(.active)' not in content:
    css_patch = """
    /* Cognitive Focus Mode */
    .a11y-dyslexic #code-panel .cl:not(.active) { opacity: 0.35; transition: opacity 0.3s; }
    """
    content = content.replace('</style>', css_patch + '</style>')

# 4. Update makeMat for colorblind textures
old_makemat = """function makeMat(hex) {
  return new THREE.MeshPhongMaterial({ color: hex, shininess: 75, specular: 0x223355 });
}"""

new_makemat = """const textureCache = {};
function createPatternTexture(hex, type) {
  const key = hex + '_' + type;
  if(textureCache[key]) return textureCache[key];
  
  const c = document.createElement('canvas');
  c.width = 64; c.height = 64;
  const ctx = c.getContext('2d');
  
  ctx.fillStyle = '#' + hex.toString(16).padStart(6, '0');
  ctx.fillRect(0,0,64,64);
  
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  if (type === 'stripes') {
    for(let i=0; i<64; i+=16) ctx.fillRect(i, 0, 8, 64);
  } else if (type === 'dots') {
    for(let y=8; y<64; y+=16) {
      for(let x=8; x<64; x+=16) {
        ctx.beginPath(); ctx.arc(x,y,5,0,Math.PI*2); ctx.fill();
      }
    }
  } else if (type === 'grid') {
    for(let i=0; i<64; i+=16) { ctx.fillRect(i,0,4,64); ctx.fillRect(0,i,64,4); }
  }
  
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1, 1);
  textureCache[key] = tex;
  return tex;
}

function makeMat(hex) {
  const isHighContrast = document.documentElement.classList.contains('a11y-high-contrast');
  let map = null;
  
  if (isHighContrast) {
    if (hex === C.cmp) map = createPatternTexture(hex, 'stripes');
    else if (hex === C.swap) map = createPatternTexture(hex, 'grid');
    else if (hex === C.pivot) map = createPatternTexture(hex, 'dots');
    else if (hex === C.sorted || hex === C.found || hex === C.visit) map = createPatternTexture(hex, 'dots');
  }
  
  return new THREE.MeshPhongMaterial({ color: hex, map: map, shininess: 75, specular: 0x223355 });
}"""
content = content.replace(old_makemat, new_makemat)

with open('/Users/alexeiferreira/Website/algorithms/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied WebGL GPU rendering optimizations and A11y patch.")
