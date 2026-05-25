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

## Where the domain actually serves from

The serving topology is **split** and easy to get wrong:

| Surface                           | Served by         | TLS / headers                  |
| --------------------------------- | ----------------- | ------------------------------ |
| `lx8labs.com` (apex)              | GitHub Pages      | Cloudflare in front, no CSP    |
| `lx8labs.com/*` (root sections)   | GitHub Pages      | same — meta CSP is the policy  |
| `*.lx8labs.com` (subdomains)      | Firebase Hosting  | full firebase.json header set  |
| `lx8-*.web.app` (native fallback) | Firebase Hosting  | full firebase.json header set  |

GitHub Pages can't set response headers, so the apex relies entirely on
the inline `<meta http-equiv="Content-Security-Policy">` written into
every authored page. `scripts/sync_csp.py` keeps that meta tag in
lock-step with the CSP that firebase.json emits for the subdomains —
single source of truth, two enforcement layers.

## SRE & Infrastructure

Pushes to `main` trigger:

1. **QA** (`.github/workflows/qa.yml`) — runs six gates:
   - `html-validate` over authored pages
   - lychee internal-link check
   - Lighthouse against homepage + three flagship sections
   - `sitemap.xml` drift (regenerated from filesystem)
   - subdomain placeholder stub check
   - CSP drift between firebase.json and inline `<meta>` tags
2. **Deploy** (`.github/workflows/deploy.yml`) — `firebase deploy --only
   hosting,functions,firestore:rules`. Requires repo secret
   `FIREBASE_SERVICE_ACCOUNT_LX8_LABS_WEBSITE` (a Firebase service-account
   JSON). Without that secret, every step is skipped with a CI notice
   so QA still gates merges. Pass a custom `only` value via
   `workflow_dispatch` to deploy a single surface (e.g. `functions`).

   **Cloud Function secrets** are bound at runtime via Firebase Functions
   v2 `defineSecret()` (see `functions/index.js`). Provision them once via
   the Firebase CLI before the first deploy of `functions`:

   ```bash
   firebase functions:secrets:set STRIPE_SECRET_KEY        # sk_live_… (or sk_test_…)
   firebase functions:secrets:set STRIPE_WEBHOOK_SECRET    # whsec_…
   firebase functions:secrets:set LICENSE_PRIVATE_KEY      # PEM contents of enterprise_private.pem
   firebase functions:secrets:set PRICE_TUPA               # price_… for Tupã IDE
   firebase functions:secrets:set PRICE_BIPARTITE_BOOK     # price_… for Bipartite Universe Book
   firebase functions:secrets:set PRICE_AIMEM              # price_… for aimem
   ```

   These have no `"sk_test_dummy"`-style fallbacks anymore — a missing
   secret fails the function at cold start, surfacing the
   misconfiguration immediately rather than letting placeholder values
   reach production.
3. **Subdomain health** (`.github/workflows/subdomain-health.yml`) — every
   6 h, probes both the custom-domain and native-URL of every target and
   audits the response headers (CSP / HSTS / X-Frame-Options / X-Content-
   Type-Options). Surfaces drift as warnings without failing the workflow.

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

# Run every CI gate locally (mirrors qa.yml exactly)
bash scripts/qa-local.sh
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
- **CORS** on every HTTP function is an explicit allowlist of `lx8labs.com`
  + the seven `*.lx8labs.com` subdomains + the two native Firebase URLs.
  No `cors: true`. Other origins get a CORS rejection at the platform
  layer.
- **License keys** use `crypto.randomBytes` (CSPRNG), not `Math.random`.
- **Stripe webhook idempotency** is enforced both ways: a Firestore
  transaction writes `stripe_events/{event.id}` *before* any handler
  runs, so a redelivery from Stripe (default policy retries up to 3 days)
  is a guaranteed no-op. `checkout.sessions.create` also passes
  `{ idempotencyKey: sha256(uid|productId|day) }` so a user double-click
  doesn't open two parallel checkouts.
- **Refund handling**: `charge.refunded` flips the matching license to
  `active: false, refundedAt: …`. `generateOfflineLicense` refuses to mint
  a fresh signed token for a refunded license.
- **Error surface**: every catch funnels through a `respondError` helper
  that logs the internal error with a request id and returns only a
  generic public message. We no longer leak Stripe internals or
  "Enterprise Private Key not configured" to clients.
- **Firestore telemetry** writes require auth and a strict shape (≤128-char
  `event`, ≤8 kB payload, `uid` must match `request.auth.uid`).
- **Content-Security-Policy** has one canonical value living in
  `firebase.json` (target `main`). Firebase Hosting applies it as a response
  header for the subdomains; `scripts/sync_csp.py` mirrors the same value
  into a `<meta>` tag on every authored page (the apex is on GitHub Pages,
  which can't set response headers). CI gate `csp-drift` blocks merges
  where the two diverge.

## Intellectual Property & Licensing

The core repositories, native source files (Rust, Swift, Metal), and raw
manuscripts within the `~/Lx8Labs/` taxonomy are **strictly proprietary and
confidential intellectual property of Lx8 Labs**. The public website and SRE
deployment scripts are licensed strictly under their respective headers; no
proprietary algorithms or product core models are exposed.

---
*© 2026 Lx8 Labs. All rights reserved.*
