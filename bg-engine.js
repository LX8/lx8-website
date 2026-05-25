// High-Performance Zero-Cost Canvas Engine
// Replaces heavy CSS filter: blur() blobs with an optimized, 60fps aesthetic field.
//
// Deferral strategy:
//   The 180-particle canvas + 60fps requestAnimationFrame loop is purely
//   decorative — never required for first contentful paint, first input,
//   or any text content. Starting it inside requestIdleCallback frees up
//   the main thread during initial parse/render, which lowers TBT on
//   weak devices. We fall back to setTimeout(0) on browsers without
//   requestIdleCallback (Safari before 17).

function _initBackgroundEngine() {
  const canvas = document.createElement('canvas');
  canvas.id = 'bg-canvas';
  canvas.style.position = 'fixed';
  canvas.style.inset = '0';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.zIndex = '0';
  canvas.style.pointerEvents = 'none';
  canvas.style.background = '#000000';
  canvas.style.opacity = '0.9';
  
  // Insert before the old #bg div or at the top of body
  document.body.prepend(canvas);

  const ctx = canvas.getContext('2d', { alpha: false });
  let w = canvas.width = window.innerWidth;
  let h = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  });

  const particles = [];
  const pCount = 180; // Optimized count

  for (let i = 0; i < pCount; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.2,
      a: Math.random() * 0.5 + 0.1,
      // Create a cinematic color palette matching Lx8 brand (indigo, blue, cyan)
      c: Math.random() > 0.5 ? 'rgba(99, 102, 241, ' : 'rgba(59, 130, 246, '
    });
  }

  function draw() {
    // Clear with a faint trail effect
    ctx.fillStyle = 'rgba(0, 0, 5, 0.2)';
    ctx.fillRect(0, 0, w, h);

    // Subtle gradient mesh effect overlay
    const g = ctx.createRadialGradient(w/2, h/2, 0, w/2, h/2, w);
    g.addColorStop(0, 'rgba(10, 10, 30, 0.0)');
    g.addColorStop(1, 'rgba(0, 0, 0, 0.9)');
    
    for (let i = 0; i < pCount; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = w;
      if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h;
      if (p.y > h) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.c + p.a + ')';
      ctx.fill();
    }
    
    // Draw vignette overlay
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    requestAnimationFrame(draw);
  }

  // Start engine if reduced motion is not forced
  const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (!mql.matches) {
    requestAnimationFrame(draw);
  } else {
    // Static fallback
    ctx.fillStyle = '#05050a';
    ctx.fillRect(0, 0, w, h);
  }
}

if (typeof requestIdleCallback === 'function') {
  requestIdleCallback(_initBackgroundEngine, { timeout: 1500 });
} else {
  // Safari ≤ 16 has no requestIdleCallback; setTimeout 0 still defers past
  // first paint, which is the property we actually care about.
  setTimeout(_initBackgroundEngine, 0);
}
