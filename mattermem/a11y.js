// Accessibility (A11y) Engine
// Handles Paused Animations, Dyslexia Font Mode, and High Contrast.

(function() {
  const A11Y_STATE = {
    dyslexic: localStorage.getItem('lx8-a11y-dyslexic') === 'true',
    contrast: localStorage.getItem('lx8-a11y-contrast') === 'true',
    paused: localStorage.getItem('lx8-a11y-paused') === 'true'
  };

  // Apply immediately to prevent flash
  if (A11Y_STATE.dyslexic) document.body.classList.add('dyslexic-mode');
  if (A11Y_STATE.contrast) document.body.classList.add('high-contrast');
  if (A11Y_STATE.paused) document.body.classList.add('paused-animations');

  // Inject UI once DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    const nav = document.getElementById('nav');
    if (!nav) return;

    // Create A11y Button
    const btn = document.createElement('button');
    btn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>`;
    btn.setAttribute('aria-label', 'Accessibility Settings');
    btn.className = 'a11y-btn';
    btn.style.cssText = 'background:none; border:none; color:var(--text2); cursor:pointer; padding:6px; margin-left:auto; margin-right: 15px; border-radius: 6px; display:flex; align-items:center; transition: color 0.2s;';
    
    // Create Menu
    const menu = document.createElement('div');
    menu.className = 'a11y-menu';
    menu.style.cssText = 'position:absolute; top:70px; right:20px; background:var(--bg); border:1px solid var(--border); padding:1rem; border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,0.5); display:none; flex-direction:column; gap:12px; z-index:999;';

    const createToggle = (id, label, stateKey, className) => {
      const wrapper = document.createElement('label');
      wrapper.style.cssText = 'display:flex; align-items:center; justify-content:space-between; gap:20px; font-size:0.85rem; cursor:pointer; color:var(--text);';
      wrapper.innerHTML = `<span>${label}</span><input type="checkbox" id="${id}" ${A11Y_STATE[stateKey] ? 'checked' : ''}>`;
      
      const input = wrapper.querySelector('input');
      input.addEventListener('change', (e) => {
        const isChecked = e.target.checked;
        A11Y_STATE[stateKey] = isChecked;
        localStorage.setItem(`lx8-a11y-${stateKey}`, isChecked);
        document.body.classList.toggle(className, isChecked);
      });
      return wrapper;
    };

    menu.appendChild(createToggle('a11y-t-dys', 'Dyslexia Friendly Font', 'dyslexic', 'dyslexic-mode'));
    menu.appendChild(createToggle('a11y-t-con', 'High Contrast Mode', 'contrast', 'high-contrast'));
    menu.appendChild(createToggle('a11y-t-pau', 'Pause Animations', 'paused', 'paused-animations'));

    btn.addEventListener('click', () => {
      const isVisible = menu.style.display === 'flex';
      menu.style.display = isVisible ? 'none' : 'flex';
      btn.style.color = isVisible ? 'var(--text2)' : 'var(--text)';
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!btn.contains(e.target) && !menu.contains(e.target)) {
        menu.style.display = 'none';
        btn.style.color = 'var(--text2)';
      }
    });

    // Insert into nav
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
