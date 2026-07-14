(function() {
  const DEFAULT_LANG = 'en';

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  function setCookie(name, value) {
    const domain = window.location.hostname.includes('lx8labs.com') ? '.lx8labs.com' : window.location.hostname;
    document.cookie = `${name}=${value};path=/;domain=${domain};max-age=31536000;SameSite=Lax`;
  }

  let currentLang = getCookie('lx8-lang') || localStorage.getItem('lx8-lang') || DEFAULT_LANG;

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
      const active = btn.getAttribute('data-lang') === lang;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-pressed', String(active));
    });

    window.dispatchEvent(new CustomEvent('lx8:languagechange', { detail: { lang } }));
  }

  window.lx8SetLanguage = function(lang) {
    if (!window.lx8Translations[lang]) return;
    currentLang = lang;
    localStorage.setItem('lx8-lang', lang);
    setCookie('lx8-lang', lang);
    updateDOM(lang);
  };

  // Run on DOM loaded
  document.addEventListener('DOMContentLoaded', () => {
    updateDOM(currentLang);
    
    // Inject lang switcher UI next to a11y btn
    const nav = document.getElementById('nav');
    if (nav) {
      const switcher = document.createElement('div');
      switcher.className = 'lang-switcher';
      
      const langs = [
        { id: 'en', label: 'EN', name: 'English' },
        { id: 'pt-BR', label: 'PT', name: 'Português' },
        { id: 'de', label: 'DE', name: 'Deutsch' }
      ];
      
      langs.forEach((l, i) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'lang-btn';
        btn.setAttribute('data-lang', l.id);
        btn.setAttribute('aria-label', l.name);
        btn.setAttribute('aria-pressed', String(l.id === currentLang));
        btn.textContent = l.label;
        if (l.id === currentLang) btn.classList.add('active');
        btn.onclick = () => window.lx8SetLanguage(l.id);
        switcher.appendChild(btn);
        
        if (i < langs.length - 1) {
          const sep = document.createElement('span');
          sep.textContent = '|';
          sep.setAttribute('aria-hidden', 'true');
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
