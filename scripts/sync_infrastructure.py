#!/usr/bin/env python3
"""
Regenerate firebase.json and .firebaserc from lx8_registry.yaml.

This is the single source of truth for hosting target configuration. Each
target (main + one per subdomain in the registry) gets identical caching
and security headers — when those need to change, edit `HEADERS_BLOCK`
below and re-run, rather than hand-editing the 8 duplicated blocks in
firebase.json.

Usage:
    python3 scripts/sync_infrastructure.py
"""

import json
import os
import shutil

import yaml

REGISTRY_FILE      = "lx8_registry.yaml"
FIREBASE_JSON_FILE = "firebase.json"
FIREBASERC_FILE    = ".firebaserc"
PROJECT_ID         = "lx8-labs-website"

# ── Shared header policy ────────────────────────────────────────────────
# A single canonical Content-Security-Policy that covers everything the
# Lx8 site loads at runtime (Firebase Auth, Stripe, Bunny fonts, GitHub
# avatars). Previously a stricter server-side CSP intersected with a
# more-permissive <meta> CSP inside index.html — the intersection silently
# blocked bunny.net fonts and a few image origins.
CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://apis.google.com https://js.stripe.com https://www.gstatic.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.bunny.net https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.bunny.net https://fonts.gstatic.com; "
    "img-src 'self' data: https://avatars.githubusercontent.com https://*.googleusercontent.com; "
    "connect-src 'self' https://*.googleapis.com https://*.cloudfunctions.net "
    "https://identitytoolkit.googleapis.com https://securetoken.googleapis.com wss://*.firebaseio.com; "
    "frame-src 'self' https://js.stripe.com https://lx8-labs-website.firebaseapp.com; "
    "base-uri 'self'; "
    "form-action 'self' https://checkout.stripe.com; "
    "frame-ancestors 'none';"
)

SECURITY_HEADERS = [
    {"key": "X-Frame-Options",             "value": "DENY"},
    {"key": "X-Content-Type-Options",      "value": "nosniff"},
    {"key": "Strict-Transport-Security",   "value": "max-age=31536000; includeSubDomains; preload"},
    {"key": "Referrer-Policy",             "value": "strict-origin-when-cross-origin"},
    {"key": "Permissions-Policy",          "value": "geolocation=(), microphone=(), camera=(), interest-cohort=()"},
    {"key": "Content-Security-Policy",     "value": CSP},
]

HEADERS_BLOCK = [
    {
        "source": "**/*.@(js|css|png|jpg|jpeg|gif|svg|woff|woff2)",
        "headers": [{"key": "Cache-Control", "value": "max-age=31536000, immutable"}],
    },
    {
        "source": "**/*.html",
        "headers": [{"key": "Cache-Control", "value": "no-cache"}],
    },
    {
        "source": "**",
        "headers": SECURITY_HEADERS,
    },
]

# ── Per-target ignore lists ─────────────────────────────────────────────
# The root "main" target excludes subdomain folders (each is its own
# hosting target), build outputs, infra docs, and the Python tooling that
# should never be served as static content.
MAIN_IGNORE = [
    "firebase.json",
    "**/.*",
    "**/node_modules/**",
    "aimem/**",
    "tupa/**",
    "tupaide/**",
    "suit/**",
    "bipartitebook/**",
    "installations/**",
    "mattermem/**",
    "dashboard/**",
    ".deploy_cache.json",
    "*.py",
    "scripts/**",
    "lx8_registry.yaml",
    "ARCHITECTURE.md",
    "README.md",
    "docs/**",
    "infrastructure/**",
    "functions/**",
]

SUBDOMAIN_IGNORE = ["firebase.json", "**/.*", "**/node_modules/**"]

# ── Asset sync ──────────────────────────────────────────────────────────
def sync_assets(target_dir):
    """Copy shared client assets (a11y.js, firebase-init.js, i18n/, dashboard/dist)
    into a subdomain's public folder so every site ships them at parity."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for src in ("a11y.js", "firebase-init.js"):
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(target_dir, src))

    if os.path.exists("i18n"):
        dst = os.path.join(target_dir, "i18n")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree("i18n", dst)

    dashboard_dist = os.path.join("dashboard", "dist")
    if os.path.exists(dashboard_dist):
        dst = os.path.join(target_dir, "dashboard")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(dashboard_dist, dst)
        print(f"  -> Synced dashboard dist to {dst}")


def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        print(f"Error: {REGISTRY_FILE} not found.")
        return None
    with open(REGISTRY_FILE) as f:
        return yaml.safe_load(f)


def main_target():
    return {
        "target": "main",
        "public": ".",
        "cleanUrls": True,
        "trailingSlash": False,
        "ignore": MAIN_IGNORE,
        # No catch-all rewrite — broken URLs should fall through to 404.html
        # (Firebase serves it automatically). SPAs at /admin and /dashboard
        # need their own rewrites so client-side routing works.
        "rewrites": [
            {"source": "/admin/**",     "destination": "/admin/index.html"},
            {"source": "/dashboard/**", "destination": "/dashboard/index.html"},
        ],
        "headers": HEADERS_BLOCK,
    }


def subdomain_target(name):
    return {
        "target": name,
        "public": name,
        "cleanUrls": True,
        "ignore": SUBDOMAIN_IGNORE,
        # Subdomain sites are SPAs (Next.js exports or React apps): keep
        # the catch-all rewrite so deep links work.
        "rewrites": [
            {"source": "/dashboard/**", "destination": "/dashboard/index.html"},
            {"source": "**",            "destination": "/index.html"},
        ],
        "headers": HEADERS_BLOCK,
    }


def update_firebase_config(registry_data):
    """Rewrite firebase.json hosting blocks and .firebaserc target map."""
    if os.path.exists(FIREBASE_JSON_FILE):
        with open(FIREBASE_JSON_FILE) as f:
            fb_json = json.load(f)
    else:
        fb_json = {"hosting": []}

    new_hosting = [main_target()]

    if os.path.exists(FIREBASERC_FILE):
        with open(FIREBASERC_FILE) as f:
            fb_rc = json.load(f)
    else:
        fb_rc = {"projects": {"default": PROJECT_ID}, "targets": {PROJECT_ID: {"hosting": {}}}}

    fb_rc.setdefault("targets", {})
    fb_rc["targets"].setdefault(PROJECT_ID, {"hosting": {}})
    targets = fb_rc["targets"][PROJECT_ID]["hosting"]
    targets["main"] = [PROJECT_ID]

    print("Syncing infrastructure from registry…")
    for product in registry_data.get("products", []):
        site_id = product["id"]
        target_name = product["subdomain"]

        new_hosting.append(subdomain_target(target_name))
        targets[target_name] = [site_id]

        sync_assets(target_name)
        print(f"  ✓ Configured {site_id} → {target_name}.lx8labs.com")

    fb_json["hosting"] = new_hosting

    with open(FIREBASE_JSON_FILE, "w") as f:
        json.dump(fb_json, f, indent=2)
        f.write("\n")

    with open(FIREBASERC_FILE, "w") as f:
        json.dump(fb_rc, f, indent=2)
        f.write("\n")

    print("Successfully updated firebase.json and .firebaserc")


def print_manual_dns_instructions(registry_data):
    print("\n" + "=" * 60)
    print("ACTION REQUIRED: DNS & FIREBASE CONSOLE LINKING")
    print("=" * 60)
    print("Custom domain linking requires Firebase domain verification.")
    print(f"URL: https://console.firebase.google.com/project/{PROJECT_ID}/hosting/sites\n")

    header = f"{'Site ID':<20} | {'Custom Domain':<25} | Status"
    print(header)
    print("-" * len(header))
    for product in registry_data.get("products", []):
        site_id = product["id"]
        domain = f"{product['subdomain']}.lx8labs.com"
        print(f"{site_id:<20} | {domain:<25} | Needs linking")

    print("\nFor each site above:")
    print("  1. Click 'Add Custom Domain'")
    print("  2. Enter the Custom Domain name")
    print("  3. Firebase will provide A records — paste them into your DNS provider.")
    print("=" * 60)


if __name__ == "__main__":
    registry = load_registry()
    if registry:
        update_firebase_config(registry)
        print_manual_dns_instructions(registry)
