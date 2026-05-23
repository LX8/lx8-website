// Lx8 Labs - Cognitive Accessibility (A11y) Engine
// Custom-built to support engineers/readers with ADHD, Dyslexia, and visual processing differences.

(function() {
  const A11Y_STATE = {
    dyslexic: localStorage.getItem('lx8-a11y-dyslexic') === 'true',
    contrast: localStorage.getItem('lx8-a11y-contrast') === 'true',
    paused: localStorage.getItem('lx8-a11y-paused') === 'true',
    bionic: localStorage.getItem('lx8-a11y-bionic') === 'true',
    ruler: localStorage.getItem('lx8-a11y-ruler') === 'true'
  };

  // Inject Styles dynamically to avoid external dependency issues across subdomains
  const style = document.createElement('style');
  style.textContent = `
    /* Dyslexia Mode - Atkinson Legibility Base */
    body.dyslexic-mode {
      font-family: 'Atkinson Hyperlegible', system-ui, -apple-system, sans-serif !important;
      word-spacing: 0.18em !important;
      letter-spacing: 0.04em !important;
      line-height: 1.85 !important;
    }
    body.dyslexic-mode p, body.dyslexic-mode li {
      color: #f8fafc !important;
    }
    
    /* High Contrast Mode */
    body.high-contrast {
      --text: #ffffff !important;
      --text2: #e2e8f0 !important;
      --bg: #000000 !important;
      --border: #ffffff !important;
      --border-hi: #6366f1 !important;
    }
    body.high-contrast * {
      text-shadow: none !important;
    }
    
    /* Paused Animations */
    body.paused-animations * {
      animation: none !important;
      transition: none !important;
    }

    /* Bionic Reading highlights */
    body.bionic-mode .lx8-bionic-word b {
      font-weight: 700 !important;
      color: var(--text) !important;
    }
    body:not(.bionic-mode) .lx8-bionic-word b {
      font-weight: inherit !important;
      color: inherit !important;
    }
  `;
  document.head.appendChild(style);

  // Apply CSS states immediately to minimize visual flash (FOUC)
  if (A11Y_STATE.dyslexic) document.body.classList.add('dyslexic-mode');
  if (A11Y_STATE.contrast) document.body.classList.add('high-contrast');
  if (A11Y_STATE.paused) document.body.classList.add('paused-animations');
  if (A11Y_STATE.bionic) document.body.classList.add('bionic-mode');

  // Bionic parser traversing only pure text nodes to secure HTML structure
  let bionicParsed = false;
  function parseBionicContent() {
    if (bionicParsed) return;
    const root = document.querySelector('main') || document.getElementById('main') || document.body;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      const parent = node.parentNode;
      if (!parent || ['SCRIPT', 'STYLE', 'BUTTON', 'A', 'NAV', 'CODE', 'PRE', 'CANVAS'].includes(parent.tagName)) return;
      if (parent.closest('nav') || parent.closest('.a11y-menu')) return;
      
      const words = node.nodeValue.split(/(\s+)/);
      const frag = document.createDocumentFragment();
      
      words.forEach(word => {
        if (word.trim().length === 0) {
          frag.appendChild(document.createTextNode(word));
        } else {
          const len = word.length;
          const boldLen = len <= 3 ? 1 : (len <= 6 ? 2 : Math.ceil(len * 0.45));
          const boldPart = word.substring(0, boldLen);
          const restPart = word.substring(boldLen);
          
          const span = document.createElement('span');
          span.className = 'lx8-bionic-word';
          span.style.cssText = 'display:inline;';
          
          const b = document.createElement('b');
          b.textContent = boldPart;
          
          span.appendChild(b);
          span.appendChild(document.createTextNode(restPart));
          frag.appendChild(span);
        }
      });
      parent.replaceChild(frag, node);
    });
    bionicParsed = true;
  }

  // Inject Atkinson Legibility font link asynchronously
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://fonts.bunny.net/css?family=atkinson-hyperlegible:400,700,400i,700i&display=swap';
  document.head.appendChild(link);

  // Initialize UI switcher on DOM ready
  document.addEventListener('DOMContentLoaded', () => {
    const nav = document.getElementById('nav');
    if (!nav) return;

    // Create A11y Button
    const btn = document.createElement('button');
    btn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>`;
    btn.setAttribute('aria-label', 'Accessibility Settings');
    btn.className = 'a11y-btn';
    btn.style.cssText = 'background:none; border:none; color:var(--text2); cursor:pointer; padding:6px; margin-left:auto; margin-right: 15px; border-radius: 6px; display:flex; align-items:center; transition: color 0.2s;';
    
    // Create Menu Panel
    const menu = document.createElement('div');
    menu.className = 'a11y-menu';
    menu.style.cssText = 'position:absolute; top:70px; right:20px; background:var(--bg); border:1px solid var(--border); padding:1.25rem; border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,0.6); display:none; flex-direction:column; gap:14px; z-index:9999; backdrop-filter:blur(20px); width: 240px;';

    // Create Focus Ruler
    const ruler = document.createElement('div');
    ruler.className = 'a11y-ruler';
    ruler.style.cssText = 'position:fixed; left:0; right:0; height:45px; pointer-events:none; z-index:9998; background:rgba(99,102,241,0.06); border-top:1px dashed rgba(99,102,241,0.3); border-bottom:1px dashed rgba(99,102,241,0.3); box-shadow:0 0 80px rgba(99,102,241,0.03); display:none; transform:translateY(-100px); transition: transform 0.05s ease-out;';
    document.body.appendChild(ruler);

    if (A11Y_STATE.ruler) {
      ruler.style.display = 'block';
    }

    document.addEventListener('mousemove', (e) => {
      if (A11Y_STATE.ruler) {
        ruler.style.transform = `translateY(${e.clientY - 22}px)`;
      }
    });

    // Parse Bionic instantly if stored active
    if (A11Y_STATE.bionic) {
      parseBionicContent();
    }

    const createToggle = (id, label, stateKey, className, callback) => {
      const wrapper = document.createElement('label');
      wrapper.style.cssText = 'display:flex; align-items:center; justify-content:space-between; gap:16px; font-size:0.82rem; cursor:pointer; color:var(--text2); font-weight: 500; transition: color 0.2s;';
      wrapper.innerHTML = `<span>${label}</span><input type="checkbox" id="${id}" ${A11Y_STATE[stateKey] ? 'checked' : ''} style="accent-color:var(--ind4);">`;
      
      const input = wrapper.querySelector('input');
      input.addEventListener('change', (e) => {
        const isChecked = e.target.checked;
        A11Y_STATE[stateKey] = isChecked;
        localStorage.setItem(`lx8-a11y-${stateKey}`, isChecked);
        if (className) document.body.classList.toggle(className, isChecked);
        if (callback) callback(isChecked);
      });
      return wrapper;
    };

    menu.appendChild(createToggle('a11y-t-dys', 'Dyslexia Friendly Font', 'dyslexic', 'dyslexic-mode'));
    menu.appendChild(createToggle('a11y-t-con', 'High Contrast Mode', 'contrast', 'high-contrast'));
    menu.appendChild(createToggle('a11y-t-pau', 'Pause Animations', 'paused', 'paused-animations'));
    
    // ADHD Bionic Eye Guider
    menu.appendChild(createToggle('a11y-t-bio', 'Bionic Focus Guide (ADHD)', 'bionic', 'bionic-mode', (active) => {
      if (active) {
        parseBionicContent();
      }
    }));

    // Focus Line Ruler
    menu.appendChild(createToggle('a11y-t-rul', 'Line Reading Ruler', 'ruler', null, (active) => {
      ruler.style.display = active ? 'block' : 'none';
    }));

    btn.addEventListener('click', () => {
      const isVisible = menu.style.display === 'flex';
      menu.style.display = isVisible ? 'none' : 'flex';
      btn.style.color = isVisible ? 'var(--text2)' : 'var(--text)';
    });

    document.addEventListener('click', (e) => {
      if (!btn.contains(e.target) && !menu.contains(e.target)) {
        menu.style.display = 'none';
        btn.style.color = 'var(--text2)';
      }
    });

    const backLink = nav.querySelector('.back-link');
    if (backLink) {
      nav.insertBefore(btn, backLink);
      nav.appendChild(menu);
    } else {
      nav.appendChild(btn);
      nav.appendChild(menu);
    }
  });
})();
