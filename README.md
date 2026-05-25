# Lx8 Labs Web Platform

[![Deploy](https://github.com/LX8/lx8-website/actions/workflows/deploy.yml/badge.svg)](https://github.com/LX8/lx8-website/actions/workflows/deploy.yml)
[![QA](https://github.com/LX8/lx8-website/actions/workflows/qa.yml/badge.svg)](https://github.com/LX8/lx8-website/actions/workflows/qa.yml)

The official web platform and digital storefront for **Lx8 Labs** — the Tupã
IDE ecosystem, the Bipartite Universe course architecture, the aimem
context server, and laboratory insights.

## Architecture & Stack

Strict zero-build-step authoring policy at the root: raw performance, minimal
dependencies, semantic HTML/CSS over JavaScript frameworks. The control-plane
dashboard (`dashboard/`) is the one exception — it builds with Vite into
static assets that get copied into each subdomain.

- **Frontend Engine** — Vanilla HTML5 / CSS3 at the root.
- **Design Language** — Tactile Brutalism, with horizontal scroll-snap
  carousels for progressive disclosure.
- **CSS Architecture** — Unified `global.css` for design tokens, responsive
  typography, and nav states. Targets sub-second First Contentful Paint.
- **3D Visualisations** — `three.js`, deferred-loaded, for the Algorithm Lab
  and Bipartite Universe scenes.
- **Hosting** — Firebase Hosting (multi-site), one target per subdomain.
- **Backend** — Firebase Auth + Firestore + Cloud Functions (Node 20)
  for Stripe checkout, license provisioning, and the support triage agent.

## Global Architecture

Lx8 Labs is built on a sovereign, cross-platform architecture:

1. **Central OS Dashboard** — React/Vite unified control plane (`dashboard/`).
2. **Omni-Channel Licensing**
   - Web apps (Bipartite Book): Firebase Auth custom claims.
   - Native / CLI (Tupã IDE, aimem): offline-first ECDSA-signed tokens.
   - Hardware (mattermem): zero-touch device pairing.
3. **Telemetry** — Firebase Performance Monitoring; the prior open-write
   Firestore rule has been replaced with an authed, schema-validated rule.
4. **SRE Deploy** — A Python orchestrator (`scripts/deploy.py`) does hash
   diffing, semver bumps, and per-target Firebase deploys.
5. **Support Agent** — Cloud Function on the `/support` queue.

## Project Structure

```text
├── index.html             # Landing & core navigation
├── algorithms/            # Algorithm Lab (3D visualiser)
├── tupa/                  # tupa.lx8labs.com mirror (managed via Firebase target)
├── aimem/                 # aimem.lx8labs.com mirror
├── bipartitebook/         # bipartitebook.lx8labs.com — Next.js export
├── installations/         # installations.lx8labs.com
├── mattermem/             # mattermem.lx8labs.com
├── about/ courses/ shop/ ... # Authored static pages
├── dashboard/             # React/Vite control plane (builds to dashboard/dist)
├── functions/             # Cloud Functions (Stripe, licensing, triage)
├── i18n/                  # Centralized translations + runtime engine
├── scripts/               # SRE automation
│   ├── deploy.py
│   ├── sync_infrastructure.py   # Single source of truth for firebase.json
│   ├── dns_*.py
│   └── legacy/                  # Archived one-off patcher scripts
├── global.css             # Design tokens & shared styles
├── firebase-init.js       # Firebase Auth/DB/Telemetry bootstrap
├── firebase.json          # Generated from sync_infrastructure.py
└── ARCHITECTURE.md        # Full systems design
```

## SRE & Infrastructure

Pushes to `main` trigger:

1. **QA** (`.github/workflows/qa.yml`) — html-validate over authored pages,
   internal-link check via lychee, Lighthouse against the homepage and the
   three flagship sections.
2. **Deploy** (`.github/workflows/deploy.yml`) — Firebase Hosting deploy of
   the live channel. Requires repo secret
   `FIREBASE_SERVICE_ACCOUNT_LX8_LABS_WEBSITE` (a Firebase service-account
   JSON). Without that secret, the deploy job is skipped (with a CI notice)
   so QA still gates merges.

To regenerate the Firebase config from the registry:

```bash
python3 scripts/sync_infrastructure.py
```

To force a global deploy locally:

```bash
python3 scripts/deploy.py --force
```

## Local Development

```bash
# Static root
python3 -m http.server 8000

# Dashboard (in another terminal)
cd dashboard && npm install && npm run dev
```

## Subdomain Health & TLS

A scheduled GitHub Action (`.github/workflows/subdomain-health.yml`) probes
every hosting target every 6 hours. The same probe can be run locally:

```bash
pip install pyyaml certifi
python3 scripts/verify_subdomains.py --include-apex
```

Subdomain pages are generated from `lx8_registry.yaml`:

```bash
python3 scripts/build_placeholders.py            # render any stubs
python3 scripts/build_placeholders.py --force    # refresh generated pages
                                                 # (hand-written pages are
                                                 # protected by a sentinel
                                                 # marker and never touched)
```

### Custom-domain status (manual binding required in Firebase Console)

Five subdomains have their DNS pointed at Firebase but no TLS cert minted yet.
Bind each custom domain to its site at
<https://console.firebase.google.com/project/lx8-labs-website/hosting/sites>
and Firebase will issue a Let's Encrypt cert within 24–48h.

| Custom domain                 | Bind to Firebase site | Current state             |
| ----------------------------- | --------------------- | ------------------------- |
| `aimem.lx8labs.com`           | `lx8-aimem`           | TLS hostname mismatch     |
| `tupa.lx8labs.com`            | `lx8-tupa`            | TLS hostname mismatch     |
| `tupaide.lx8labs.com`         | `lx8-tupa-ide`        | TLS hostname mismatch     |
| `mattermem.lx8labs.com`       | `lx8-mattermem`       | TLS hostname mismatch     |
| `suit.lx8labs.com`            | `lx8-bmss`            | TLS hostname mismatch     |
| `bipartitebook.lx8labs.com`   | `bipartitebook`       | 404 — domain not linked   |
| `installations.lx8labs.com`   | `lx8-installations`   | 404 — domain not linked   |

Every native Firebase URL (`https://<site-id>.web.app/`) is reachable and
serves content; the gap is purely at the custom-domain layer.

## Security model

- **Cloud Functions** authenticate every mutating endpoint with a Firebase
  ID token from the `Authorization: Bearer …` header. The UID is taken from
  the verified token, never from the request body.
- **License keys** use `crypto.randomBytes` (CSPRNG), not `Math.random`.
- **Firestore telemetry** writes require auth and a strict shape (≤128-char
  `event`, ≤8 kB payload, `uid` must match `request.auth.uid`).
- **Content-Security-Policy** is set at the Hosting layer in `firebase.json`
  (regenerated by `sync_infrastructure.py`); pages no longer ship a
  conflicting inline `<meta>` CSP.

## Intellectual Property & Licensing

The core repositories, native source files (Rust, Swift, Metal), and raw
manuscripts within the `~/Lx8Labs/` taxonomy are **strictly proprietary and
confidential intellectual property of Lx8 Labs**. The public website and SRE
deployment scripts are licensed strictly under their respective headers; no
proprietary algorithms or product core models are exposed.

---
*© 2026 Lx8 Labs. All rights reserved.*
