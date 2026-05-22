# Lx8 Labs Website

This repository contains the source code for [lx8labs.com](https://lx8labs.com), the central hub for the Bipartite Universe course, Tupã IDE, and other Lx8 creations.

## Architecture

* **Frontend:** Extremely fast, static HTML/CSS built around the "Tactile Brutalism" aesthetic.
* **Layout:** Custom CSS Grid/Flexbox layouts featuring **Progressive Disclosure** (horizontal scroll-snap carousels) for dense content like Projects and Insights.
* **CSS Architecture:** A unified `global.css` file contains all base tokens, animations, nav, and footer styles to ensure sub-second First Contentful Paint (FCP) and cross-page cacheability.
* **Backend:** Future integration with Firebase Authentication & Firestore (Phase 3 in progress).

## Recent Optimizations (May 2026)

* **Performance:** Extracted all inline `<style>` blocks into `global.css`. Added `defer` attributes to massive 3D WebGL scripts (`three.min.js`, `OrbitControls.js`) to unblock the HTML parser and drastically improve FCP. Fixed Cumulative Layout Shift (CLS) on dynamic avatars by enforcing strict aspect ratios.
* **SEO (Machine Experience):** 
  * Rasterized SVG OpenGraph images (`og-image.svg` -> `og-image.png`) to ensure social link previews render perfectly across iMessage, LinkedIn, and Twitter.
  * Injected `application/ld+json` Product schemas into `shop.html` and `theory.html` to inform AI search engines about the new $19/mo Bipartite Universe subscription.
* **Accessibility (A11y):** Fixed dozens of implicit form submissions by enforcing `type="button"` across all structural components globally.
* **Content Alignment:** Synced `tupa.html` roadmap with real-world `LX8/tupan-ide` progress (Command Palette, Settings full page, LSP Diagnostics).

## Development

To serve the site locally:
```bash
python3 -m http.server 8000
```

*Note: Since Firefox strictly enforces HTTPS-Only Mode for WebCrypto/Auth flows, local development may require tunneling via `ssh -R 80:localhost:8000 nokey@localhost.run`.*
