# Workspace rules

Written after two sessions working at once collided inside this repo on
10 Aug 2026. What happened, and how to keep projects out of each other.

## What went wrong

A second session generalised `tools/fb_photo_grab.py` to accept any page URL,
then ran it for **Overspray Solutions** with the output path still pointing at
`C:\Users\dlint\formulamobile\facebook-photos\`. The result: **1,249 photos
(166 MB) belonging to a different client** sat inside Formula's repo, one
`git add -A` away from being committed and deployed to Formula's site.

At the same time this directory lost `.git`, `site/`, `docs/`, `README.md`, and
230 of its 231 photos. Everything was recoverable only because it had been
pushed. Those files have been restored from the remote, and Overspray's photos
moved to `C:\Users\dlint\CDS---Overspray-Solutions\facebook-photos\`.

## Rules

**One project, one directory, one repo.** Never write another client's output
into this tree, even temporarily. Each of these has its own repo:

| Project | Directory | Repo |
|---|---|---|
| Formula Mobile Car Detailing | `formulamobile/` | `neuronestaudio/formulamobile` |
| CDS / Overspray Solutions | `CDS---Overspray-Solutions/` | `neuronestaudio/CDS---Overspray-Solutions` |
| Premier Mobile Detailing | `premier-ppf/` | `neuronestaudio/Premiermobiledetailing` |
| Glossed Out | `Glossedout/` | `neuronestaudio/Glossedout` |

**Tools that write files take an explicit output path.** `fb_photo_grab.py` now
takes `<storage_state.json> <page_url> [output_dir]`. Never leave a client
directory as a default — a default is what put Overspray's photos here.

**Never `git add -A` without reading `git status` first.** That is how the
Facebook tooling ended up inside commits about the ceramic coating film. Stage
deliberately: `git add www tools docs`.

**One port per project**, so two dev servers never fight:

| Port | Project |
|---|---|
| 8788 | **formulamobile** (this repo) |
| 5173 | premier-ppf |
| 5199 | highend-auto-ppf |
| 5210 | protection-lab |

Serve this one with:

```bash
cd www && python -m http.server 8788
```

## Deployment

Vercel serves the **repo root**, and this repo's site lives in `www/` — that is
why the first deploy returned `404: NOT_FOUND` with nothing but a Vercel error
page. Two ways to fix it; the repo now does the first:

1. **Root `vercel.json`** with `"outputDirectory": "www"` — committed, works on
   the next push, no dashboard change needed. This is the one in force.
2. Vercel dashboard → Settings → Build & Deployment → **Root Directory = `www`**.
   Then `www/vercel.json` becomes authoritative instead.

Don't do both and let them drift. The root file wins; `www/vercel.json` is kept
only so option 2 still works if you ever switch.

`.vercelignore` keeps `site/`, `docs/`, `tools/` and `facebook-photos/` out of
the upload — 34 MB of working material that has no business on the CDN.
