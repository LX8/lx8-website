#!/usr/bin/env python3
"""
Remove the broken X/Twitter link from all HTML pages and normalize
social footer markup across lx8-website.

The X handle @lx8labs resolves to 404; keeping the link hurts credibility.
LinkedIn currently points to the founder's personal profile. Once the
LinkedIn Company Page (linkedin.com/company/lx8labs) is created, run this
script again with the --linkedin-company flag to update that link.
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Patterns that cover both the icon-row footer and the text-link footer.
X_LINK_RE = re.compile(
    r'\s*<a[^>]*href="https?://x\.com/lx8labs"[^>]*>.*?</a>',
    re.IGNORECASE | re.DOTALL,
)

X_SAMEAS_RE = re.compile(
    r'\s*"https?://x\.com/lx8labs",?',
    re.IGNORECASE,
)

LINKEDIN_PERSONAL = "https://de.linkedin.com/in/lx8-alexei"
LINKEDIN_COMPANY = "https://www.linkedin.com/company/lx8labs"


def collect_html_files(root: str) -> list[str]:
    html_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip dependency/build directories.
        skip_dirs = {".git", "node_modules", ".firebase", "dist", "dashboard", "assets"}
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            if filename.endswith(".html"):
                html_files.append(os.path.join(dirpath, filename))
    return sorted(html_files)


def fix_file(path: str, linkedin_company: bool) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    content = original

    # Remove the broken X link from HTML.
    content = X_LINK_RE.sub("", content)

    # Remove the broken X link from JSON-LD sameAs arrays.
    content = X_SAMEAS_RE.sub("", content)

    # Optionally point LinkedIn to the company page once it exists.
    if linkedin_company:
        content = content.replace(LINKEDIN_PERSONAL, LINKEDIN_COMPANY)

    if content == original:
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix LX8 website social links")
    parser.add_argument(
        "--linkedin-company",
        action="store_true",
        help="Point LinkedIn links to the LX8 Labs company page instead of the founder profile",
    )
    args = parser.parse_args()

    files = collect_html_files(ROOT)
    changed = 0
    for path in files:
        if fix_file(path, args.linkedin_company):
            rel = os.path.relpath(path, ROOT)
            print(f"Updated {rel}")
            changed += 1

    print(f"\n{changed} file(s) updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
