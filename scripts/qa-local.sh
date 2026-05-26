#!/usr/bin/env bash
# Local equivalent of the gates in .github/workflows/qa.yml. Run before
# pushing so CI doesn't surface anything you could have caught in 30
# seconds at your desk.
#
# Each gate prints its own banner; the script exits non-zero on the first
# failing gate. Set FAST=1 to skip the html-validate install if you've
# already done it once.
#
# Usage:
#   bash scripts/qa-local.sh
#   FAST=1 bash scripts/qa-local.sh

set -euo pipefail

cd "$(dirname "$0")/.."

c_green=$'\033[32m'
c_red=$'\033[31m'
c_blue=$'\033[36m'
c_dim=$'\033[2m'
c_reset=$'\033[0m'

step() { printf '\n%s━━ %s ━━%s\n' "$c_blue" "$1" "$c_reset"; }
ok()   { printf '%s✓ %s%s\n' "$c_green" "$1" "$c_reset"; }
fail() { printf '%s✗ %s%s\n' "$c_red"   "$1" "$c_reset"; exit 1; }

# 1. sitemap.xml drift
step "sitemap.xml drift"
python3 scripts/generate_sitemap.py --check && ok "sitemap up to date" \
    || fail "sitemap.xml is stale — run: python3 scripts/generate_sitemap.py"

# 2. CSP drift between firebase.json and inline <meta>
step "CSP drift"
python3 scripts/sync_csp.py --check && ok "CSP in sync" \
    || fail "meta CSP drift — run: python3 scripts/sync_csp.py"

# 2b. feed.xml drift from insights/*.html metadata
step "feed.xml drift"
python3 scripts/generate_feed.py --check && ok "feed.xml up to date" \
    || fail "feed.xml is stale — run: python3 scripts/generate_feed.py"

# 2c. i18n key coverage across en / pt-BR / de
step "i18n key coverage"
python3 scripts/check_i18n.py >/dev/null && ok "every data-i18n key translated in all 3 languages" \
    || { python3 scripts/check_i18n.py; fail "i18n gap — fill in i18n/translations.js"; }

# 3. Subdomain placeholder stubs
step "subdomain stub check"
python3 scripts/build_placeholders.py --check && ok "no <h1>Welcome to…</h1> stubs" \
    || fail "stub subdomain found — run: python3 scripts/build_placeholders.py"

# 3b. Dashboard build (tsc + vite). Skipped if no node_modules and SKIP_DASHBOARD=1.
step "dashboard build (tsc + vite)"
if [ -n "${SKIP_DASHBOARD:-}" ]; then
    printf '%sSKIP_DASHBOARD set — skipping dashboard build%s\n' "$c_dim" "$c_reset"
elif [ ! -d dashboard ]; then
    printf '%sno dashboard/ — skipping%s\n' "$c_dim" "$c_reset"
else
    (cd dashboard && \
        if [ -f package-lock.json ]; then
            npm ci --silent --no-audit --no-fund
        else
            npm install --silent --no-audit --no-fund
        fi && \
        npm run build) \
    && ok "dashboard built" \
    || fail "dashboard build failed — fix tsc/vite errors"
fi

# 4. html-validate over authored HTML
step "html-validate"
if [ -z "${FAST:-}" ]; then
    printf '%s(installing html-validate; set FAST=1 to skip)%s\n' "$c_dim" "$c_reset"
fi
mapfile -t files < <(find . \
    \( -type d \( -name node_modules -o -name __pycache__ \
                 -o -path './bipartitebook' \
                 -o -path './dashboard' -o -path '*/dashboard' \) -prune \) \
    -o -type f -name '*.html' -print)
printf '%s%d authored .html file(s)%s\n' "$c_dim" "${#files[@]}" "$c_reset"
npx --yes html-validate@9 --max-warnings 200 "${files[@]}" \
    && ok "html-validate clean" \
    || fail "html-validate found errors"

# 5. Internal link check (lychee) — optional. Skipped if the binary isn't
#    available locally; CI runs it.
step "lychee internal-link check"
if command -v lychee >/dev/null 2>&1; then
    lychee --offline --no-progress --include-fragments \
        --root-dir "$(pwd)" \
        --exclude '^mailto:' --exclude '^https?://' \
        --exclude-path 'functions/node_modules' \
        --exclude-path 'dashboard' \
        --exclude-path 'aimem/dashboard' \
        --exclude-path 'bipartitebook' \
        --exclude-path 'installations/dashboard' \
        --exclude-path 'mattermem/dashboard' \
        --exclude-path 'suit/dashboard' \
        --exclude-path 'tupa/dashboard' \
        --exclude-path 'tupaide/dashboard' \
        '**/*.html' '**/*.md' \
        && ok "no broken internal links" \
        || fail "lychee reported broken internal links"
else
    printf '%slychee not installed locally — CI will still run it%s\n' "$c_dim" "$c_reset"
fi

# 6. Subdomain probe (live; skipped without network)
step "subdomain probe (live)"
if [ -n "${SKIP_NETWORK:-}" ]; then
    printf '%sSKIP_NETWORK set — skipping live probe%s\n' "$c_dim" "$c_reset"
else
    if python3 -c 'import yaml, certifi' 2>/dev/null; then
        python3 scripts/verify_subdomains.py --include-apex --check-headers \
            || printf '%s(non-zero exit only on FAIL severity; warnings are fine)%s\n' \
                 "$c_dim" "$c_reset"
    else
        printf '%spyyaml/certifi missing — pip install pyyaml certifi%s\n' \
            "$c_dim" "$c_reset"
    fi
fi

printf '\n%sAll local QA gates passed.%s\n' "$c_green" "$c_reset"
