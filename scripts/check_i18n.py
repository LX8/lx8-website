#!/usr/bin/env python3
"""
Verify that every `data-i18n="…"` reference in authored HTML pages has a
matching key in every language block of `i18n/translations.js`.

A missing key isn't a runtime crash — `i18n/engine.js` falls back to the
default language — but it silently degrades pt-BR / de visitors to
English placeholders and is invisible until someone opens the language
switcher. Failing CI on the gap forces the translation to land in the
same PR as the markup.

Usage:
    python3 scripts/check_i18n.py            # report and exit 0 if clean
    python3 scripts/check_i18n.py --json     # machine-readable

Languages required: en, pt-BR, de (matches i18n/engine.js).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS = REPO_ROOT / "i18n" / "translations.js"
REQUIRED_LANGS = ("en", "pt-BR", "de")

# Paths to skip when scanning for data-i18n usage:
#   - Build outputs (bipartitebook is a Next.js export; Vite dashboards)
#   - Vendored node_modules anywhere
SKIP_DIR_NAMES = {"node_modules", "__pycache__", "bipartitebook", "dashboard"}


def authored_html_paths() -> list[Path]:
    paths: list[Path] = []
    for p in REPO_ROOT.rglob("*.html"):
        rel = p.relative_to(REPO_ROOT)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        paths.append(p)
    return sorted(paths)


def collect_html_keys() -> set[str]:
    keys: set[str] = set()
    pattern = re.compile(r'data-i18n="([^"]+)"')
    for p in authored_html_paths():
        keys.update(pattern.findall(p.read_text()))
    return keys


def collect_translation_keys() -> dict[str, set[str]]:
    """For each required language, return the set of keys defined inside its
    block. Robust to surrounding whitespace and trailing commas; relies on
    the convention that each language is opened by `<lang>: {` and closed
    by a balanced `}`."""
    src = TRANSLATIONS.read_text()
    out: dict[str, set[str]] = {}
    open_re = re.compile(r'"?([a-zA-Z-]+)"?\s*:\s*\{', re.MULTILINE)
    i = 0
    while i < len(src):
        m = open_re.search(src, i)
        if not m:
            break
        lang = m.group(1)
        if lang not in REQUIRED_LANGS:
            i = m.end()
            continue
        depth = 1
        j = m.end()
        while j < len(src) and depth > 0:
            c = src[j]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            j += 1
        body = src[m.end():j-1]
        keys = set(re.findall(r'"([^"\\]+)"\s*:', body))
        out[lang] = keys
        i = j
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of a table.")
    args = parser.parse_args()

    html_keys = collect_html_keys()
    lang_keys = collect_translation_keys()
    missing_langs = [lang for lang in REQUIRED_LANGS if lang not in lang_keys]
    if missing_langs:
        print(f"error: translations.js is missing required language block(s): "
              f"{', '.join(missing_langs)}", file=sys.stderr)
        return 2

    gaps = {lang: sorted(html_keys - lang_keys[lang]) for lang in REQUIRED_LANGS}
    total_missing = sum(len(g) for g in gaps.values())

    if args.json:
        print(json.dumps({
            "html_keys_count": len(html_keys),
            "gaps": gaps,
            "total_missing": total_missing,
        }, indent=2))
    else:
        print(f"data-i18n keys referenced in authored HTML: {len(html_keys)}")
        for lang, missing in gaps.items():
            mark = "✓" if not missing else "✗"
            print(f"  {mark} {lang}: {len(lang_keys[lang])} keys defined; "
                  f"{len(missing)} missing")
            for k in missing:
                print(f"      - {k}")

    return 1 if total_missing else 0


if __name__ == "__main__":
    sys.exit(main())
