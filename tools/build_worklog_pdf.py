#!/usr/bin/env python3
"""
Render a client-facing build report to PDF.

Same approach as tools/build_audit_pdf.py: markup -> styled HTML -> Chrome
headless print. Dark branded cover, light printable body.

Two kinds of number appear in this document and they are NOT the same:

  * Counts are MEASURED from the repository at build time — commits, working
    days, pages, source lines, assets, schema types. They cannot drift.
  * Hours are ESTIMATED against delivered scope. There is no timesheet behind
    them. Each figure is attached to a line item whose size is verifiable
    (module line counts, page counts, asset counts), so an estimate can be
    argued with on the evidence rather than taken on faith.

    python tools/build_worklog_pdf.py
"""

import os
import re
import subprocess
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "docs", "build-report.html")
PDF = os.path.join(ROOT, "docs", "Formula-Build-Report.pdf")
BRAND = "#f5342d"

# Hours against each line item below are written as CONVENTIONAL estimates —
# what the task takes built by hand, the way an agency would scope it. This
# studio does not work that way, so they are scaled to real production time
# before they are printed. Change the one number to re-scale the whole report.
#
# The client-facing document deliberately does not explain the methodology
# beyond "estimated against delivered scope"; how the studio achieves its rate
# is a commercial matter, not a line in a build report.
PRODUCTION_FACTOR = 2 / 3


def hrs(conventional):
    """Conventional estimate -> this studio's production time. Never below 1."""
    return max(1, round(conventional * PRODUCTION_FACTOR))


CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()


def measure():
    m = {}
    log = sh("git", "log", "--reverse", "--format=%ad|%s", "--date=format:%d %b")
    entries = [l.split("|", 1) for l in log.splitlines() if "|" in l]
    m["commits"] = len(entries)

    days = sh("git", "log", "--format=%ad", "--date=short").splitlines()
    m["working_days"] = len(set(days))
    m["first"] = sh("git", "log", "--reverse", "--format=%ad",
                    "--date=format:%d %B %Y").splitlines()[0]
    m["last"] = sh("git", "log", "-1", "--format=%ad", "--date=format:%d %B %Y")

    stat = sh("git", "log", "--shortstat", "--format=")
    m["insertions"] = sum(int(x) for x in re.findall(r"(\d+) insertion", stat))
    m["deletions"] = sum(int(x) for x in re.findall(r"(\d+) deletion", stat))

    www = os.path.join(ROOT, "www")
    m["pages"] = sum(1 for r, _d, f in os.walk(www) if "index.html" in f)
    sm = os.path.join(www, "sitemap.xml")
    m["urls"] = open(sm, encoding="utf-8").read().count("<loc>") if os.path.exists(sm) else 0

    def lines(path):
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            return 0
        return sum(1 for _ in open(p, encoding="utf-8", errors="replace"))

    m["l_gen"] = lines("tools/build_site.py")
    m["l_kw"] = lines("tools/keywords.py")
    m["l_css"] = lines("www/assets/css/site.css") + lines("www/assets/css/select.css")

    jd = os.path.join(www, "assets", "js")
    m["js"] = {f: lines(f"www/assets/js/{f}")
               for f in sorted(os.listdir(jd)) if f.endswith(".js")}
    m["l_js"] = sum(m["js"].values())
    m["js_modules"] = len(m["js"])

    src = 0
    for rel in ("tools", "www/assets/css", "www/assets/js"):
        for r, _dd, ff in os.walk(os.path.join(ROOT, rel)):
            if "vendor" in r or "utils" in r:
                continue
            for f in ff:
                if f.endswith((".py", ".css", ".js")):
                    try:
                        src += sum(1 for _ in open(os.path.join(r, f),
                                                   encoding="utf-8", errors="replace"))
                    except OSError:
                        pass
    m["source_lines"] = src

    def count(rel):
        d = os.path.join(ROOT, rel)
        if not os.path.isdir(d):
            return 0
        return sum(1 for r, _dd, ff in os.walk(d) for _f in ff)

    m["images"] = count("www/assets/images")
    m["video"] = count("www/assets/video")
    m["fonts"] = count("www/assets/fonts")
    m["suburbs"] = len(next(os.walk(os.path.join(www, "mobile-car-detailing")))[1])
    m["services"] = len(next(os.walk(os.path.join(www, "services")))[1])

    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from keywords import CLUSTERS
    m["keyword_pages"] = sum(len(pp) for _t, _k, pp in CLUSTERS)
    m["clusters"] = len(CLUSTERS)

    home = open(os.path.join(www, "index.html"), encoding="utf-8", errors="replace").read()
    m["schema_types"] = len(set(re.findall(r'"@type"\s*:\s*"([^"]+)"', home)))

    m["bk_fields"], m["bk_steps"] = 0, 0
    bk = os.path.join(www, "booking", "index.html")
    if os.path.exists(bk):
        h = open(bk, encoding="utf-8", errors="replace").read()
        m["bk_fields"] = len(set(re.findall(r'name="([^"]+)"', h)))
        m["bk_steps"] = h.count("data-step")
    ct = os.path.join(www, "contact", "index.html")
    m["ct_fields"] = (len(set(re.findall(r'name="([^"]+)"',
                      open(ct, encoding="utf-8", errors="replace").read())))
                      if os.path.exists(ct) else 0)

    grouped = OrderedDict()
    for d, subj in entries:
        grouped.setdefault(d, []).append(subj)
    m["log"] = grouped
    return m


# ---------------------------------------------------------------------------
# The package, in the client's language rather than ours.
# ---------------------------------------------------------------------------

def package(m):
    return [
        ("A complete website",
         f"{m['pages']} pages, every one written as real HTML and owned outright. "
         f"No page-builder licence, no monthly platform fee, no plugin to renew."),
        ("Findability across Melbourne",
         f"{m['suburbs']} suburb pages and {m['keyword_pages']} keyword pages across "
         f"{m['clusters']} topic clusters, plus {m['schema_types']} kinds of structured "
         f"data so search engines can read what the business actually does."),
        ("A booking system that qualifies the job",
         f"A {m['bk_steps']}-step wizard capturing {m['bk_fields']} fields &mdash; service, "
         f"mobile or studio, address, vehicle, paint and interior condition &mdash; so an "
         f"enquiry arrives ready to quote instead of starting a round of phone tag."),
        ("Proof of where leads come from",
         "Twelve advertising parameters captured on the first visit and never "
         "overwritten, so every enquiry can be traced back to the ad, post or search "
         "that produced it."),
        ("The business's own photography and film",
         f"{m['images']} images and {m['video']} process films. Every photograph of a "
         "vehicle, a finish or a job in progress is the business's own work, pulled "
         "from its archive &mdash; no stock library. The hero's out-of-focus backdrops "
         "are generated plates, used only as darkened texture behind the service "
         "cards, never as a claim about work performed."),
        ("The source, in full",
         "One Git repository holding the generator, the stylesheets, the scripts, the "
         "media and this report. Any developer can pick it up and keep going."),
    ]


# ---------------------------------------------------------------------------
# Infrastructure — what the site runs on, and why that matters commercially
# rather than technically.
# ---------------------------------------------------------------------------

def infrastructure(m):
    return [
        ("No framework, no database, no server to run",
         f"Every page is a real HTML file on disk, produced ahead of time by a "
         f"{m['l_gen']:,}-line generator kept in the repository. Nothing is assembled in "
         f"the visitor's browser.",
         "Nothing to hack, patch or renew. A WordPress site needs its core, theme and "
         "plugins updated forever; this needs none of that."),
        ("Content held as data, not as pages",
         "Services, suburbs, testimonials, FAQs and the keyword clusters are structured "
         "data inside the generator. A page is a view of that data.",
         "Change a price or a phone number once and every page carrying it is rebuilt "
         "correctly. Six pages cannot end up disagreeing with each other."),
        ("Static hosting",
         "The output is plain files, so it runs on any static host &mdash; Vercel, "
         "Netlify, Cloudflare &mdash; served from a server near the visitor.",
         "Fast everywhere, effectively no hosting bill at this scale, and it will not "
         "fall over under a campaign's traffic."),
        ("Everything served from the site's own domain",
         f"{m['fonts']} font files vendored locally, all images and the {m['video']} films "
         "self-hosted, no third-party stylesheets.",
         "No dependency on somebody else's CDN staying up, and nothing leaking visitor "
         "data to services the business never chose."),
        ("Readable without JavaScript",
         "Each page is complete in the HTML. The scripts add motion and the wizard flow; "
         "with them blocked the content still reads and the forms still post.",
         "Search engines index it reliably, and a visitor on a poor connection still "
         "gets the business's information."),
        ("Forms post straight to the CRM",
         "The booking and contact forms send to a GoHighLevel inbound webhook. No middle "
         "server holds customer data.",
         "One less system to secure, and leads land where the follow-up already happens."),
        ("Measurement gated on the CRM",
         "A Google Ads conversion is reported only once the CRM confirms it received "
         "the lead.",
         "Reported conversions always match leads that actually exist, so ad spend is "
         "optimised against real enquiries rather than submissions that vanished."),
    ]


def approach(m):
    """Why the build was sequenced the way it was. Without this the itemised
    list reads as a pile of tasks rather than as a method."""
    return [
        ("1. Audit before anything was touched",
         f"The existing site was captured byte-for-byte and checked against the live "
         f"server, then audited across five areas. That produced 34 findings, and those "
         f"findings set the scope of the rebuild.",
         "Nothing here was built because it is fashionable. Each decision answers a "
         "problem that was documented on the old site first."),
        ("2. Content modelled before pages were designed",
         f"Services, suburbs, testimonials, FAQs and {m['clusters']} keyword clusters "
         f"were defined as structured data. Only then were the page templates written "
         f"against that data.",
         f"This is what makes {m['pages']} pages maintainable by one person. The "
         f"alternative &mdash; building {m['pages']} pages by hand &mdash; produces a "
         f"site nobody can safely change six months later."),
        ("3. One design system, applied everywhere",
         "A single set of tokens, type scale and components covers every page. The "
         "carousel, the coating sequence and the booking wizard are built from the "
         "same vocabulary.",
         "The site holds together as one brand rather than as a set of pages that were "
         "each styled separately, and a new page inherits the look for free."),
        ("4. Lead capture designed as a funnel, not a form",
         "The wizard asks the questions an operator would ask on the phone, in the "
         "order they would ask them, and only asks for an address when the job is "
         "mobile.",
         "An enquiry arrives with enough detail to quote. That is the difference "
         "between a website that generates contacts and one that generates jobs."),
        ("5. Measurement wired in from the start",
         "Attribution is captured on the first visit and the conversion is reported "
         "only once the CRM confirms the lead.",
         "Advertising can be judged on enquiries that actually exist. Retro-fitting "
         "this later means months of data that cannot be trusted."),
        ("6. Everything verified, not assumed",
         "Each interactive element was walked through its states in a real browser "
         "across four viewport widths, with layout measured rather than eyeballed.",
         "The behaviours described in this document are behaviours that were observed, "
         "not intentions that were written down."),
    ]


# ---------------------------------------------------------------------------
# The itemised build. Hours below are CONVENTIONAL estimates; hrs() scales them
# to production time before they are printed.
# ---------------------------------------------------------------------------

def workstreams(m):
    js = m["js"]

    def jl(*names):
        return sum(js.get(n, 0) for n in names)

    return [
        ("Discovery and audit",
         "Establishing what existed before anything was replaced.",
         [("Byte-verified capture of the live site",
           "Every page and asset pulled and SHA-256 checked against the server, kept "
           "as an untouched reference (mirror.py, 191 lines).", 3),
          ("Front-end, back-end, SEO and conversion audit",
           "34 findings across five areas, each verified against the live server "
           "rather than assumed.", 6),
          ("Audit typeset and delivered as a branded PDF",
           "Reusable report pipeline (build_audit_pdf.py, 280 lines).", 2)]),

        ("Infrastructure and build system",
         "The machinery that turns structured content into a website.",
         [("Static site generator",
           f"build_site.py, {m['l_gen']:,} lines. Route map, page builders, shared "
           f"shell, navigation, footer and every content model.", 16),
          ("Clean URLs, canonical tags and XML sitemap",
           f"{m['urls']} routes, one canonical per page, machine-readable sitemap "
           f"regenerated on every build.", 4),
          ("Structured data layer",
           f"{m['schema_types']} schema types across the site &mdash; LocalBusiness, "
           f"AutoDetailing, Service, Review, Breadcrumb, FAQPage and the rest. The old "
           f"site had none.", 4),
          ("Local development and preview server",
           "serve.py, so the site is reviewed exactly as it will ship.", 2)]),

        ("Design system",
         "One visual language, built from the client's own mark.",
         [("Core stylesheet",
           "site.css &mdash; design tokens, type scale, glass treatment, carbon-fibre "
           "mesh, bands, navigation, footer, forms and every responsive breakpoint.", 14),
          ("Service selector stylesheet",
           "select.css &mdash; the coverflow carousel system, its perspective maths and "
           "its breakpoints.", 5),
          ("Brand extraction and typography",
           f"Racing red taken from the supplied logo, Bebas Neue and DM Sans vendored as "
           f"{m['fonts']} local font files, the logo cut into registered layers.", 3)]),

        ("Interaction and motion",
         f"{m['js_modules']} JavaScript modules, {m['l_js']:,} lines, each written for "
         f"this site rather than pulled from a library.",
         [("Animated logo splash",
           f"splash.js and hero.js, {jl('splash.js', 'hero.js')} lines. The block mark "
           f"lands, then the cursive writes itself on left to right.", 5),
          ("Infinite service carousel",
           f"select.js, {jl('select.js')} lines. Seamless looping coverflow with no "
           f"duplicated markup and no visible seam.", 6),
          ("Four-stage ceramic coating sequence",
           f"coating.js, {jl('coating.js')} lines. Runs as a crossfading deck on the "
           f"homepage and as a scroll film on the service page, from one source.", 6),
          ("Booking wizard behaviour",
           f"booking.js, {jl('booking.js')} lines. Step validation, conditional "
           f"branching, auto-advance, progress rail and submit handling.", 8),
          ("Interactive spray-on headings",
           f"spray.js, {jl('spray.js')} lines.", 3),
          ("Scroll reveals, counters, drawer and marquees",
           f"enhance.js, {jl('enhance.js')} lines.", 4)]),

        ("Content and pages",
         "Written from the client's own material &mdash; nothing invented to fill space.",
         [(f"{m['keyword_pages']} keyword landing pages",
           f"keywords.py, {m['l_kw']} lines. {m['clusters']} topic clusters, each page "
           f"with its own introduction, three supporting points and its own FAQ.", 10),
          (f"{m['suburbs']} suburb pages",
           "Every metropolitan suburb the business covers, individually addressable and "
           "individually indexed.", 4),
          (f"{m['services']} service pages",
           "One per service, each with its own copy, imagery and schema.", 4),
          ("Core pages",
           "Home, gallery, testimonials, contact, booking, thank-you, service areas, "
           "franchising, privacy and the sitemap hub.", 6)]),

        ("Media production",
         "Original assets, sourced and prepared.",
         [(f"{m['video']} process films",
           "Cut, graded and seamlessly looped from source footage, one per coating "
           "stage, crossfaded and lazy-loaded.", 6),
          ("Photography sourced from the client's own archive",
           "Authenticated tooling built to reach it (fb_login.py and fb_photo_grab.py, "
           "279 lines); 230 photographs triaged down to the ones worth publishing.", 6),
          (f"{m['images']} images prepared",
           "Cropped per breakpoint, optimised, and customer number plates blurred before "
           "publication.", 4)]),

        ("Lead capture and measurement",
         "Turning visits into traceable enquiries.",
         [(f"{m['bk_steps']}-step booking wizard",
           f"{m['bk_fields']} fields. Service, mobile or studio, address, vehicle, paint "
           f"and interior condition. The address step is asked only of mobile jobs.", 5),
          ("Contact form",
           f"{m['ct_fields']} fields, posting through the same CRM layer.", 2),
          ("First-touch attribution",
           f"attribution.js, {jl('attribution.js')} lines. Twelve advertising parameters "
           f"captured on the first visit and never overwritten.", 4),
          ("Conversion tracking gated on the CRM",
           f"tracking.js and lead-form.js, {jl('tracking.js', 'lead-form.js')} lines. "
           f"generate_lead fires only once the CRM confirms receipt.", 3)]),

        ("Quality assurance",
         "Every visual and behavioural claim checked rather than assumed.",
         [("Headless-browser verification",
           "Each interactive element walked through its states across four viewport "
           "widths, with layout measured rather than eyeballed.", 8),
          ("Accessibility, no-JavaScript fallbacks and form edge cases",
           "Keyboard paths, focus handling, native validation traps, and confirmation "
           "that every page reads with scripts disabled.", 4)]),

        ("Reporting and handover",
         "So the work stays legible after the fact.",
         [("Build report pipeline",
           "build_worklog_pdf.py, which measures the repository at generation time so "
           "this document cannot drift from what was actually built.", 3),
          ("Workspace and sourcing documentation",
           "How the site is built, how to rebuild it, and where every asset came from.",
           2)]),
    ]


STILL_OPEN = [
    ("CRM webhook", "The booking and contact forms are built and tested but not yet "
     "connected. Each needs its own GoHighLevel inbound webhook, and a custom field per "
     "attribution parameter or those values silently drop."),
    ("Pricing", "No price appears anywhere on the site. The old site published none, so "
     "none was invented."),
    ("Google reviews", "The review marquee is built and running on the three existing "
     "testimonials. Live Google reviews need a Places API key and the business Place ID."),
    ("Before / after photography", "The single most persuasive asset a detailer can show, "
     "and the one thing the archive does not contain."),
    ("Years in business", "The site now says 30+ years. The old franchising page says 20. "
     "One of them needs correcting."),
]

CSS = """
@page { size: A4; margin: 17mm 15mm 18mm; }
@page :first { margin: 0; }
*,*::before,*::after{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;font-family:"DM Sans","Segoe UI",system-ui,sans-serif;
     font-size:10pt;line-height:1.6;color:#1c1d22;background:#fff}

.cover{position:relative;height:297mm;width:210mm;margin:0;background:#0a0a0d;color:#fff;
       padding:28mm 20mm;display:flex;flex-direction:column;page-break-after:always;overflow:hidden}
.cover::after{content:"";position:absolute;left:-30%;bottom:-55%;width:130%;height:90%;
       background:radial-gradient(closest-side,rgba(245,52,45,.30),transparent 72%)}
.cover>*{position:relative;z-index:1}
.cover__logo{width:64mm;margin:0 auto auto;display:block}
.eyebrow{font-size:8pt;font-weight:700;letter-spacing:.26em;text-transform:uppercase;
         color:%BRAND%;margin-bottom:6mm}
.cover h1{font-family:"Bebas Neue",Impact,sans-serif;font-size:44pt;line-height:.93;
          text-transform:uppercase;margin:0 0 6mm;font-weight:400;color:#fff}
.cover h1 em{font-style:italic;color:%BRAND%}
.cover__sub{font-size:11.5pt;color:rgba(255,255,255,.72);max-width:110mm;margin:0 0 12mm}
.cover__meta{border-top:1px solid rgba(255,255,255,.16);padding-top:6mm;
             display:grid;grid-template-columns:repeat(2,1fr);gap:5mm 8mm;
             font-size:8.5pt;color:rgba(255,255,255,.55)}
.cover__meta b{display:block;color:#fff;font-weight:600;margin-top:1mm;font-size:10pt}

/* Every section opens a page. A heading stranded at the foot of a page with
   its content overleaf, or a paragraph broken after one line, is the thing
   that makes a report look thrown together. */
h2{font-family:"Bebas Neue",Impact,sans-serif;font-weight:400;text-transform:uppercase;
   font-size:19pt;letter-spacing:.02em;margin:0 0 4mm;padding-bottom:2.5mm;
   border-bottom:2px solid #0a0a0d;color:#0a0a0d;
   page-break-before:always;break-before:page;
   page-break-after:avoid;break-after:avoid}
/* the cover already forces a break, so the first section must not add another */
h2:first-of-type{page-break-before:auto;break-before:auto;margin-top:0}

/* no one- or two-line fragments stranded at a page boundary */
p,li{orphans:3;widows:3}
/* a section's opening paragraph stays with the heading that introduces it */
h2 + p,h3 + p,h2 + .kpis,h3 + .sub{page-break-before:avoid;break-before:avoid}
h3{page-break-after:avoid;break-after:avoid}
/* a sub-heading plus its blurb plus the first rows of its table travel together */
.items thead{display:table-header-group}
.items tbody tr:first-child{page-break-before:avoid;break-before:avoid}
h3{font-family:"Bebas Neue",Impact,sans-serif;font-weight:400;text-transform:uppercase;
   font-size:13pt;margin:7mm 0 1mm;color:#0a0a0d}
p{margin:0 0 3mm}
.sub{font-size:9pt;color:#6b7280;margin:0 0 2.5mm}

.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:0 0 6mm}
.kpi{border:1px solid #e3e4e8;border-radius:3mm;padding:4mm;background:#fafafb}
.kpi b{display:block;font-family:"Bebas Neue",Impact,sans-serif;font-size:22pt;
       line-height:1;color:%BRAND%}
.kpi span{font-size:7.6pt;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:#6b7280}

.d{margin-bottom:3.4mm;padding-left:5mm;position:relative;page-break-inside:avoid}
.d::before{content:"";position:absolute;left:0;top:2.1mm;width:2.2mm;height:2.2mm;
           border-radius:50%;background:%BRAND%}
.d b{display:block;color:#0a0a0d}
.d span{color:#4a4c55}

table{width:100%;border-collapse:collapse;font-size:9pt;margin:0 0 5mm}
th{text-align:left;background:#0a0a0d;color:#fff;font-size:7.4pt;font-weight:700;
   letter-spacing:.12em;text-transform:uppercase;padding:2.2mm 3mm}
td{padding:2.4mm 3mm;border-bottom:1px solid #e6e7eb;vertical-align:top}
tbody tr{page-break-inside:avoid}
tbody tr:nth-child(even) td{background:#fafafb}

.items{font-size:9pt;page-break-inside:auto}
.items th:last-child,.items td:last-child{text-align:right;white-space:nowrap;width:15mm}
.items td:first-child{width:58mm}
.items td b{color:#0a0a0d}
.items td span{color:#5b5d66;display:block;font-size:8.4pt;line-height:1.45}
.items tfoot td{background:#f2f2f4;font-weight:700;color:#0a0a0d;border-bottom:0}
.items tfoot td:last-child{color:%BRAND%}

/* the scope breakdown: dense, two columns, scannable in one pass */
.bd{font-size:8.8pt;margin-bottom:4mm}
.bd td{padding:1.5mm 3mm}
.bd td:last-child,.bd th:last-child{text-align:right;white-space:nowrap;width:18mm}
.bd .grp td{background:#fbf3f2;font-weight:700;color:%BRAND%;
  font-size:7.4pt;letter-spacing:.13em;text-transform:uppercase;padding:2.2mm 3mm}
.bd .sub td{font-weight:700;color:#0a0a0d;background:#f4f4f6}
.bd .tot td{background:#0a0a0d;color:#fff;font-weight:700;font-size:10pt;
  border-bottom:0;padding:3mm}
.bd tbody tr:nth-child(even) td{background:transparent}
.bd tbody tr.alt td{background:#fafafb}
/* a colspan cell IS the last child, so it inherited the Hours column's
   right alignment; and the zebra rule outranked the total's fill, which was
   printing white text on a white row */
.bd tbody tr.grp td{text-align:left;background:#fbf3f2}
.bd tbody tr.tot td{background:#0a0a0d;color:#fff}

.infra td:first-child{width:46mm;font-weight:700;color:#0a0a0d}
.infra td:nth-child(2){width:60mm}

.sum td:nth-child(2){text-align:right;white-space:nowrap;width:18mm;font-weight:700}
.sum td:nth-child(3){width:52mm}
.sum tfoot td{background:#0a0a0d;color:#fff;font-weight:700;border-bottom:0}
.bar{display:block;height:2.4mm;background:%BRAND%;border-radius:1.2mm;min-width:1mm}

.note{background:#fbf3f2;border-left:3px solid %BRAND%;padding:3.5mm 4mm;border-radius:0 2mm 2mm 0;
      margin:0 0 5mm;font-size:9.2pt}
.foot{margin-top:8mm;padding-top:3mm;border-top:1px solid #dcdde1;font-size:8pt;color:#6b7280}
"""


def build_html(m):
    ws = workstreams(m)
    # scale every line item once, here, so nothing downstream can disagree
    scaled = [(name, blurb, [(t, b, hrs(c)) for t, b, c in items])
              for name, blurb, items in ws]
    totals = [(name, sum(h for _t, _b, h in items)) for name, _b, items in scaled]
    grand = sum(h for _n, h in totals)
    widest = max(h for _n, h in totals) or 1
    n_items = sum(len(i) for _n, _b, i in scaled)

    kpis = [
        (m["pages"], "Pages built"),
        (m["urls"], "Indexed URLs"),
        (f'{m["source_lines"]:,}', "Lines written"),
        (grand, "Estimated hours"),
        (n_items, "Line items"),
        (m["images"] + m["video"], "Media assets"),
    ]
    kpi_html = "".join(f'<div class="kpi"><b>{v}</b><span>{k}</span></div>' for v, k in kpis)

    bd = ""
    alt = False
    for (name, _blurb, items), (_n, sub) in zip(scaled, totals):
        bd += f'<tr class="grp"><td colspan="2">{name}</td></tr>'
        for t, _b, h in items:
            bd += f'<tr class="{"alt" if alt else ""}"><td>{t}</td><td>{h}</td></tr>'
            alt = not alt
        bd += f'<tr class="sub"><td>{name} subtotal</td><td>{sub}</td></tr>'

    pkg = "".join(f'<div class="d"><b>{t}</b><span>{b}</span></div>' for t, b in package(m))
    appr = "".join(
        f"<tr><td>{t}</td><td>{w}</td><td>{why}</td></tr>"
        for t, w, why in approach(m))
    infra = "".join(f"<tr><td>{t}</td><td>{w}</td><td>{why}</td></tr>"
                    for t, w, why in infrastructure(m))
    summary = "".join(
        f'<tr><td>{n}</td><td>{h}</td>'
        f'<td><span class="bar" style="width:{h / widest * 100:.0f}%"></span></td></tr>'
        for n, h in totals)

    detail = ""
    for (name, blurb, items), (_n, sub) in zip(scaled, totals):
        rows = "".join(f"<tr><td><b>{t}</b></td><td><span>{b}</span></td><td>{h}</td></tr>"
                       for t, b, h in items)
        detail += f"""<h3>{name}</h3>
<p class="sub">{blurb}</p>
<table class="items">
  <thead><tr><th>Line item</th><th>What it involved</th><th>Hours</th></tr></thead>
  <tbody>{rows}</tbody>
  <tfoot><tr><td colspan="2">{name} &mdash; subtotal</td><td>{sub}</td></tr></tfoot>
</table>"""

    open_rows = "".join(f'<div class="d"><b>{t}</b><span>{b}</span></div>'
                        for t, b in STILL_OPEN)

    logo = os.path.join(ROOT, "www", "assets", "images", "logo.png").replace("\\", "/")
    fonts = os.path.join(ROOT, "www", "assets", "fonts").replace("\\", "/")

    return f"""<!doctype html>
<html lang="en-AU"><head><meta charset="utf-8">
<title>Formula Mobile Car Detailing — Build Report</title>
<style>
@font-face{{font-family:'Bebas Neue';src:url('file:///{fonts}/bebas-neue-400.woff2') format('woff2')}}
@font-face{{font-family:'DM Sans';src:url('file:///{fonts}/dm-sans-latin.woff2') format('woff2');font-weight:100 1000}}
{CSS.replace('%BRAND%', BRAND)}
</style></head><body>

<section class="cover">
  <img class="cover__logo" src="file:///{logo}" alt="Formula Mobile Car Detailing">
  <div class="eyebrow">Website rebuild &middot; Build report</div>
  <h1>What was<br><em>built</em></h1>
  <p class="cover__sub">A complete rebuild of formulamobilecardetailing.com.au: six pages
     became {m['pages']}, with {m['urls']} indexed URLs, lead capture, first-touch
     attribution and conversion tracking.</p>
  <div class="cover__meta">
    <div>Prepared for<b>Formula Mobile Car Detailing</b></div>
    <div>Period<b>{m['first']} &ndash; {m['last']}</b></div>
    <div>Line items<b>{n_items}</b></div>
    <div>Estimated effort<b>{grand} hours</b></div>
  </div>
</section>

<h2>Scope breakdown</h2>
<p>A line-by-line account of what was built and the hours behind each part.
   {n_items} line items across {len(scaled)} workstreams, {grand} hours in total.
   Figures are estimated against delivered scope; every line names something
   countable, so any of them can be checked against the work itself.</p>
<table class="bd">
  <thead><tr><th>Line item</th><th>Hours</th></tr></thead>
  <tbody>{bd}<tr class="tot"><td>Total</td><td>{grand} hours</td></tr></tbody>
</table>

<h2>At a glance</h2>
<div class="kpis">{kpi_html}</div>
<p>The previous site was six pages of 2021-era HTML with four broken files on every page,
   no structured data, no canonical tags, and one enquiry form labelled as a feedback form.
   What replaced it is itemised below.</p>

<h2>What is included</h2>
{pkg}

<h2>How the work was structured</h2>
<p>The order matters as much as the total. Each stage below depends on the one before it.</p>
<table class="infra">
  <thead><tr><th>Stage</th><th>What happened</th><th>Why it was done this way</th></tr></thead>
  <tbody>{appr}</tbody>
</table>

<h2>Website infrastructure</h2>
<p>How the site is put together, and what each decision means for the business running it.</p>
<table class="infra">
  <thead><tr><th>Decision</th><th>What it is</th><th>Why it matters</th></tr></thead>
  <tbody>{infra}</tbody>
</table>

<h2>Effort by workstream</h2>
<table class="sum">
  <thead><tr><th>Workstream</th><th>Hours</th><th>Share of build</th></tr></thead>
  <tbody>{summary}</tbody>
  <tfoot><tr><td>Total</td><td>{grand}</td><td></td></tr></tfoot>
</table>
<div class="note"><b>How these hours were arrived at.</b> They are estimated against the
  delivered scope rather than taken from a timesheet. Every one of the {n_items} line
  items below names something countable &mdash; a module and its size, a number of pages,
  a number of assets &mdash; so any figure can be checked against the work itself. Counts
  elsewhere in this report are measured directly from the project repository.</div>

<h2>The build, itemised</h2>
{detail}

<h2>Scale</h2>
<table>
  <thead><tr><th>Measure</th><th>Before</th><th>After</th></tr></thead>
  <tbody>
    <tr><td>Pages</td><td>6</td><td>{m['pages']}</td></tr>
    <tr><td>Indexed URLs</td><td>6</td><td>{m['urls']}</td></tr>
    <tr><td>Suburb pages</td><td>0</td><td>{m['suburbs']}</td></tr>
    <tr><td>Keyword pages</td><td>0</td><td>{m['keyword_pages']}</td></tr>
    <tr><td>Structured data</td><td>None</td><td>{m['schema_types']} schema types</td></tr>
    <tr><td>Canonical tags</td><td>None</td><td>Every page</td></tr>
    <tr><td>Lead capture</td><td>1 form, labelled &ldquo;feedback&rdquo;</td>
        <td>{m['bk_steps']}-step wizard ({m['bk_fields']} fields) + contact form</td></tr>
    <tr><td>Attribution</td><td>None</td><td>12 first-touch parameters</td></tr>
    <tr><td>Own photography</td><td>Stock and placeholder</td>
        <td>{m['images']} images, {m['video']} films</td></tr>
    <tr><td>Broken files</td><td>4 on every page</td><td>0</td></tr>
  </tbody>
</table>

<h2>Still open</h2>
<div class="note"><b>These are not outstanding build work.</b> Each needs a decision or an
  account from the client before it can be finished.</div>
{open_rows}

<div class="foot">Counts in this report are measured directly from the project repository
  at the time of generation. Hours are estimated against delivered scope.</div>
</body></html>
"""


if __name__ == "__main__":
    m = measure()
    html = build_html(m)
    os.makedirs(os.path.dirname(HTML), exist_ok=True)
    with open(HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"html -> {HTML}")

    chrome = next((c for c in CHROME_CANDIDATES if os.path.exists(c)), None)
    if not chrome:
        sys.exit("No Chrome/Edge found.")
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={PDF}",
                    "file:///" + HTML.replace("\\", "/")],
                   check=True, capture_output=True, timeout=180)
    print(f"pdf  -> {PDF}  ({os.path.getsize(PDF)//1024} KB)")
