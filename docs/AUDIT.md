# Formula Mobile Car Detailing — site audit

**Audited:** 2 Aug 2026 · **Target:** https://formulamobilecardetailing.com.au · **Basis:** the byte-exact capture in `site/` plus live server probing.

Every claim below was verified against the live server. Findings that looked bad on first pass but tested clean are listed in [What's actually fine](#whats-actually-fine) so the pitch doesn't overreach.

---

## Executive summary

The site is a 2021–2022-era static build (Apache/PHP, Bootstrap 3, jQuery) that has been left untouched for roughly four years. The **hosting layer is in better shape than expected** — HTTP/2, TLS 1.3, gzip and a valid certificate are all live. The problems are in the build itself and in what the site *doesn't do*.

Three things matter commercially:

1. **The site is quietly broken.** Four CSS/JS files referenced on every page return 404, jQuery is loaded twice on the homepage in a way that breaks Bootstrap's JavaScript, and the contact-page map points at the middle of the Indian Ocean instead of Melbourne.
2. **It is close to invisible to local search.** No structured data, no canonical tags, no suburb pages, and an H1 that never once says "car detailing" or "Melbourne". For a *mobile* detailer whose entire market is geographic, this is the single largest missed opportunity.
3. **There is a lead flow — but it is working against itself.** A real enquiry form exists on `/contact`, with reCAPTCHA correctly wired and firing. The problem is how it's positioned: it sits on one page only, the copy above it invites *feedback* rather than a booking, and it captures no service and no vehicle, so nothing that arrives can be quoted without a call back. Add no pricing and no booking option, and a customer who is ready to buy is given no obvious way to do it.

The underlying content is genuinely good — the service descriptions have real technical depth. This is a presentation, findability and conversion problem, not a "start from nothing" problem.

---

## 1. Broken in production — Critical

| # | Finding | Impact |
|---|---|---|
| 1.1 | **Four referenced files 404 on every page:** `snavvy.css`, `assets/css/style.css`, `assets/css/media.css`, `js/core.js`. `js/core.js` is script-tagged on all six pages. | Styling and behaviour the original developer wrote are simply absent. Every page load fires four failed requests. Whatever `core.js` did, it has not run since the files went missing. |
| 1.2 | **jQuery is loaded twice on the homepage.** All pages load jQuery 1.12.4 from `ajax.googleapis.com`; the homepage then loads jQuery 3.2.1 locally *after* `bootstrap.min.js`. The second load replaces `window.jQuery`, orphaning every plugin bound to the first. | Bootstrap's JS components on the homepage are bound to a jQuery instance that no longer exists. Silent, intermittent breakage — the classic "sometimes the menu doesn't work" bug. |
| 1.3 | **~15 further images 404**, referenced from inside CSS: `assets/images/patterns/overlay1-10.png`, `blank.gif`, `camera-loader.gif`, `images/call-sec.jpg`, `images/arrorw-select.png`. | Slider overlays and loading states never render. The slider has no loading indicator. |
| 1.4 | **The contact-page Google Map does not show the business.** The embed is centred on `-21.19, 95.47` — open ocean west of Australia — at country-level zoom, with the place name literally set to "Australia". (Locale params `1sen!2snp` suggest it was never localised past the offshore build.) | A visitor on the Contact page trying to confirm the business is local sees a map of the entire continent. Actively erodes trust. |
| 1.5 | **The Facebook icon links to `https://www.facebook.com/`** — Facebook's own homepage, not a business page. | Every social click is a dead-end and a lost visitor. |

## 2. Performance — High

Server config is fine; the payload is not.

| # | Finding | Detail |
|---|---|---|
| 2.1 | **No cache policy on static assets.** | `Cache-Control`, `Expires` and `ETag` are all absent. Only `Last-Modified` is sent. Every repeat visitor re-validates every asset instead of serving from cache — on a 6.5 MB site that is the difference between an instant second visit and another full round-trip set. Lowest-effort, highest-return fix on the list. |
| 2.2 | **5.56 MB of raster images across 41 files.** | Largest single image 563 KB. The four slider JPGs alone total ~1.8 MB and load on the homepage. |
| 2.3 | **No modern image formats, no responsive sizing, no lazy loading.** | All JPEG/PNG. No WebP/AVIF, no `srcset`, no `loading="lazy"`. Mobile visitors download desktop-resolution images over mobile data — the exact audience a *mobile* detailing service is chasing. |
| 2.4 | **~448 KB of CSS + JS** across 16 files (250 KB CSS, 198 KB JS). | Includes a full Bootstrap 3 build, Modernizr, Camera slider, WOW.js, Animate.css and SimpleLightbox for what is a six-page brochure site. |
| 2.5 | **TTFB ~675 ms** on the homepage. | Slow for a static-content response. Suggests shared hosting with no caching layer. |

## 3. Security — High

| # | Finding | Detail |
|---|---|---|
| 3.1 | **No security headers at all.** | `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy` are all absent. The site can be framed for clickjacking and offers no transport-security guarantee. |
| 3.2 | **The `www` redirect drops to plaintext mid-chain.** | `https://www...` → **`http://`** (unencrypted) → `https://`. Every `www` visitor makes one cleartext hop, exposed to interception on hostile networks. Compounded by 3.1 — with no HSTS there is nothing to stop the downgrade. One-line Apache fix. |
| 3.3 | **jQuery 1.12.4 (2016) and 3.2.1 (2017).** | Both predate 3.5.0, which fixed the `jQuery.htmlPrefilter` XSS flaws (CVE-2020-11022 / CVE-2020-11023). |
| 3.4 | **Bootstrap 3.3.7 — end-of-life since July 2019.** | Carries known XSS issues in `data-*` attribute handling (CVE-2018-14041 and related). No security patches will ever be issued. |

## 4. SEO & discoverability — High

This is where the largest commercial upside sits.

| # | Finding | Impact |
|---|---|---|
| 4.1 | **No structured data anywhere.** No `LocalBusiness`, `Service`, `Review`, `AggregateRating` or `FAQ` schema. | The business is ineligible for review stars, service listings and rich results in Google. For a local service business this is the most valuable schema on the web, and none of it is implemented. |
| 4.2 | **No suburb or service-area pages.** The entire geographic footprint is the string "Metropolitan Melbourne". | Every "car detailing [suburb]" search — the highest-intent, highest-converting query class for a mobile operator — has nothing to rank. The service is mobile; the site is not built to prove it. |
| 4.3 | **No canonical tags on any page.** | Nothing consolidates duplicate URL variants (`www`/non-`www`, `/services` vs `/services?modal=ceramic`). |
| 4.4 | **The declared canonical contradicts the server.** `og:url` and every `sitemap.xml` entry point at `www.`, but `www.` 301-redirects to non-`www`. | The site tells Google its canonical home is a URL that redirects away. Split, self-contradicting signals. |
| 4.5 | **Homepage has four identical H1s**, all reading `Let UsTake Care of your Car` — note the missing space. | Four H1s dilute the signal, and the one heading Google weights most heavily contains neither "detailing" nor "Melbourne". |
| 4.6 | **Services page H1 is just "Our Services".** | No keyword, no geography, on the most commercially important page. |
| 4.7 | **Sitemap is stale and thin.** All `lastmod` dates are `2022-05-09`; generated by a free online generator. | Signals an abandoned site. |
| 4.8 | **Six pages total, no blog or content layer.** Nine images have empty `alt`; four `alt` texts read "detaling". | Almost no surface area to rank for anything beyond the brand name. |

## 5. Conversion & content — High

| # | Finding | Impact |
|---|---|---|
| 5.1 | **No pricing anywhere on the site.** | High-intent visitors comparing detailers leave to find someone who publishes numbers. |
| 5.2 | **The site's only lead form is introduced as a feedback form.** The copy directly above it reads, verbatim: *"If you have some feedback please fill the form."* | This is the entire lead-capture mechanism on the site, and it is labelled as the one thing that isn't a sale. A visitor ready to book has no signal that this is where to ask. The highest-intent visitors are the ones most likely to skip it. |
| 5.3 | **One form, on one page.** `/contact` is the only page on the site with a form. The homepage, all six service descriptions, the gallery and the franchising page have none. | Every enquiry has to survive a navigation step to convert. The services page — where intent peaks — offers "Read More" eight times and "Contact Us" twice. |
| 5.4 | **The form captures no service and no vehicle.** Fields are First Name, Last Name, Address, Phone, E-mail, Comments. Nothing identifies what the customer wants or what they drive. | Nothing that arrives can be quoted or scheduled without a call back, so every lead costs an extra round trip. Meanwhile a full street address is demanded at first touch, before any value has been exchanged. |
| 5.5 | **No client-side validation, and no labels at all.** All fields are plain `type="text"` — no `required`, no `type="email"`, no `type="tel"`. There are **zero `<label>` elements**; all six fields rely on placeholders alone. Posts to `/response`. | Malformed and incomplete submissions with no inline feedback. Placeholders vanish the moment someone types, so anyone who pauses loses the prompt, and screen readers handle them poorly. **Where these enquiries are delivered is unverified** — confirm before any migration, or leads will drop silently. |
| 5.6 | **No online booking and no quote flow.** The strings "Book Now", "Get a Quote" and "Request a Quote" appear nowhere on the site. | No capture outside business hours, and no self-service path for customers who would rather not phone. |
| 5.7 | **Footer contradicts itself.** "Our support available to help you 24 hours a day, seven days a week" sits directly above "Monday-friday: 6:30am to 6:30 pm / Saturday: 6:30am to 6:30 pm / **Sunday: Closed**". | Visible, unresolved contradiction in the site furniture on every page. |
| 5.8 | **Copyright reads 2021.** | Five years stale on every page. The clearest possible "this business may not still be trading" signal. |
| 5.9 | **Three static testimonials, no live reviews.** No Google Reviews integration, no star ratings, no schema. One contains the typo "Highly Recomended". | Social proof is unverifiable and frozen. Competitors surfacing live Google ratings win the comparison by default. |
| 5.10 | **Gallery is eight images with no before/after pairing.** | Paint correction and overspray removal are inherently before/after services. The single most persuasive asset this business could show, and it isn't shown. |

---

## What's actually fine

Worth knowing so the pitch stays credible — these were tested and passed:

- **HTTP/2 and TLS 1.3** both negotiate correctly via ALPN.
- **gzip compression is enabled** on HTML and CSS (homepage 14.5 KB → 3.9 KB on the wire).
- **Valid Let's Encrypt certificate**, current through 24 Sep 2026, auto-renewing.
- **All six pages are valid UTF-8** — no encoding corruption.
- **`viewport` meta is present** and there are ~25 media queries, so a responsive foundation exists.
- **Google Analytics 4 is installed and current** (`G-ZKYL0YQ0QZ`).
- **The contact form is live and functional.** It renders, reCAPTCHA v2 is correctly wired and firing, and it posts to a real server-side handler. The lead path exists — section 5 is about how it's positioned and what it captures, not about building one from scratch.
- **All 76 images carry an `alt` attribute** (9 are empty, but the attribute is there).
- **Per-page meta titles and descriptions are unique** and reasonably written.
- **The service content has real technical depth** — Mini/Full/Interior/Exterior detail, overspray removal, Graphene Pro 10H N1, Quartz 9H Pro, glass and interior coatings, and 3/4/5/6-stage paint correction. This is strong raw material and should carry across to the rebuild.
- **A second business line already exists** — the franchising page.

---

## Scope implied by the above

Grouped by how the work would realistically be sold.

**Stabilise** — resolve the four 404s, fix the double-jQuery conflict, correct the map embed, fix the Facebook link, update the copyright, resolve the hours contradiction, fix the two typos.

**Harden & accelerate** — add cache headers, add the security header set, fix the plaintext redirect hop, upgrade jQuery and move off end-of-life Bootstrap 3, compress and convert the 5.56 MB image library, add lazy loading and responsive sizing.

**Make it findable** — `LocalBusiness` / `Service` / `Review` / `FAQ` schema, canonical tags, reconcile the `www` canonical conflict, rewrite the heading hierarchy for keyword and geographic intent, build out suburb-level service-area pages, regenerate the sitemap.

**Make it sell** — the biggest wins here are cheap. Reframe the existing form from "feedback" to a quote request, add service and vehicle fields so enquiries arrive quotable, put a capture point on the service pages instead of only on `/contact`, and add real labels and validation. Then: publish pricing or price ranges, add an online booking option, *confirm where the form delivers*, integrate live Google Reviews, and rebuild the gallery around before/after pairs.

**Recover from the host first** — `response.php`, the `.php` page sources and `.htaccess` are not reachable over HTTP and must come off the cPanel/FTP account before anything is migrated. See the README.
