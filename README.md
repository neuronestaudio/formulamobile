# Formula Mobile Car Detailing

Rebuild of **formulamobilecardetailing.com.au**. The new site lives in `www/`; the byte-exact capture of the old one is kept in `site/` as the reference base.

## What's here

| Path | Contents |
|---|---|
| **`www/`** | **The new site — 62 pages, static, built by `tools/build_site.py`** |
| `site/` | Byte-exact mirror of the OLD live site — 6 pages, 63 assets (~6.5 MB) |
| `docs/AUDIT.md` | Front-end / back-end audit of the old site |
| `docs/mirror-manifest.json` | Every URL captured, plus external refs and dead links |
| `tools/build_site.py` | Generator for `www/` — edit content here, not in the HTML |
| `tools/mirror.py` | The crawler used to produce `site/` (re-runnable) |
| `tools/serve.py` | Local static server that resolves extensionless URLs like production |

Everything in `site/` was verified byte-identical to what the origin server returns (SHA-256 compared against live URLs at capture time).

---

# The new build (`www/`)

## Run it

```bash
python tools/build_site.py          # regenerate www/
cd www && python -m http.server 4321
# http://localhost:4321
```

`www/` is generated output. **Edit `tools/build_site.py` and rebuild** — hand-edits to `www/*.html` get overwritten.

## Architecture

Follows the [Premier Mobile Detailing](https://github.com/neuronestaudio/Premiermobiledetailing) build:

- **Route-per-directory** — every route is `<route>/index.html`, clean URLs, no extensions
- **All assets root-relative** (`/assets/…`) and local — no CDN dependencies at all
- **`vercel.json`** — clean URLs plus the cache and security headers the old site was missing

It departs from Premier in one way: Premier ships a rendered mirror of a React SPA (a 474 KB hydrating bundle). This is hand-authored static HTML with ~20 KB of CSS and ~8 KB of JS, so every page is real HTML with no hydration step.

## Design system

Premier's dark premium architecture, Formula's own brand colour.

| Token | Value | Note |
|---|---|---|
| `--bg` | `#0a0a0d` | near-black base |
| `--brand` | `#f5342d` | **Formula racing red**, lifted from the existing logo |
| Display | Bebas Neue | condensed, motorsport; italic `.slant` echoes the logo's skew |
| Body | DM Sans | vendored locally, latin subset |

Carbon-fibre hex mesh on raised bands, button sheen sweep, cursor-tracking card spotlights, scroll reveal and stat count-up — the Premier interaction layer, rebuilt in `assets/js/enhance.js`.

## The hero: Tesla's `dx-splash`, rebuilt

The scroll animation from [tesla.com/en_au/model3-choose](https://www.tesla.com/en_au/model3-choose), identified by instrumenting the live page in headless Chrome on 2 Aug 2026. See `assets/js/splash.js` for the full write-up.

The mechanism, and why the car appears to swap without moving:

- `.dx-splash` is only **~20px taller than the viewport** — that runway is a **trigger**, not a scrub track
- `.dx-splash__wrapper` is `position: sticky; top: 0`; the slides are `position: fixed`, stacked at identical coordinates
- Crossing the threshold flips **one class** (`dx-splash__active-slide-N`)
- CSS does the animation: `transition: opacity 0.5s ease-in-out`. **Only opacity animates — nothing translates or scales**
- Tesla's two renders are both 2880×1800 with the car in the same pixel position, `object-fit: cover`

So it is a **discrete state machine**, not a scroll-scrubbed animation — the fade always runs at the same speed regardless of scroll velocity. Tesla also disables the transition entirely under `prefers-reduced-motion`; this build does the same.

Our version generalises it to three slides (Full Detail / Paint Correction / Ceramic Coatings), driven by scroll, a switch button, clickable pips, and arrow keys.

> **Note on the art:** Tesla's effect is perfect because both renders are pre-registered. Formula's three hero shots are different cars at similar-but-not-identical framing, so it reads as a strong cinematic dissolve rather than a true in-place morph. Shooting (or compositing) three registered hero frames would take this the last 10%.

## What the audit findings this fixes

Directly addresses `docs/AUDIT.md`: `LocalBusiness`/`Service`/`Review`/`Breadcrumb` schema on every page (4.1), 44 suburb pages (4.2), canonical tags (4.3–4.4), one keyword+geo H1 per page (4.5–4.6), regenerated sitemap (4.7), security and cache headers via `vercel.json` (2.1, 3.1), self-updating copyright year (5.8), and correct hours with the 24/7 contradiction removed (5.7).

On the lead flow specifically (5.2–5.6): the form is now framed as **"Get a quote"** rather than an invitation for feedback, carries **service** and **vehicle** fields so enquiries arrive quotable, asks for a suburb instead of a full street address at first touch, and uses real `<label>` elements with `required`, `type="email"` and `type="tel"`. Every page also carries a persistent quote CTA and a sticky call bar on mobile, so capture no longer depends on reaching `/contact`.

## Still needed before launch

- **Pricing.** The old site published none, so none was invented. Needs to come from the client.
- **A form handler.** `/contact/` posts to `/thank-you/`; wire it to a real endpoint (Vercel function, Formspree, etc.) and **confirm the destination inbox**.
- **Privacy policy** copy — `/privacy/` is a placeholder.
- **Real before/after gallery pairs** — the single most persuasive asset this business isn't showing (audit 5.10).
- **Registered hero renders** for the splash, per the note above.

## Viewing the snapshot

The live server runs Apache with a rewrite mapping `/services` → `services.php`, so internal links are extensionless. Opening `site/index.html` straight off disk means nav links won't resolve. Use the shim:

```bash
python tools/serve.py        # http://localhost:8000
```

## Pages captured

| Live URL | File |
|---|---|
| `/` | `site/index.html` |
| `/services` | `site/services.html` |
| `/gallery` | `site/gallery.html` |
| `/testimonials` | `site/testimonials.html` |
| `/contact` | `site/contact.html` |
| `/franchising` | `site/franchising.html` |

The sitemap also lists `/services?modal=mini|interior|exterior|fulldetail|ceramic|correction`. These are not separate pages — they're query params that open a modal already present in `services.html`, so all six service descriptions are captured in that one file.

## Stack as captured

Static HTML rendered by PHP on Apache. jQuery 3.2.1, Bootstrap 3.3.7, Camera slider, WOW.js, Animate.css, SimpleLightbox. Google Analytics `G-ZKYL0YQ0QZ`. Contact form POSTs to `/response` (server-side PHP, **not** captured — see below) with Google reCAPTCHA v2.

## Not captured — needs to come from the host

These live server-side and can't be pulled over HTTP. Get them from the cPanel/FTP account before any migration:

- **`response.php`** — the contact form handler. Where enquiries are delivered is currently unknown; confirm the destination inbox before cutting over or leads will silently drop.
- The `.php` page sources and `.htaccess` rewrite rules.
- Any DNS/email config on the domain.

## Known-broken on the live site

Four files are referenced by the HTML but return 404 in production. They are absent from `site/` because they don't exist:

- `snavvy.css`
- `assets/css/style.css`
- `assets/css/media.css`
- `js/core.js`

Plus several images referenced from within CSS (`images/call-sec.jpg`, `assets/images/patterns/overlay1-10.png`, `assets/images/blank.gif`, `assets/images/camera-loader.gif`, `images/arrorw-select.png`). Full list in `docs/mirror-manifest.json`. Details in `docs/AUDIT.md`.

## External dependencies still hot-linked

`site/` references these off-site — they are not vendored, so the snapshot depends on them staying up:

- `maxcdn.bootstrapcdn.com` — Font Awesome 4.6.1
- `ajax.googleapis.com` — jQuery
- `www.google.com` — reCAPTCHA
- `www.googletagmanager.com` — Analytics
