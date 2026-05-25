# Legacy one-off scripts

These were ad-hoc migration / patch scripts used at specific historical
moments (e.g., `patch_csp.py`, `patch_csp2.py`, `patch_csp3.py` to roll
out three iterations of Content Security Policy across all pages).

They are preserved here for traceability but are **not part of the build
or deploy pipeline**. Treat them as read-only artifacts; if you need
similar functionality, prefer extending `scripts/sync_infrastructure.py`
or writing a fresh, single-purpose helper.

## Inventory

| Script | Purpose (historical) |
| --- | --- |
| `add_a11y.py` | Inject the a11y.js bootstrap into every page. |
| `apply_security.py` | First-pass CSP + security headers across pages. |
| `build_admin_cms.py` | Scaffold the admin CMS skeleton. |
| `create_shop_and_update_nav.py` | Create the /shop section and add it to nav. |
| `fix_filters.py`, `fix_iframe_styles.py`, `fix_links.py`, `fix_optimizations.py` | Targeted bug-fix sweeps. |
| `inject_i18n.py`, `nav_i18n.py` | Wire i18n hooks into nav / pages. |
| `modify_index.py` | Bulk-edit the homepage. |
| `optimize.py`, `optimize_lcp.py`, `optimize_scripts.py`, `optimize_square.py` | Perf experiments. |
| `parse_lighthouse.py` | Parse a Lighthouse JSON report into a summary. |
| `patch_csp.py`, `patch_csp2.py`, `patch_csp3.py` | Three iterations of the CSP rollout (now superseded by the canonical CSP in `firebase.json`). |
| `remove_links.py`, `restore_links.py` | Bulk link surgery. |
| `restructure.py`, `restructure2.py` | Section-layout migrations. |
| `seed_courses.py` | Seed Firestore with the initial course catalogue. |
| `update_courses_page.py`, `update_footers.py`, `update_ft_grid.py` | Per-page bulk updates. |

If any of these turn out to still be needed, please promote them into
`scripts/` proper with a clear name, a `--help` flag, and tests.
