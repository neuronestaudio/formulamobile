# Formula Mobile Car Detailing — site snapshot

A complete capture of the live site at **https://formulamobilecardetailing.com.au** taken **2 Aug 2026**, kept as the reference base for the rebuild/transfer.

## What's here

| Path | Contents |
|---|---|
| `site/` | Byte-exact mirror of the live site — 6 pages, 64 assets (~6.5 MB) |
| `docs/AUDIT.md` | Front-end / back-end audit of the existing site |
| `docs/mirror-manifest.json` | Every URL captured, plus external refs and dead links |
| `tools/mirror.py` | The crawler used to produce `site/` (re-runnable) |
| `tools/serve.py` | Local static server that resolves extensionless URLs like production |

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
