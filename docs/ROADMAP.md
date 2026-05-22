# Lx8 Website Roadmap

## Deferred Items (UI & Animations)

### 1. Chronological Timeline of Algorithms (SVG)
- **File Paths:** `algorithms/index.html` (or possibly a new section in `products/index.html`).
- **State Shape:** Needs to extract the 39 algorithms from `INFO` in `algorithms/index.html` and render an SVG timeline or orbit similar to the products constellation.
- **IPC Surface:** N/A (Static HTML/JS SVG generation).
- **Rough Budget:** ~1.5 h to design the SVG layout, plot the timeline nodes chronologically, and wire hover states to load the respective algorithms.
- **Failure Mode:** Trying to hand-code 39 SVG nodes manually in HTML would clutter the file and break responsiveness. Should be generated dynamically via JS on load.

### 2. Space Elements Animation (Comets, Aliens, Astronomers)
- **File Paths:** `products/index.html` (inside `.orbit-svg`).
- **State Shape:** SVG `<path>` and `<g>` elements animated via CSS `@keyframes` or `<animateMotion>`.
- **IPC Surface:** N/A (CSS/SVG Animation).
- **Rough Budget:** ~2 h to properly design glowing comets (`stroke-dasharray` animations) and micro-illustrations (emojis or SVGs) of aliens 👽 and astronomers 🔭 orbiting or traversing the canvas without making it look chaotic.
- **Failure Mode:** Dropping static emojis across the screen looks unpolished; needs carefully tuned SVG paths and easing curves to match the premium dark-mode aesthetic.
