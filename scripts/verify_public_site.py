#!/usr/bin/env python3
"""Validate the public Lx8 Labs surface without scanning generated artifacts."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROUTES = (
    "/",
    "/products/",
    "/research/",
    "/changelog/",
    "/team/",
    "/tupa/",
    "/aimem/",
    "/algorithms/",
    "/bipartitebook/",
    "/impressum/",
    "/privacy/",
)
FORBIDDEN_HOMEPAGE_TEXT = (
    'href="#"',
    "buy.stripe.com/test",
    "contact@lx8.io",
    "Founded 2013",
    'name="twitter:site"',
)


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for name in ("href", "src"):
            value = attr_map.get(name)
            if value:
                self.references.append((name, value))


def route_file(route: str) -> Path:
    if route == "/":
        return ROOT / "index.html"
    return ROOT / route.strip("/") / "index.html"


def local_reference_file(reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme or reference.startswith(("#", "mailto:", "tel:")):
        return None
    path = parsed.path
    if not path or path == "/":
        return ROOT / "index.html"
    candidate = ROOT / path.lstrip("/")
    if path.endswith("/"):
        return candidate / "index.html"
    return candidate


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def verify() -> list[str]:
    errors: list[str] = []
    index = ROOT / "index.html"
    html = index.read_text(encoding="utf-8")

    if (ROOT / "CNAME").read_text(encoding="utf-8").strip() != "lx8labs.com":
        fail("CNAME must contain lx8labs.com", errors)
    if not (ROOT / ".nojekyll").exists():
        fail(".nojekyll is required for direct static publication", errors)

    for route in PUBLIC_ROUTES:
        path = route_file(route)
        if not path.is_file():
            fail(f"Missing public route {route}: {path.relative_to(ROOT)}", errors)

    parser = ReferenceParser()
    parser.feed(html)
    for kind, reference in parser.references:
        path = local_reference_file(reference)
        if path is not None and not path.exists():
            fail(f"Homepage {kind} does not resolve: {reference}", errors)

    for forbidden in FORBIDDEN_HOMEPAGE_TEXT:
        if forbidden in html:
            fail(f"Homepage contains forbidden placeholder or unverified claim: {forbidden}", errors)

    jsonld_blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        html,
        flags=re.DOTALL,
    )
    if not jsonld_blocks:
        fail("Homepage must contain JSON-LD", errors)
    for block in jsonld_blocks:
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            fail(f"Invalid homepage JSON-LD: {exc}", errors)

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    icon_path = local_reference_file(manifest["icons"][0]["src"])
    if icon_path is None or not icon_path.is_file():
        fail("Manifest icon does not resolve", errors)

    translations = (ROOT / "i18n" / "translations.js").read_text(encoding="utf-8")
    translation_keys = set(re.findall(r'data-i18n="([^"]+)"', html))
    for key in sorted(translation_keys):
        if translations.count(f'"{key}":') != 3:
            fail(f"Homepage translation must exist once in EN, PT-BR and DE: {key}", errors)

    for workflow_name in ("cloudflare-pages.yml", "deploy.yml", "central-deploy.yml"):
        workflow = (ROOT / ".github" / "workflows" / workflow_name).read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*push:\s*$", workflow):
            fail(f"{workflow_name} must not auto-deploy while credentials/provider are unresolved", errors)

    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1
    print(f"[OK] Public website verified: {len(PUBLIC_ROUTES)} routes, local brand assets, valid JSON-LD")
    return 0


if __name__ == "__main__":
    sys.exit(main())
