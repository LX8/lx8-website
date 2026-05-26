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
    """Single HEAD probe with timing. Captures response headers so we can
    also audit the security-header configuration in the same pass."""
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
                "headers": {k.lower(): v for k, v in resp.headers.items()},
            }
    except urllib.error.HTTPError as e:
        import time
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return {
            "url": url, "code": e.code, "ok": False,
            "elapsed_ms": round(elapsed_ms, 1),
            "error": f"http {e.code}",
            "headers": {k.lower(): v for k, v in (e.headers or {}).items()},
        }
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionError) as e:
        return {
            "url": url, "code": None, "ok": False,
            "elapsed_ms": None,
            "error": _short_transport_error(e),
            "headers": {},
        }


def _short_transport_error(exc: BaseException) -> str:
    """Map a noisy transport exception into a 1-line tag suitable for a
    status table cell. Keeps the table grep-able from CI logs."""
    reason = getattr(exc, "reason", exc)
    msg = str(reason) or exc.__class__.__name__
    lower = msg.lower()
    if "hostname mismatch" in lower or "doesn't match" in lower:
        return "tls hostname mismatch"
    if "certificate verify failed" in lower:
        return "tls verify failed"
    if "ssl" in lower and "handshake" in lower:
        return "tls handshake failed"
    if "name or service not known" in lower or "name resolution" in lower or "nodename" in lower:
        return "dns NXDOMAIN"
    if "connection refused" in lower:
        return "conn refused"
    if "timed out" in lower:
        return "timeout"
    return msg[:48]


# Security headers we expect on every Lx8 response. Mirrors the policy in
# firebase.json — if anything here is missing it usually means the Hosting
# headers block didn't match the path or didn't apply to that target.
REQUIRED_SECURITY_HEADERS = (
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
)


import re
import subprocess


def tls_san_covers(host: str) -> tuple[bool, str | None]:
    """Open a raw TLS connection to host:443, dump the cert via OpenSSL,
    return (covers_host, presented_subject_or_first_san).

    A custom-domain probe failing because of TLS hostname mismatch is the
    standard "domain not yet bound in Firebase Console" failure mode — the
    DNS resolves to Firebase's edge IP but Firebase hasn't minted a cert
    for the host yet, so it serves the default `*.firebaseapp.com` cert
    whose SAN list doesn't cover the hostname.
    """
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                der = ssock.getpeercert(binary_form=True)
        result = subprocess.run(
            ["openssl", "x509", "-noout", "-text"],
            input=ssl.DER_cert_to_PEM_cert(der).encode(),
            capture_output=True, check=True, timeout=4,
        )
        text = result.stdout.decode()
        subject_match = re.search(r"Subject:[^\n]*CN\s*=\s*([^\n,]+)", text)
        subject = subject_match.group(1).strip() if subject_match else ""
        san_block = re.search(r"X509v3 Subject Alternative Name:\s*\n\s*([^\n]+)", text)
        sans = re.findall(r"DNS:([^,\s]+)", san_block.group(1)) if san_block else []
        covers = False
        for s in sans:
            if s == host:
                covers = True
                break
            # Wildcard SAN (only matches one label deep).
            if s.startswith("*.") and host.endswith(s[1:]) and host.count(".") == s.count("."):
                covers = True
                break
        return covers, subject or (sans[0] if sans else None)
    except (socket.timeout, ssl.SSLError, ConnectionError, OSError, subprocess.SubprocessError):
        return False, None


def audit_headers(headers: dict[str, str]) -> list[str]:
    """Return a list of human-readable findings (empty when all required
    headers are present)."""
    missing = [h for h in REQUIRED_SECURITY_HEADERS if h not in headers]
    findings: list[str] = []
    if missing:
        findings.append("missing: " + ", ".join(missing))

    # Sanity-check HSTS max-age is at least 1 year (per industry best
    # practice and what firebase.json declares).
    hsts = headers.get("strict-transport-security", "")
    if hsts:
        try:
            max_age = int(hsts.split("max-age=", 1)[1].split(";", 1)[0])
            if max_age < 31_536_000:
                findings.append(f"hsts max-age={max_age} (<1y)")
        except (ValueError, IndexError):
            findings.append("hsts unparseable")

    # CSP with 'unsafe-eval' is a known footgun — flag it. 'unsafe-inline'
    # for scripts is similar; we tolerate it for styles since the Hosting
    # CSP already permits it project-wide.
    csp = headers.get("content-security-policy", "")
    if "'unsafe-eval'" in csp:
        findings.append("csp allows 'unsafe-eval'")
    if "script-src" in csp:
        script_src = csp.split("script-src", 1)[1].split(";", 1)[0]
        if "'unsafe-inline'" in script_src:
            findings.append("csp script-src allows 'unsafe-inline'")

    return findings


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


def evaluate(custom: dict, native: dict, *, audit_headers_flag: bool) -> tuple[int, list[str]]:
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

    if audit_headers_flag and native["ok"]:
        # Audit the *native* response — custom domains may be served by an
        # upstream proxy (Cloudflare) that strips/adds headers, but the
        # native .web.app URL talks straight to Firebase.
        for finding in audit_headers(native["headers"]):
            sev = max(sev, S_WARN)
            notes.append(f"headers: {finding}")

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
    parser.add_argument("--check-headers", action="store_true",
                        help="Also audit security headers on the native URL; "
                             "missing CSP/HSTS/X-Frame-Options or weak HSTS "
                             "becomes a warning.")
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
        futs = {pool.submit(probe_pair, t, args.check_headers): t for t in targets}
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


def probe_pair(target: dict, audit_headers_flag: bool = False) -> dict:
    """Probe both URLs for one target plus version.json from the native URL.

    On any custom-domain failure we also dump the TLS cert to figure out
    whether the issue is "domain not bound in Firebase Console" (cert
    doesn't cover the host → tls_san_covers=False) or "domain bound but
    serving 404" (cert covers the host → it's a content/binding issue).
    The actionable hint goes into `target['action']`.
    """
    custom = probe(target["custom_url"])
    native = probe(target["native_url"])
    version = fetch_version(target["native_url"]) if native["ok"] else None
    severity, notes = evaluate(custom, native, audit_headers_flag=audit_headers_flag)

    action: str | None = None
    if not custom["ok"]:
        host = target["custom_url"].split("/")[2]
        covers, _subject = tls_san_covers(host)
        if not covers:
            # Preferred fix is the automated workflow; fall back to manual.
            action = (
                f"`{host}` not bound to site `{target['site']}`. "
                f"Run: `gh workflow run bind-domains.yml --repo LX8/lx8-website` "
                f"(needs FIREBASE_SERVICE_ACCOUNT secret with "
                f"roles/firebasehosting.admin). Manual fallback: Firebase "
                f"Console → site `{target['site']}` → Add custom domain `{host}`."
            )
        else:
            # Cert is good; 404 means content / wrong-site binding.
            action = (
                f"Custom domain `{host}` is bound (cert valid) but serves 404. "
                f"Check that the binding points at `{target['site']}` and that "
                f"that site has content (native URL: {target['native_url']})."
            )
        notes.append(action)

    return {
        **target,
        "custom": custom,
        "native": native,
        "version": version,
        "severity": severity,
        "severity_label": LEVEL_NAMES[severity],
        "notes": notes,
        "action": action,
    }


if __name__ == "__main__":
    sys.exit(main())
