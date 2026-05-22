# Lx8 Labs Web Platform

[![Deploy Status](https://img.shields.io/badge/deploy-active-success.svg)](https://lx8labs.com)
[![Architecture](https://img.shields.io/badge/architecture-static--html-blue.svg)]()
[![Performance](https://img.shields.io/badge/lighthouse-100-brightgreen.svg)]()

The official web platform and digital storefront for **Lx8 Labs**, encompassing the Tupã IDE ecosystem, the Bipartite Universe course architecture, and laboratory insights.

## Architecture & Stack

The platform is designed with a strict zero-build-step philosophy, prioritizing raw performance, minimal dependencies, and semantic HTML/CSS over heavy JavaScript frameworks.

* **Frontend Engine:** Vanilla HTML5 / CSS3.
* **Design Language:** Tactile Brutalism, featuring progressive disclosure mechanisms (horizontal scroll-snap carousels) to minimize cognitive load.
* **CSS Architecture:** A unified, cache-optimized `global.css` governs base design tokens, responsive typography, and navigation states to ensure sub-second First Contentful Paint (FCP).
* **3D Visualizations:** WebGL integration via `three.js` (deferred loading) for the Bipartite Universe interactive physics engine.
* **Machine Experience (MX):** Extensive `application/ld+json` schema implementations for seamless product ingestion by LLMs and search engines.
* **Authentication & Backend:** (In Progress) Firebase Authentication and Cloud Firestore for subscription management and course gating.

## Project Structure

```text
├── index.html            # Landing & Core Navigation
├── tupa.html             # Tupã IDE Product Overview
├── shop.html             # Storefront (Subscriptions & Merchandise)
├── theory.html           # Interactive 3D Physics Engine (WebGL)
├── aimem.html            # AI-Memory Protocol Documentation
├── global.css            # Centralized Design Tokens
├── og-image.png          # Rasterized OpenGraph Preview
└── .gitignore            # Excluded artifacts (certificates, logs)
```

## Local Development

The platform requires no local build steps (e.g., no Node.js/NPM builds required for UI compilation).

1. Clone the repository and navigate to the root directory.
2. Serve the static files locally:
   ```bash
   python3 -m http.server 8000
   ```
3. Access the site via `http://localhost:8000`.

### Secure Tunneling (Auth Workflows)
Modern browsers (like Firefox) strictly enforce HTTPS for WebCrypto and Authentication callbacks. If you are developing Firebase Auth flows locally, establish an encrypted reverse tunnel:
```bash
ssh -R 80:localhost:8000 nokey@localhost.run
```

## Production Guidelines

* **Asset Optimization:** All OpenGraph and social preview images must be rasterized (`.png`, `.jpg`, `.webp`); SVG previews are strictly unsupported by the OpenGraph standard.
* **Performance Budget:** Ensure all external scripts (e.g., `three.min.js`) utilize the `defer` attribute to prevent blocking the HTML parser.
* **Accessibility (a11y):** All structural elements must maintain strict WCAG compliance (e.g., explicit `type="button"`, unique ARIA landmarks).

---
*© 2026 Lx8 Labs. All rights reserved.*
