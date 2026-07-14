# Lx8 Labs Web Platform

[![Deploy Status](https://img.shields.io/badge/deploy-recovery-orange.svg)](https://lx8labs.com)
[![Architecture](https://img.shields.io/badge/architecture-static--html-blue.svg)]()

The official web platform and digital storefront for **Lx8 Labs**, encompassing the Tupã IDE ecosystem, the Bipartite Universe course architecture, and laboratory insights.

## Architecture & Stack

The public site is a static HTML/CSS/JavaScript surface. GitHub Pages is the credential-free recovery origin; Cloudflare Pages remains the intended production origin after account authorization and a verified cutover.

* **Frontend Engine:** Vanilla HTML5 / CSS3.
* **Design Language:** Tactile Brutalism, featuring progressive disclosure mechanisms (horizontal scroll-snap carousels) to minimize cognitive load.
* **CSS Architecture:** A unified, cache-optimized `global.css` governs base design tokens, responsive typography, and navigation states to ensure sub-second First Contentful Paint (FCP).
* **3D Visualizations:** WebGL integration via `three.js` (deferred loading) for the Bipartite Universe## Global Architecture

Lx8 Labs is built on a sovereign, cross-platform architecture:
1. **Central OS Dashboard:** React/Vite unified control plane.
2. **Omni-Channel Licensing:** 
   - **Web Apps (Bipartite Book):** Firebase Auth Custom Claims.
   - **Native/CLI (Tupã IDE, aimem):** Offline-first ECDSA cryptographically signed tokens.
   - **Hardware (mattermem):** Zero-touch device pairing.
3. **Telemetry Engine:** React ErrorBoundary mapped to Firebase Analytics (Web Crashlytics equivalent).
4. **SRE Deploy Engine:** A custom Python orchestrator (`scripts/deploy.py`) that performs local hashing and live cloud verification to achieve zero-cost idempotency.
5. **Support Agent:** AI Triage Agent running on Firebase Functions, listening to the `/support` queue.

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

Lx8 Labs utilizes an intelligent, zero-cost CI/CD SRE pipeline powered by GitHub Actions and a centralized Python deployment engine.

1. **Product Registry**: Maintain the product subdomains and version tracks in `lx8_registry.yaml`.
2. **Controlled deployment**: GitHub Pages publishes the static source without Jekyll. Cloudflare and Firebase workflows are manual until credentials and the canonical provider are approved.
3. **Smart Deploy Engine (`scripts/deploy.py`)**:
   - Analyzes codebase hashes to identify which subdomains have modified files.
   - Automatically bumps Semantic Versions and generates a `version.json` payload for auditing.
   - Rebuilds and synchronizes all global telemetry, React dashboards, and translations.
   - Deploys **only** dirty targets to Firebase via targeted CLI commands.
   - Implements aggressive zero-cost caching (1-year `max-age` for static assets, and `no-cache` ETags for immediate HTML revalidation).

To manually force a global deploy locally:
```bash
python3 scripts/deploy.py --force
```

Validate the public surface before deployment:

```bash
python3 scripts/verify_public_site.py
```

## Local Development

The platform requires minimal local setup.

1. Clone the repository and navigate to the root directory.
2. Serve the static files locally:
   ```bash
   python3 -m http.server 8000
   ```
3. To test the dashboard locally, navigate to `dashboard/` and run `npm run dev`.

## Intellectual Property & Licensing

The core repositories, native source files (Rust, Swift, Metal), and raw manuscripts within the `~/Lx8Labs/` taxonomy are **strictly proprietary and confidential intellectual property of Lx8 Labs**. The public website and SRE deployment scripts are licensed strictly under their respective headers; no proprietary algorithms or product core models are exposed.

---
*© 2026 Lx8 Labs. All rights reserved.*
