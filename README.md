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

### Glassmorphism

Every surface — cards, nav, form fields, quotes, FAQ, footer, suburb chips, the mobile call bar — is frosted glass, calibrated against Glossedout's heaviest treatment (`blur(24px) saturate(185%)`).

The part that actually matters is **the ambient light field**. Glass is a refraction effect: over flat black, `backdrop-filter` renders as a marginally lighter rectangle and nothing more. So `body::before` lays down five large, heavily-blurred colour pools — brand red, a cool blue, a violet, a teal — fixed to the viewport and drifting on a 34s cycle. Panels then shift against that light as the page scrolls, which is what makes the blur read as glass rather than as opacity.

Two supporting details: `saturate(180%)` pulls the ambient colour *through* the panel instead of greying it out, and each card carries a top-down `::after` sheen that reads as pane thickness. Tokens live in `:root` as `--glass-bg`, `--glass-brd`, `--glass-blur`, `--glass-inset`, `--glass-drop`.

The drift respects `prefers-reduced-motion`.

## The hero: carbon-fibre splash → the service carousel

The homepage opens on a woven carbon-fibre splash carrying the logo, which dissolves into the **same coverflow carousel** as `/services/select/` — that carousel *is* the hero.

Two rules govern it:

- **It is not a scroll trap.** The splash resolves on a 2.1s timer, and scroll / click / key / touch all skip it instantly. The carousel itself runs without `data-select-lock`, so the wheel belongs to the page and the visitor can scroll straight past into the rest of it. (`.sel` is `overflow:hidden` + `overscroll-behavior:none`; the inline variant has to undo both, or the page silently refuses to scroll.)
- **The splash plays once per session** (`sessionStorage`). A logo animation is charming the first time and an obstacle the fourth, so return views land straight on the carousel.

Because the wheel isn't captured, the hero carousel autoplays (`data-select-auto="4600"`) and stops permanently on the first real interaction — routed through `touched()`, which every input path already calls. It pauses while off-screen or backgrounded.

The markup comes from one `carousel_html(inline=…)` function shared with the standalone page, so the coverflow maths, glass and background crossfade can't drift apart.

`prefers-reduced-motion` skips the splash animation and the autoplay entirely.

> **Note:** this replaced the Tesla `dx-splash` hero. `assets/js/splash.js` is still in the repo, unreferenced, with its full write-up — the mechanic is a good fit for the planned 3-part coating parallax section.

## The previous hero: Tesla's `dx-splash`, rebuilt

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

## Lead-gen infrastructure

Ported from [Glossedout](https://github.com/neuronestaudio/Glossedout) — same architecture, vanilla JS instead of React/TS so it needs no build step.

| File | Ported from | Does |
|---|---|---|
| `assets/js/attribution.js` | `src/lib/attribution.ts` | First-touch capture of 10 ad params + landing page + referrer |
| `assets/js/tracking.js` | `src/lib/gtm.ts` | `dataLayer` pushes: phone/email CTAs, scroll depth, dwell, key-page views |
| `assets/js/lead-form.js` | submit path in `QuoteForm.tsx` | Posts the lead to the GHL webhook, then fires the conversion |
| FAQ accordion (in `build_site.py`) | `src/components/FAQAccordion.tsx` | Native `<details>` accordion on the home and services pages |

**First-touch, gap-fill only.** The record is written on the first visit and afterwards only *filled in* — a field holding a value is never overwritten, and `first_landing_page` is never replaced. A later untagged visit therefore can't erase what a tagged visit recorded, which is the usual way naive implementations lose attribution. Verified: landing tagged `utm_source=google&gclid=…`, then revisiting untagged, then arriving with `fbclid` + `utm_source=facebook` → `fbclid` fills in, `utm_source` stays `google`.

**The conversion is gated on the CRM.** `generate_lead` fires only after the webhook returns 2xx, so a conversion reported to Google Ads or Meta always corresponds to a lead the CRM actually holds. Verified both ways:

| Webhook | Events fired | Result |
|---|---|---|
| `200` | `quote_form_submit`, `generate_lead` | → `/thank-you/` |
| `500` | *none* | stays on `/contact/`, retry message, input preserved |

### Configure before launch

Three constants at the top of [tools/build_site.py](tools/build_site.py). Empty is a safe state, not a broken one — no GTM container is injected, and the form falls back to its native post rather than firing a fetch into nowhere.

```python
GTM_ID          = ""   # GTM-XXXXXXX
GHL_WEBHOOK     = ""   # Formula's OWN inbound webhook
GADS_CONVERSION = ""   # AW-XXXXXXXXX/AbCdEfGhIj
```

> **`GHL_WEBHOOK` must be Formula's own webhook.** Copying the URL out of the Glossedout source would deliver Formula's leads into a different business's CRM.

Two things that bite after the URL is set:

- **GHL needs a custom field per attribution param**, or the webhook accepts the payload and silently drops anything unmapped. The payload sends 12: `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `gclid`, `gbraid`, `wbraid`, `fbclid`, `msclkid`, `first_landing_page`, `referrer` — plus `submission_id`.
- **The endpoint must answer the CORS preflight.** A cross-origin JSON POST sends `OPTIONS` first; without `Access-Control-Allow-Origin` the browser blocks the send and every lead fails.

### Three deliberate divergences from Glossedout

- **`referrer` is captured here.** Your architecture diagram lists it, but `attribution.ts` doesn't implement it. Without it, an untagged organic or referral visit is indistinguishable from direct. Only *external* referrers are stored — internal navigation would otherwise overwrite the real source on the second pageview.
- **The FAQ ships with `FAQPage` schema.** Glossedout's accordion has none, so its Q&As can never surface as rich results. It's also built on native `<details>`/`<summary>` rather than div-and-onclick, so it is keyboard-operable and works with JS disabled.
- **Key-page events are derived from the URL shape** (`/services/*`, `/mobile-car-detailing/*`) rather than Glossedout's hardcoded path list, so all 44 suburb pages and 7 service pages are covered without maintaining an array.

### Still to build (offline layer)

The CRM → ad-platform feedback loop in the diagram is configuration in GHL and the ad accounts, not site code: pipeline stages (Qualified / Booked / Completed / Revenue) feeding Google Ads **Enhanced Conversions / Offline Conversion Import** via `gclid`/`gbraid`/`wbraid`, and Meta **CAPI/CRM events**. The site's job is capturing and passing the click IDs, which it now does.

## Still needed before launch

- **Pricing.** The old site published none, so none was invented. Needs to come from the client.
- **CRM webhook + GTM container.** Set `GHL_WEBHOOK`, `GTM_ID` and `GADS_CONVERSION` in `tools/build_site.py`, create the GHL custom fields, and **confirm the destination inbox**. See "Lead-gen infrastructure" above.
- **Privacy policy** copy — `/privacy/` is a placeholder.
- **Real photos of their own work.** Their Facebook page has them (branded van, AMG GT, Corvette, XC90) but only 160px thumbnails are reachable publicly — see [docs/FACEBOOK-PHOTOS.md](docs/FACEBOOK-PHOTOS.md) for the two routes that work. Before/after pairs remain the single most persuasive asset they are not showing (audit 5.10).
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
