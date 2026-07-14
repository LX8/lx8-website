(() => {
  const header = document.getElementById('site-header');
  const menuButton = document.getElementById('menu-button');
  const mobileNav = document.getElementById('mobile-nav');
  const year = document.getElementById('current-year');

  const menuLabels = {
    en: { open: 'Open navigation', close: 'Close navigation' },
    'pt-BR': { open: 'Abrir navegação', close: 'Fechar navegação' },
    de: { open: 'Navigation öffnen', close: 'Navigation schließen' }
  };

  function setMenu(open) {
    menuButton?.setAttribute('aria-expanded', String(open));
    const labels = menuLabels[document.documentElement.lang] || menuLabels.en;
    menuButton?.setAttribute('aria-label', open ? labels.close : labels.open);
    if (mobileNav) mobileNav.hidden = !open;
  }

  menuButton?.addEventListener('click', () => {
    setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
  });

  mobileNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setMenu(false));
  });

  window.addEventListener('scroll', () => {
    header?.classList.toggle('scrolled', window.scrollY > 12);
  }, { passive: true });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 1020) setMenu(false);
  });

  window.addEventListener('lx8:languagechange', () => setMenu(false));

  setMenu(false);
  if (year) year.textContent = String(new Date().getFullYear());
})();
