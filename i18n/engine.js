(function() {
  const DEFAULT_LANG = 'en';
  let currentLang = localStorage.getItem('lx8-lang') || DEFAULT_LANG;

  function updateDOM(lang) {
    document.documentElement.lang = lang;
    const dict = window.lx8Translations[lang] || window.lx8Translations[DEFAULT_LANG];
    
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });
    
    document.querySelectorAll('.lang-btn').forEach(btn => {
      if (btn.getAttribute('data-lang') === lang) {
        btn.classList.add('active');
        btn.style.color = 'var(--text)';
        btn.style.fontWeight = 'bold';
      } else {
        btn.classList.remove('active');
        btn.style.color = 'var(--text2)';
        btn.style.fontWeight = 'normal';
      }
    });
  }

  window.lx8SetLanguage = function(lang) {
    if (!window.lx8Translations[lang]) return;
    currentLang = lang;
    localStorage.setItem('lx8-lang', lang);
    updateDOM(lang);
  };

  // Run on DOM loaded
  document.addEventListener('DOMContentLoaded', () => {
    updateDOM(currentLang);
    
    // Inject lang switcher UI next to a11y btn
    const nav = document.getElementById('nav');
    if (nav) {
      const switcher = document.createElement('div');
      switcher.style.cssText = 'display:flex; gap:8px; margin-left:15px; font-size:0.8rem; border-left: 1px solid var(--border); padding-left: 15px; align-items:center;';
      
      const langs = [
        { id: 'en', label: 'EN' },
        { id: 'pt-BR', label: 'PT' },
        { id: 'de', label: 'DE' }
      ];
      
      langs.forEach((l, i) => {
        const btn = document.createElement('button');
        btn.className = 'lang-btn';
        btn.setAttribute('data-lang', l.id);
        btn.textContent = l.label;
        btn.style.cssText = 'background:none; border:none; cursor:pointer; color:var(--text2); transition: color 0.2s;';
        if (l.id === currentLang) {
          btn.style.color = 'var(--text)';
          btn.style.fontWeight = 'bold';
        }
        btn.onclick = () => window.lx8SetLanguage(l.id);
        switcher.appendChild(btn);
        
        if (i < langs.length - 1) {
          const sep = document.createElement('span');
          sep.textContent = '|';
          sep.style.color = 'var(--border)';
          switcher.appendChild(sep);
        }
      });
      
      const a11yBtn = document.querySelector('.a11y-btn');
      if (a11yBtn && a11yBtn.nextSibling) {
        // Insert right after a11y btn (but before back link)
        nav.insertBefore(switcher, a11yBtn.nextSibling);
      } else {
        nav.appendChild(switcher);
      }
    }
  });
})();
