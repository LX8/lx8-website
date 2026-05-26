#!/usr/bin/env python3
"""
Bind every Lx8 Labs subdomain to its Firebase Hosting site via the
Firebase Hosting REST API. Source of truth: `lx8_registry.yaml` +
`.firebaserc` (the existing site_id map).

Why this script exists despite `LX8/lx8-infrastructure` having a
Terraform declaration for the same resource: GitHub Actions minutes on
private repos are not paid for in this org (policy 2026-05-20), so a
Terraform-CI loop in that private repo can't allocate a runner. Public
repos get free Actions minutes — so the actual REST-API call lives
here in the public `lx8-website` repo. The Terraform file in
`lx8-infrastructure` stays as declarative intent for the day paid CI
becomes available (or for manual `terraform apply` from a workstation).

API reference:
  https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.sites.customDomains

Auth:
  Uses Application Default Credentials. In CI, the
  GOOGLE_APPLICATION_CREDENTIALS env var should point at a service
  account JSON with `roles/firebasehosting.admin` (already materialised
  by deploy.yml). Locally, run `gcloud auth application-default login`
  once.

Usage:
    python3 scripts/bind_custom_domains.py --check    # exit 1 if any
                                                      # custom domain
                                                      # is missing on
                                                      # Firebase
    python3 scripts/bind_custom_domains.py --apply    # create the
                                                      # missing
                                                      # bindings
    python3 scripts/bind_custom_domains.py --dry-run --apply
                                                      # print what
                                                      # --apply would
                                                      # do without
                                                      # calling the API
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: pyyaml is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

try:
    from google.auth import default as gcp_default
    from google.auth.transport.requests import Request
except ImportError:
    print("error: google-auth is required (pip install google-auth google-auth-httplib2 requests)",
          file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "lx8_registry.yaml"
FIREBASERC = REPO_ROOT / ".firebaserc"
PROJECT = "lx8-labs-website"
API_BASE = f"https://firebasehosting.googleapis.com/v1beta1/projects/{PROJECT}"


def gcp_token() -> str:
    """Get an OAuth2 access token via Application Default Credentials."""
    creds, _ = gcp_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())
    return creds.token


def load_targets() -> list[dict]:
    """Return [{host, site_id}, ...] derived from the registry + .firebaserc.

    The registry lists which subdomains exist; .firebaserc maps each
    subdomain to its Firebase Hosting site_id. We need both to know
    which (host, site) pair to bind.
    """
    rc = json.loads(FIREBASERC.read_text())
    sites = rc["targets"][PROJECT]["hosting"]
    registry = yaml.safe_load(REGISTRY.read_text())
    targets = []
    for product in registry.get("products", []):
        sub = product["subdomain"]
        site_ids = sites.get(sub) or []
        if not site_ids:
            print(f"  ! {sub}: no .firebaserc mapping — skipping", file=sys.stderr)
            continue
        targets.append({
            "host": f"{sub}.lx8labs.com",
            "site_id": site_ids[0],
        })
    return targets


def http_json(method: str, url: str, token: str, body: dict | None = None,
              timeout: int = 30) -> tuple[int, dict | None]:
    """Tiny urllib wrapper. Returns (status_code, parsed_body).

    Avoids dragging in `requests` so the script's deps stay to pyyaml +
    google-auth + the stdlib. google-auth has its own urllib-style
    transport, but the simple GET/POST path is shorter via stdlib.
    """
    req = urllib.request.Request(url, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Lx8-bind-custom-domains/1.0",
    })
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8", errors="replace")
        try:
            body_json = json.loads(payload)
        except Exception:
            body_json = {"_raw": payload}
        return e.code, body_json


def list_existing_domains(token: str, site_id: str) -> list[str]:
    """Return the list of custom-domain hostnames already bound on `site_id`."""
    code, body = http_json(
        "GET", f"{API_BASE}/sites/{site_id}/customDomains", token,
    )
    if code == 404 or not body:
        return []
    if code != 200:
        print(f"  ! list {site_id}: HTTP {code} — {body}", file=sys.stderr)
        return []
    out = []
    for entry in body.get("customDomains", []):
        # entry["name"] is "projects/{p}/sites/{s}/customDomains/{host}"
        full = entry.get("name", "")
        if "/customDomains/" in full:
            out.append(full.split("/customDomains/")[-1])
    return out


def create_domain(token: str, site_id: str, host: str, *, dry_run: bool) -> dict:
    """POST a new customDomain. Idempotent: a 409 (already exists) is OK."""
    url = f"{API_BASE}/sites/{site_id}/customDomains?customDomainId={host}"
    if dry_run:
        return {"dry_run": True, "would_post": url}
    code, body = http_json("POST", url, token, body={})
    if code == 200:
        return {"status": "created", "body": body}
    if code == 409:
        return {"status": "already_exists"}
    return {"status": "error", "code": code, "body": body}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="Drift report only; exit 1 if any binding is missing.")
    parser.add_argument("--apply", action="store_true",
                        help="Create missing bindings.")
    parser.add_argument("--dry-run", action="store_true",
                        help="With --apply, print intended API calls without making them.")
    args = parser.parse_args()

    if not (args.check or args.apply):
        parser.error("specify --check or --apply")

    try:
        token = gcp_token()
    except Exception as e:  # noqa: BLE001 — clear top-level error message
        print(f"error: could not obtain a GCP access token: {e}", file=sys.stderr)
        print("       in CI, ensure GOOGLE_APPLICATION_CREDENTIALS is set;", file=sys.stderr)
        print("       locally, run `gcloud auth application-default login`.", file=sys.stderr)
        return 2

    targets = load_targets()
    missing: list[dict] = []
    print(f"Checking {len(targets)} subdomain binding(s) against Firebase Hosting:")
    for t in targets:
        existing = list_existing_domains(token, t["site_id"])
        if t["host"] in existing:
            print(f"  ✓ {t['host']:32s} → {t['site_id']}")
        else:
            print(f"  ✗ {t['host']:32s} → {t['site_id']}  (missing)")
            missing.append(t)

    if args.check:
        if missing:
            print(f"\n{len(missing)} binding(s) missing. Run --apply to create.",
                  file=sys.stderr)
            return 1
        print("\nAll bindings present.")
        return 0

    # apply mode
    if not missing:
        print("\nNothing to do.")
        return 0

    print(f"\nCreating {len(missing)} binding(s)…")
    failed = 0
    for t in missing:
        result = create_domain(token, t["site_id"], t["host"], dry_run=args.dry_run)
        if result.get("status") == "error":
            failed += 1
            print(f"  ✗ {t['host']:32s} → {t['site_id']}  {result}", file=sys.stderr)
        else:
            print(f"  ✓ {t['host']:32s} → {t['site_id']}  ({result.get('status', 'dry-run')})")

    if failed:
        print(f"\n{failed} create(s) failed.", file=sys.stderr)
        return 1

    if args.dry_run:
        print("\nDry-run complete; no API calls made.")
    else:
        print("\nDone. Let's Encrypt cert provisioning takes ~30 min – 24 h.")
        print("Re-run `verify_subdomains.py` after that to confirm each host is live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
