# Migration: GitHub Pages → Cloudflare Pages

The goal is to make `LX8/lx8-website` private without taking
**lx8labs.com** offline. GitHub Pages from a private repo requires
GitHub Pro/Team/Enterprise, and the LX8 org is on the free plan. Cloudflare
Pages is the planned cloud target anyway (see the master plan, Part 6), so this
migration both unblocks the privacy flip and lands an already-planned move.

## What changes

| | Today | After |
|---|---|---|
| Origin for lx8labs.com | GitHub Pages (legacy, repo root → main) | Cloudflare Pages project `lx8labs` |
| Deploy trigger | Auto on push to `main` (GitHub Pages legacy) | `.github/workflows/cloudflare-pages.yml` on push to `main` |
| DNS / proxy | Cloudflare (already) | Cloudflare (unchanged) — only the backend swaps |
| TLS cert | GitHub Pages-issued (Let's Encrypt) | Cloudflare-issued, automatic |
| Repo visibility | `public` (forced by free plan + Pages) | `private` ✅ |

What does **not** change: the DNS authority stays Cloudflare; the proxy
(`server: cloudflare`) stays in front; nothing on the visitor side moves; the
Firebase **Auth** client SDK calls (used by admin / login / insights pages)
keep working — those hit Google's identity API directly, not Firebase Hosting.

## Pre-cutover gotcha — 4 files exceed the 25 MiB-per-file Pages limit

`bipartitebook/downloads/` ships the book in 4 large artifacts that Cloudflare
Pages will reject at upload:

```
The_Bipartite_Universe.epub          51M
The_Bipartite_Universe_Color.pdf     52M
The_Bipartite_Universe_BW.pdf        52M
The_Bipartite_Universe_Dyslexia.pdf  53M
```

**Fix:** move them to an R2 bucket (Cloudflare object storage) and link from
the book page. R2 supports a custom-domain mapping, so a clean URL like
`https://books.lx8labs.com/The_Bipartite_Universe.epub` is one-line config.
This matches the audit-honest brand value (the dyslexia-accessible variant in
particular is part of the accessibility differentiator — must stay downloadable).

Concrete steps (do BEFORE the first Pages deploy succeeds):

1. `wrangler r2 bucket create lx8-book-downloads`
2. `for f in bipartitebook/downloads/{*.pdf,*.epub}; do wrangler r2 object put lx8-book-downloads/"$(basename $f)" --file "$f"; done`
3. In the Cloudflare dashboard → R2 → bucket → Settings → Connect Domain → `books.lx8labs.com`.
4. Update the download links in `bipartitebook/index.html` (and any other page that points at `bipartitebook/downloads/*`) to the R2 URLs.
5. Add `bipartitebook/downloads/*.pdf` and `*.epub` to a `.assetsignore` in the repo root so Pages skips them on upload.

## Cutover runbook (zero-downtime)

> Steps marked **YOU** need your Cloudflare account; steps marked **CI** run
> automatically once `chore/cloudflare-pages-migration` lands on `main`.

### Phase A — Cloudflare prep (YOU)

1. Install wrangler (one-time):
   ```
   npm install -g wrangler
   wrangler login          # opens browser, OAuths to your CF account
   ```
   *(Alternative: generate a `CLOUDFLARE_API_TOKEN` with `Account.Cloudflare Pages:Edit` + `Account.Workers R2 Storage:Edit` permissions and export it.)*

2. Note your account id (top of `wrangler whoami` output, or
   `https://dash.cloudflare.com/<account_id>`).

3. Move the 4 large book files to R2 (see "Pre-cutover gotcha" above).

4. First deploy from the repo root:
   ```
   cd ~/lx8/lx8-website
   wrangler pages deploy . --project-name=lx8labs --branch=main --commit-dirty=true
   ```
   Output gives a preview URL (`https://<hash>.lx8labs.pages.dev`). Verify
   the homepage matches `https://lx8labs.com`.

### Phase B — DNS cutover (YOU, one click)

5. Cloudflare dashboard → Workers & Pages → `lx8labs` → Custom domains →
   Add `lx8labs.com`. Because the zone is already on Cloudflare, the DNS swap
   from GitHub Pages → Pages is atomic. A new edge cert provisions in
   seconds; the visitor side never blinks.

6. Verify:
   ```
   curl -I https://lx8labs.com/
   ```
   should still return 200, content unchanged.

### Phase C — Tear down old path

7. GitHub: `LX8/lx8-website` → Settings → Pages → "Unpublish site".
8. Delete the now-stale files in a follow-up PR:
   `CNAME`, `firebase.json`, `.firebaserc`, `firestore.rules`,
   `functions/` (orphaned Stripe webhook, superseded by `aimem-license-worker`),
   `.github/workflows/deploy.yml` (Firebase Hosting deploy).

### Phase D — Add the CI deploy

9. Repo Settings → Secrets and variables → Actions, add:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
10. Merge this branch (`chore/cloudflare-pages-migration`). The new
    `.github/workflows/cloudflare-pages.yml` takes over on every push to `main`.

### Phase E — Flip private

11. ```
    gh repo edit LX8/lx8-website --visibility private --accept-visibility-change-consequences
    ```

## Rollback

If Phase B looks wrong, the rollback is one-click: in Cloudflare dashboard,
remove the custom domain from the `lx8labs` Pages project. The
GitHub-Pages-backed DNS rule re-takes effect within seconds (GitHub Pages
remains published until Phase C step 7).

## Verification checklist (end-to-end)

- [ ] `curl -sI https://lx8labs.com/ | grep -i server` → `cloudflare`
- [ ] `curl -s https://lx8labs.com/ | grep '<title>'` matches the pre-cutover snapshot
- [ ] `curl -sI https://lx8labs.com/bipartitebook/` → 200
- [ ] `curl -sI https://books.lx8labs.com/The_Bipartite_Universe.epub` → 200
  (the R2-hosted book downloads)
- [ ] `gh repo view LX8/lx8-website --json visibility --jq .visibility` → `PRIVATE`
- [ ] `gh api repos/LX8/lx8-website/pages` → 404 (site unpublished)
- [ ] A push to `main` triggers `cloudflare-pages.yml` and the change appears live
