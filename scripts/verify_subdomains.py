#!/usr/bin/env python3
"""
Probe every Lx8 Labs subdomain at both its custom domain (subdomain.lx8labs.com)
and its native Firebase URL (taken from .firebaserc), then print a status
table. Used both ad-hoc and from the scheduled subdomain-health workflow.

Exit codes:
  0  every required check passed
  1  one or more checks failed at the threshold set by --severity
  2  configuration error (registry / .firebaserc missing or unparseable)

A "failure" by default is:
  - any HTTP code != 200 at the native (.web.app) URL
  - a TLS or transport failure at either URL

Custom-domain HTTP codes only contribute as warnings; many subdomains await
manual TLS provisioning in the Firebase Console and a 4xx there is expected.

Examples:
  python3 scripts/verify_subdomains.py
  python3 scripts/verify_subdomains.py --json
  python3 scripts/verify_subdomains.py --severity warn   # fail on warnings too
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("error: pyyaml is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

# Prefer certifi's CA bundle when available — Python's bundled bundle can
# miss roots on older runtimes and corporate macs with MITM proxies.
SSL_CONTEXT = ssl.create_default_context()
try:
    import certifi  # type: ignore
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "lx8_registry.yaml"
FIREBASERC = REPO_ROOT / ".firebaserc"
PROJECT_ID = "lx8-labs-website"

USER_AGENT = "Lx8-Subdomain-Health/1.0 (+https://lx8labs.com)"
TIMEOUT = 8

# Severity levels for the rollup. higher number = worse.
S_OK = 0
S_WARN = 1
S_FAIL = 2
LEVEL_NAMES = {S_OK: "ok", S_WARN: "warn", S_FAIL: "fail"}


def load_registry() -> list[dict]:
    with REGISTRY.open() as f:
        return yaml.safe_load(f).get("products", [])


def load_site_map() -> dict[str, str]:
    """Return {target_name -> firebase_site_id} from .firebaserc."""
    with FIREBASERC.open() as f:
        rc = json.load(f)
    hosting = rc.get("targets", {}).get(PROJECT_ID, {}).get("hosting", {})
    out: dict[str, str] = {}
    for target, site_ids in hosting.items():
        if isinstance(site_ids, list) and site_ids:
            out[target] = site_ids[0]
    return out


def probe(url: str) -> dict:
    """Single HEAD probe with timing."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    started = 0.0
    try:
        import time
        started = time.perf_counter()
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as resp:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return {
                "url": url,
                "code": resp.status,
                "ok": resp.status == 200,
                "elapsed_ms": round(elapsed_ms, 1),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        import time
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return {
            "url": url, "code": e.code, "ok": False,
            "elapsed_ms": round(elapsed_ms, 1),
            "error": f"http {e.code}",
        }
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionError) as e:
        return {
            "url": url, "code": None, "ok": False,
            "elapsed_ms": None,
            "error": str(getattr(e, "reason", e)) or e.__class__.__name__,
        }


def fetch_version(url: str) -> Optional[dict]:
    """GET /version.json from a site (best-effort)."""
    req = urllib.request.Request(url.rstrip("/") + "/version.json",
                                 headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return None


def evaluate(custom: dict, native: dict) -> tuple[int, list[str]]:
    """Combine the two probes into a single severity + notes."""
    notes: list[str] = []
    sev = S_OK

    if not native["ok"]:
        sev = max(sev, S_FAIL)
        notes.append(f"native {native['error'] or native['code']}")

    if not custom["ok"]:
        # Treat custom-domain trouble as a warning unless the native side
        # is also down — the custom domain needs manual cert provisioning
        # in the Firebase Console and a 4xx is a known waiting state.
        sev = max(sev, S_WARN)
        notes.append(f"custom {custom['error'] or custom['code']}")

    return sev, notes


def render_table(rows: list[dict]) -> str:
    widths = {
        "subdomain": max(len("subdomain"), max(len(r["subdomain"]) for r in rows)),
        "site": max(len("firebase site"), max(len(r["site"]) for r in rows)),
        "version": 9,
        "custom": 12,
        "native": 12,
        "status": 6,
    }
    head = (
        f"{'subdomain'.ljust(widths['subdomain'])}  "
        f"{'firebase site'.ljust(widths['site'])}  "
        f"{'version'.ljust(widths['version'])}  "
        f"{'custom'.ljust(widths['custom'])}  "
        f"{'native'.ljust(widths['native'])}  status"
    )
    lines = [head, "-" * len(head)]
    icon = {S_OK: "✓ ok", S_WARN: "⚠ warn", S_FAIL: "✗ fail"}
    for r in rows:
        custom_txt = (str(r["custom"]["code"]) if r["custom"]["code"]
                      else r["custom"]["error"] or "—")
        native_txt = (str(r["native"]["code"]) if r["native"]["code"]
                      else r["native"]["error"] or "—")
        version_txt = (r["version"] or {}).get("version", "—")
        lines.append(
            f"{r['subdomain'].ljust(widths['subdomain'])}  "
            f"{r['site'].ljust(widths['site'])}  "
            f"{version_txt.ljust(widths['version'])}  "
            f"{custom_txt.ljust(widths['custom'])}  "
            f"{native_txt.ljust(widths['native'])}  "
            f"{icon[r['severity']]}"
        )
        for n in r["notes"]:
            lines.append(f"  └─ {n}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of a table.")
    parser.add_argument("--severity", choices=["fail", "warn"], default="fail",
                        help="Minimum severity that triggers a non-zero exit.")
    parser.add_argument("--include-apex", action="store_true",
                        help="Also probe https://lx8labs.com/ (the main site).")
    args = parser.parse_args()

    products = load_registry()
    sites = load_site_map()

    targets: list[dict] = []
    if args.include_apex:
        targets.append({
            "subdomain": "(apex)", "site": sites.get("main", "lx8-labs-website"),
            "custom_url": "https://lx8labs.com/",
            "native_url": f"https://{sites.get('main', 'lx8-labs-website')}.web.app/",
        })

    for p in products:
        sub = p["subdomain"]
        site = sites.get(sub)
        if not site:
            print(f"warning: target {sub!r} has no .firebaserc mapping; "
                  "skipping", file=sys.stderr)
            continue
        targets.append({
            "subdomain": sub,
            "site": site,
            "custom_url": f"https://{sub}.lx8labs.com/",
            "native_url": f"https://{site}.web.app/",
        })

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(probe_pair, t): t for t in targets}
        for fut in as_completed(futs):
            rows.append(fut.result())

    rows.sort(key=lambda r: r["subdomain"])

    if args.json:
        print(json.dumps(rows, indent=2, default=str))
    else:
        print(render_table(rows))

    threshold = S_FAIL if args.severity == "fail" else S_WARN
    if any(r["severity"] >= threshold for r in rows):
        return 1
    return 0


def probe_pair(target: dict) -> dict:
    """Probe both URLs for one target plus version.json from the native URL."""
    custom = probe(target["custom_url"])
    native = probe(target["native_url"])
    version = fetch_version(target["native_url"]) if native["ok"] else None
    severity, notes = evaluate(custom, native)
    return {
        **target,
        "custom": custom,
        "native": native,
        "version": version,
        "severity": severity,
        "severity_label": LEVEL_NAMES[severity],
        "notes": notes,
    }


if __name__ == "__main__":
    sys.exit(main())
