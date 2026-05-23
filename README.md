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

## Project Structure & Architecture

The website codebase operates as the central control plane inside the larger `~/Lx8Labs/` workspace. For a comprehensive overview of systems design, SRE sync pipelines, and the multi-language (i18n) framework, see [ARCHITECTURE.md](file:///Users/alexeiferreira/Lx8Labs/internal/Website/ARCHITECTURE.md).

```text
├── index.html            # Main Landing & Core Navigation
├── aimem/                # Subdomain public folder: aimem.lx8labs.com
├── tupa/                 # Subdomain public folder: tupa.lx8labs.com
├── bsms/                 # Subdomain public folder: bsms.lx8labs.com
├── bipartitebook/        # Subdomain public folder: bipartitebook.lx8labs.com
├── installations/        # Subdomain public folder: installations.lx8labs.com
├── mattermem/            # Subdomain public folder: mattermem.lx8labs.com
├── i18n/                 # Centralized multi-language translations and engine
├── scripts/              # SRE infrastructure & automated sync scripts
├── global.css            # Centralized Design Tokens & CSS Engine
├── firebase-init.js      # Consolidated Firebase Auth, DB, & Telemetry
├── firebase.json         # Orchestrated Firebase Hosting config
└── ARCHITECTURE.md       # Master system design specifications
```

## SRE & Infrastructure Synchronization

We use an automated pipeline to sync subdomains, configure CDN caching headers, and replicate translation/telemetry assets recursively across all site targets:

1. Maintain the product registry in `lx8_registry.yaml`.
2. Sync the configurations and folders locally:
   ```bash
   python3 scripts/sync_infrastructure.py
   ```
3. Deploy to production:
   ```bash
   firebase deploy
   ```

## Local Development

The platform requires no local build steps (e.g., no Node.js/NPM builds required for UI compilation).

1. Clone the repository and navigate to the root directory.
2. Serve the static files locally:
   ```bash
   python3 -m http.server 8000
   ```
3. Access the site via `http://localhost:8000`.

## Intellectual Property & Licensing

The core repositories, native source files (Rust, Swift, Metal), and raw manuscripts within the `~/Lx8Labs/` taxonomy are **strictly proprietary and confidential intellectual property of Lx8 Labs**. The public website and SRE deployment scripts are licensed strictly under their respective headers; no proprietary algorithms or product core models are exposed.

---
*© 2026 Lx8 Labs. All rights reserved.*
