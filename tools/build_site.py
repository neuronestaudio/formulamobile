#!/usr/bin/env python3
"""
Build the Formula Mobile Car Detailing static site into www/.

Architecture follows the Premier Mobile Detailing repo:
  - every route is <route>/index.html  (clean URLs, no extensions)
  - every asset reference is root-relative (/assets/...) so it serves anywhere
  - all assets local; no CDN dependencies

Content is sourced from the captured snapshot in site/ — service copy,
testimonials and contact details are the client's real words. Nothing is
invented. Pricing is deliberately absent because the old site published none;
it needs to come from the client before it goes on the page.
"""

import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "www")

SITE = "https://formulamobilecardetailing.com.au"
PHONE_DISPLAY = "1300 132 750"
PHONE_LINK = "1300132750"
EMAIL = "info@formulamobilecardetailing.com.au"
GA_ID = "G-ZKYL0YQ0QZ"

# --------------------------------------------------------------------------
# Lead-gen infrastructure — mirrors github.com/neuronestaudio/Glossedout
#
# All three are empty until the client's own accounts are wired up. Empty is a
# safe state, not a broken one:
#   - no GTM_ID       -> no container injected, dataLayer still populated
#   - no GHL_WEBHOOK  -> the form falls back to its native post rather than
#                        firing a fetch into nowhere and swallowing the lead
#   - no GADS_...     -> the gtag conversion is skipped, GTM can still fire it
#
# GHL_WEBHOOK MUST be Formula's own inbound webhook. Reusing the Glossed Out
# URL would deliver Formula's leads into a different business's CRM.
# --------------------------------------------------------------------------
GTM_ID = ""            # e.g. "GTM-XXXXXXX"
GHL_WEBHOOK = ""       # e.g. "https://services.leadconnectorhq.com/hooks/<id>/webhook-trigger/<id>"
GADS_CONVERSION = ""   # e.g. "AW-XXXXXXXXX/AbCdEfGhIjKlMnOp"

# --------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------

SPLASH = [
    {
        "img": "/assets/images/slider01.jpg",
        "tier": "Full Detail",
        "title": "Inside and out",
        "copy": "Engine bay, door jams, clay bar, hand polish, extraction through the "
                "carpets and leather conditioned. The whole vehicle, done properly.",
        "href": "/services/full-detail/",
    },
    {
        "img": "/assets/images/slider02.jpg",
        "tier": "Paint Correction",
        "title": "Swirls gone",
        "copy": "Three, four, five or six stage correction in our specialty studio — "
                "matched to the depth of the damage and the duco your manufacturer used.",
        "href": "/services/paint-correction/",
    },
    {
        "img": "/assets/images/slider03.jpg",
        "tier": "Ceramic Coatings",
        "title": "Sealed for years",
        "copy": "Graphene Pro 10H and Quartz 9H Pro. An industrial-grade polymer that "
                "chemically bonds to your duco and stays there.",
        "href": "/services/ceramic-coating/",
    },
]

SERVICES = [
    {
        "slug": "mini-detail",
        "name": "Mini Detail",
        "img": "/assets/images/services/img01.jpg",
        "blurb": "A pressure wash, shampoo and rinse, wheels and under-guards degreased, "
                 "chamois dried, interior vacuumed and windows cleaned inside and out.",
        "intro": "A mini detail or valet is the maintenance service — the one that keeps a "
                 "well-kept car well-kept. Available with or without a hand polish.",
        "groups": [
            ("A mini detail or valet consists of", [
                "Vehicle pressure washed first, shampooed and then pressure rinsed",
                "Wheels and under guards degreased and pressure washed",
                "Vehicle chamois dried",
                "Seats, carpets and cargo area vacuumed",
                "Dash wiped and blown with compressed air",
                "Windows cleaned inside and out",
                "Tyres glossed and plastics sealed",
            ]),
            ("Mini detail with hand polish adds", [
                "Paint work cleaned with a clay bar",
                "Paint work hand polished",
            ]),
        ],
    },
    {
        "slug": "full-detail",
        "name": "Full Detail",
        "img": "/assets/images/services/img11.jpg",
        "blurb": "The complete service. Engine bay degreased, clay bar, hand polish, "
                 "full interior extraction and leather conditioned.",
        "intro": "Everything the mini detail covers, plus the engine bay, door jams, clay "
                 "bar decontamination, a hand polish and a full interior extraction.",
        "groups": [
            ("A full detail consists of", [
                "Door jams cleaned",
                "Wheels and under guards degreased and pressure washed",
                "Engine bay degreased and pressure washed",
                "Vehicle washed and paint work cleaned with a clay bar",
                "Paint work chamois dried",
                "Paint work hand polished",
                "Tyres glossed and plastics sealed",
                "Door trims, dash, steering wheel, console, vents and visors detailed",
                "Ashtrays cleaned",
                "Seats, carpets, floor mats and cargo area cleaned with extraction",
                "Leather seats cleaned and conditioned",
                "Roof lining spot cleaned",
                "Windows cleaned inside and out",
            ]),
        ],
    },
    {
        "slug": "interior-detail",
        "name": "Interior Detail",
        "img": "/assets/images/services/img03.jpg",
        "blurb": "Specialised products and equipment across every interior surface — "
                 "carpet, mats, seats, wheel, dash, console, tints and mirrors.",
        "intro": "Interior car detailing involves using specialised products and equipment "
                 "to treat all interior surfaces. It goes beyond just making it look clean. "
                 "More than a spray and wipe, our mobile interior detailing uses A-grade "
                 "shampoos and cleaning agents to ensure that what you're sitting in is safe "
                 "for both you and your passengers.",
        "groups": [
            ("Our full interior detailing process consists of", [
                "Door jams cleaned",
                "Door trims, dash, steering wheel, console, visors and vents detailed",
                "Ashtrays cleaned",
                "Seats, carpets, floor mats and cargo area cleaned with extraction",
                "Leather seats cleaned and conditioned",
                "Roof lining spot cleaned",
                "Windows cleaned",
            ]),
        ],
    },
    {
        "slug": "exterior-detail",
        "name": "Exterior Detail",
        "img": "/assets/images/services/img05.jpg",
        "blurb": "A four stage process for brush marks, spider webbing, oxidised, dull "
                 "or plain neglected paint work.",
        "intro": "We specialise in surface damage that may need our 4 stage process. Whether "
                 "brush marks, spider webbing, oxidised dull or just plain neglected paint "
                 "work, we have a process to fix most situations.",
        "groups": [
            ("4 stage exterior detail process", [
                "Vehicle pressure washed first to remove loose dirt and grime",
                "Hand washed with car shampoo, then pressure rinsed",
                "Clay bar the paint work to deep clean all grime and foreign matter away",
                "Machine cut to remove scratches, spider webbing and dullness",
                "Machine glaze to de-swirl the surface and put back a deep gloss",
                "Hand polish with a quality liquid polish, wax or both to seal and protect",
            ]),
            ("Windows", [
                "The exterior of the windows can accumulate a build up of environmental "
                "pollution that normal window cleaning will not remove. We have a process "
                "that cleans the build up off the glass, leaving a smooth polished finish.",
            ]),
        ],
    },
    {
        "slug": "overspray-removal",
        "name": "Overspray Removal",
        "img": "/assets/images/services/img06.jpg",
        "blurb": "Industrial fallout, paint overspray, concrete, acid rain and tree sap "
                 "lifted off your duco.",
        "intro": "Overspray and industrial fallout caused by airborne particles of paint, "
                 "steel, dust, concrete, chemical and acid rain and tree sap are very "
                 "damaging to your vehicle's duco. These airborne emissions can be caused by "
                 "negligent work processes, accidental overspray or even vandalism.",
        "groups": [],
    },
    {
        "slug": "ceramic-coating",
        "name": "Ceramic Coatings",
        "img": "/assets/images/services/img07.jpg",
        "blurb": "Graphene Pro 10H N1, Quartz 9H Pro and Quartz 9H — industrial-grade "
                 "polymer sealers that chemically bond to your paint.",
        "intro": "Automotive ceramic coatings are made from an advanced industrial grade "
                 "liquid polymer sealer that chemically bonds to your vehicle's paint work. "
                 "The semi-permanent layer creates a hydro barrier between the finish of your "
                 "paint work and the elements.",
        "groups": [
            ("The advantages", [
                "Your vehicle stays cleaner for longer",
                "Easier to wash and dry",
                "Creates a deep glossy shine",
                "Protection against scratches and abrasions",
                "Protection against wash marks and swirls",
                "Protection against bird droppings and other nasties",
                "Minimal maintenance required",
            ]),
        ],
        "products": [
            ("Graphene Pro 10H N1", "World's first N1 nano coating. Nano-technology mixed "
             "with the properties of graphene. Up to 1000nm of protection.",
             ["10H hardness", "Up to 1000nm", "Lifetime"]),
            ("Quartz 9H Pro", "Grade 3 chemical resistance with multi-layer application to "
             "increase thickness. Up to 800nm of protection.",
             ["9H hardness", "Up to 800nm", "5 years"]),
            ("Quartz Ceramic Coating", "Enhances the reflective properties of the paint with "
             "a smooth, deep shine. Applicable to paint, metal and glass.",
             ["9H hardness", "Up to 800nm", "3 years"]),
            ("Interior Coating", "Hybrid solvent base for both fabric and leather. Protects "
             "against stains, dirt, contaminants, water and oil.",
             ["Leather + fabric", "150° repellency", "12 months"]),
        ],
    },
    {
        "slug": "paint-correction",
        "name": "Paint Correction",
        "img": "/assets/images/services/img02.jpg",
        "blurb": "Three to six stage correction in our specialty studio, matched to the "
                 "depth of the damage and the type of duco.",
        "intro": "Conducted in our specialty studio created for these applications. Paint "
                 "correction is a method applied to duco surfaces to eliminate most "
                 "imperfections. The method we use is tailored to the severity, depth of "
                 "damage, colour and the type of duco the manufacturer applied.",
        "groups": [
            ("What it removes", [
                "Swirl marks caused by a poor cut and polish",
                "Environmental damage — a build-up of pollution, rain and sun damage from "
                "being exposed to the elements and not garaged",
                "Marks, scuffs and scratches from general day to day usage",
            ]),
            ("Available as", [
                "3 stage process",
                "4 stage process",
                "5 stage process",
                "6 stage process",
            ]),
        ],
    },
]

# Backdrop + colour grade per service for the /services/select/ carousel.
# Only the four slider shots are large, so backdrops are blurred hard and each
# gets its own grade — the worlds differ, the accent stays Formula red.
SELECT_LOOKS = {
    "mini-detail":       ("/assets/images/gallery/03.jpg", "#27455f"),
    "full-detail":       ("/assets/images/slider01.jpg", "#3a3f4a"),
    "interior-detail":   ("/assets/images/gallery/04.jpg", "#6b4526"),
    "exterior-detail":   ("/assets/images/slider02.jpg", "#1d3a5e"),
    "overspray-removal": ("/assets/images/services/img06.jpg", "#1d4f47"),
    "ceramic-coating":   ("/assets/images/slider03.jpg", "#6b5320"),
    "paint-correction":  ("/assets/images/slider04.jpg", "#3f2a5e"),
}

TESTIMONIALS = [
    ("Service and attention to detail is what we look for when we get our clients cars "
     "detailed. Formula Mobile Car Detailing Melbourne provides this all the time, every "
     "time. Very friendly operators and very reliable. Highly recommended!",
     "GZM Automotive"),
    ("Thank you so much for doing such an amazing job detailing my van last week. I cannot "
     "believe you got rid of all those scratches on the duco, and the oil stains out of the "
     "seats. It is also very pleasant when someone arrives on time and does what they say "
     "they will do, in an efficient and timely manner.",
     "David from Elwood"),
    ("We have used several car detailers in the past, but Formula Mobile Car Detailing "
     "Melbourne is our preferred choice. They are a cut above everybody else. The service "
     "and finish they provide is exceptional!",
     "Preston Automatics and Differentials"),
]

# FAQ — ports the FAQAccordion pattern from Glossedout, with FAQPage schema
# added (theirs ships without it, so the Q&As never surface as rich results).
# Every answer is drawn from the client's own service copy in the snapshot;
# nothing about price or turnaround is invented, because the old site stated
# neither.
FAQS = [
    ("Do you come to me?",
     "Yes — we're fully mobile across metropolitan Melbourne. We bring our own "
     "water and power, so we can work at your home or your office and you don't "
     "need to go anywhere. Because everything is done onsite the process is "
     "completely transparent: you can watch the work happen."),
    ("What's the difference between a mini detail and a full detail?",
     "A mini detail is the maintenance service — pressure wash, shampoo and rinse, "
     "wheels and under-guards degreased, chamois dry, interior vacuumed, dash "
     "blown with compressed air, windows in and out, tyres glossed. A full detail "
     "adds the engine bay, door jams, a clay bar decontamination, a hand polish, "
     "and a full interior extraction through the seats, carpets, mats and cargo "
     "area with the leather cleaned and conditioned."),
    ("What is paint correction, and how many stages do I need?",
     "Paint correction removes swirl marks from a poor cut and polish, "
     "environmental damage from being left out in the elements, and the marks, "
     "scuffs and scratches of day-to-day use. We run 3, 4, 5 and 6 stage "
     "processes — which one your car needs depends on the severity and depth of "
     "the damage, the colour, and the type of duco the manufacturer applied. It's "
     "conducted in our specialty studio built for these applications."),
    ("How long does a ceramic coating last?",
     "It depends on the coating. Graphene Pro 10H N1 is our hardest — 10H, up to "
     "1000nm thick, and it lasts a lifetime. Quartz 9H Pro is 9H, up to 800nm, "
     "and lasts up to 5 years. Quartz Ceramic Coating is 9H, up to 800nm, around "
     "3 years. Our interior coating works on both leather and fabric and protects "
     "for up to 12 months."),
    ("Can you remove overspray or industrial fallout?",
     "Yes — it's one of our specialities. Airborne paint, steel, dust, concrete, "
     "chemical and acid rain and tree sap are all very damaging to your duco, "
     "whether they came from negligent work processes nearby, accidental "
     "overspray or vandalism. We have a process to lift them off the paint."),
    ("My paint looks dull and swirled. Can it be brought back?",
     "Usually, yes. We specialise in surface damage through our 4 stage exterior "
     "process — brush marks, spider webbing, oxidised dull or plain neglected "
     "paint work. The vehicle is pressure washed, hand washed and rinsed, clay "
     "barred, machine cut to remove the scratches and dullness, machine glazed to "
     "de-swirl and restore gloss, then hand polished to seal and protect."),
    ("Which suburbs do you service?",
     "Metropolitan Melbourne. If you're in the metro area we'll come to you — "
     "call 1300 132 750 and our operators will confirm."),
]


# Four stages of the ceramic coating process. Sourced from the client's own
# copy: the 4-stage exterior process (wash / clay / machine cut / machine
# glaze) and the ceramic coating page (industrial-grade liquid polymer sealer,
# chemical bond, semi-permanent hydro barrier). Nothing here is invented.
COATING_STAGES = [
    ("Decontaminate",
     "The vehicle is pressure washed to lift loose dirt and grime, hand washed "
     "with car shampoo, then pressure rinsed. Clay bar follows, deep cleaning "
     "grime and foreign matter out of the paint. A coating bonds to the surface "
     "it is laid on, so the surface has to be genuinely clean first."),
    ("Correct",
     "Machine cut removes scratches, spider webbing and dullness, then machine "
     "glaze de-swirls the surface and puts a deep gloss back. Whatever the paint "
     "looks like at this point is what the coating locks in — correction is not "
     "optional, it is the step that decides the result."),
    ("Coat",
     "An advanced industrial-grade liquid polymer sealer chemically bonds to the "
     "duco. Graphene Pro 10H N1 lays up to 1000nm and 10H hardness; Quartz 9H Pro "
     "up to 800nm with grade 3 chemical resistance. Glass, wheels and interior "
     "surfaces have their own coatings."),
    ("Protect",
     "The semi-permanent layer becomes a hydro barrier between your paint and the "
     "elements. The vehicle stays cleaner for longer, washes and dries more "
     "easily, holds a deep gloss, and resists wash marks, swirls, bird droppings "
     "and UV. Minimal maintenance from there."),
]

SUBURBS = [
    "Brighton", "Toorak", "South Yarra", "Hawthorn", "Kew", "Camberwell",
    "Malvern", "Armadale", "Prahran", "St Kilda", "Elwood", "Port Melbourne",
    "Docklands", "Carlton", "Fitzroy", "Richmond", "Balwyn", "Doncaster",
    "Templestowe", "Ivanhoe", "Essendon", "Moonee Ponds", "Williamstown",
    "Yarraville", "Preston", "Northcote", "Brunswick", "Coburg", "Glen Iris",
    "Box Hill", "Ringwood", "Mount Waverley", "Glen Waverley", "Bentleigh",
    "Caulfield", "Sandringham", "Mordialloc", "Frankston", "Berwick",
    "Narre Warren", "Dandenong", "Werribee", "Point Cook", "Sunshine",
]

GALLERY = [f"/assets/images/gallery/0{i}.jpg" for i in range(1, 9)]

NAV = [
    ("/booking/", "Book"),
    ("/services/", "Services"),
    ("/gallery/", "Gallery"),
    ("/testimonials/", "Reviews"),
    ("/service-areas/", "Areas"),
    ("/franchising/", "Franchising"),
    ("/contact/", "Contact"),
]

# --------------------------------------------------------------------------
# shell
# --------------------------------------------------------------------------

def esc(s):
    return html.escape(s, quote=True)


def gtm_snippet():
    """GTM container, or nothing at all if no container ID is configured.

    The dataLayer is populated either way, so tracking.js and the form handler
    behave identically before and after GTM is switched on — the events just
    queue up with no consumer until a container exists.
    """
    if not GTM_ID:
        return "<!-- GTM: no container configured (see GTM_ID in tools/build_site.py) -->"
    return (
        "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
        "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
        "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src="
        "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);"
        "})(window,document,'script','dataLayer','" + GTM_ID + "');</script>"
    )


def head(title, desc, path, og_img="/assets/images/slider01.jpg", schema=""):
    canonical = SITE + path
    links = "\n".join(
        f'    <link rel="preload" as="font" type="font/woff2" '
        f'href="/assets/fonts/{f}" crossorigin>' for f in
        ("bebas-neue-400.woff2", "dm-sans-latin.woff2")
    )
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="Formula Mobile Car Detailing">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}{og_img}">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="/favicon.ico" sizes="any">
{links}
<script>document.documentElement.classList.add('js');</script>
<link rel="stylesheet" href="/assets/css/site.css">

<script>
  window.FORMULA_CFG = {{
    ghlWebhook: {json.dumps(GHL_WEBHOOK)},
    gadsConversion: {json.dumps(GADS_CONVERSION)},
    phoneDisplay: {json.dumps(PHONE_DISPLAY)}
  }};
</script>
<script src="/assets/js/attribution.js"></script>

<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
{gtm_snippet()}
{schema}
</head>
<body>
"""


def nav(active=""):
    items = "\n".join(
        f'        <li><a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{esc(l)}</a></li>'
        for h, l in NAV
    )
    drawer_items = "\n".join(f'    <a href="{h}">{esc(l)}</a>' for h, l in NAV)
    return f"""<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<header class="nav">
  <div class="nav__in">
    <a class="nav__logo" href="/" aria-label="Formula Mobile Car Detailing — home">
      <img src="/assets/images/logo.png" alt="Formula Mobile Car Detailing" width="900" height="278">
    </a>
    <ul class="nav__links">
{items}
    </ul>
    <a class="nav__call" href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a>
    <button class="nav__burger" data-drawer-open aria-label="Open menu">
      <svg width="20" height="14" viewBox="0 0 20 14" fill="none" aria-hidden="true">
        <path d="M0 1h20M0 7h20M0 13h20" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </button>
  </div>
</header>
<nav class="drawer" data-drawer data-open="false" aria-label="Mobile">
  <button class="drawer__close" data-drawer-close aria-label="Close menu">&times;</button>
  <a href="/">Home</a>
{drawer_items}
</nav>
<main id="main">
"""


def footer():
    svc = "\n".join(
        f'        <li><a href="/services/{s["slug"]}/">{esc(s["name"])}</a></li>'
        for s in SERVICES
    ) + '\n        <li><a href="/services/select/">Browse all seven &rarr;</a></li>'
    areas = "\n".join(
        f'        <li><a href="/mobile-car-detailing/{slugify(s)}/">{esc(s)}</a></li>'
        for s in SUBURBS[:7]
    )
    return f"""</main>
<footer class="foot">
  <div class="shell">
    <div class="foot__grid">
      <div>
        <div class="foot__logo">
          <img src="/assets/images/logo.png" alt="Formula Mobile Car Detailing" width="900" height="278">
        </div>
        <p class="muted" style="font-size:.92rem;max-width:32ch">
          Mobile car detailing across metropolitan Melbourne. Over 20 years bringing
          paint work back to its best — we come to your home or office.
        </p>
      </div>
      <div>
        <h4>Services</h4>
        <ul>
{svc}
        </ul>
      </div>
      <div>
        <h4>Areas</h4>
        <ul>
{areas}
          <li><a href="/service-areas/">All areas &rarr;</a></li>
        </ul>
      </div>
      <div>
        <h4>Get in touch</h4>
        <ul>
          <li><a href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li class="muted">Metropolitan Melbourne</li>
        </ul>
        <h4 style="margin-top:1.6rem">Hours</h4>
        <ul>
          <li class="muted">Mon&ndash;Sat &nbsp;6:30am &ndash; 6:30pm</li>
          <li class="muted">Sunday &nbsp;Closed</li>
        </ul>
      </div>
    </div>
    <div class="foot__base">
      <span>&copy; <span data-year>2026</span> Formula Mobile Car Detailing. All rights reserved.</span>
      <span><a href="/privacy/">Privacy</a> &nbsp;&middot;&nbsp; <a href="/sitemap/">Sitemap</a></span>
    </div>
  </div>
</footer>

<div class="callbar">
  <a href="tel:{PHONE_LINK}" class="is-brand">Call {PHONE_DISPLAY}</a>
  <a href="/booking/">Book now</a>
</div>

<script src="/assets/js/tracking.js" defer></script>
<script src="/assets/js/enhance.js" defer></script>
</body>
</html>
"""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def write(path, content):
    full = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" \
        else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return full


# --------------------------------------------------------------------------
# schema.org — the single largest SEO gap in the audit
# --------------------------------------------------------------------------

def local_business_schema():
    reviews = ",".join(
        f"""{{"@type":"Review","reviewRating":{{"@type":"Rating","ratingValue":"5"}},
        "author":{{"@type":"Person","name":"{esc(who)}"}},
        "reviewBody":"{esc(body)}"}}"""
        for body, who in TESTIMONIALS
    )
    areas = ",".join(f'{{"@type":"City","name":"{esc(s)}, Victoria"}}' for s in SUBURBS)
    services = ",".join(
        f"""{{"@type":"Offer","itemOffered":{{"@type":"Service","name":"{esc(s['name'])}",
        "description":"{esc(s['blurb'])}"}}}}"""
        for s in SERVICES
    )
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "AutoDetailing",
  "@id": "{SITE}/#business",
  "name": "Formula Mobile Car Detailing",
  "description": "Mobile car detailing across metropolitan Melbourne — full detailing, paint correction and ceramic coatings, at your home or office.",
  "url": "{SITE}/",
  "telephone": "+61{PHONE_LINK[1:]}",
  "email": "{EMAIL}",
  "image": "{SITE}/assets/images/slider01.jpg",
  "logo": "{SITE}/assets/images/logo.png",
  "priceRange": "$$",
  "address": {{"@type": "PostalAddress", "addressRegion": "VIC", "addressCountry": "AU",
               "addressLocality": "Melbourne"}},
  "areaServed": [{areas}],
  "openingHoursSpecification": [
    {{"@type":"OpeningHoursSpecification",
      "dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
      "opens":"06:30","closes":"18:30"}}
  ],
  "hasOfferCatalog": {{"@type":"OfferCatalog","name":"Detailing services","itemListElement":[{services}]}},
  "review": [{reviews}]
}}
</script>"""


def breadcrumb_schema(trail):
    items = ",".join(
        f"""{{"@type":"ListItem","position":{i+1},"name":"{esc(n)}","item":"{SITE}{h}"}}"""
        for i, (h, n) in enumerate(trail)
    )
    return f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{items}]}}
</script>"""


def faq_schema():
    """FAQPage markup — the piece Glossedout's accordion is missing."""
    items = ",".join(
        f"""{{"@type":"Question","name":"{esc(q)}",
        "acceptedAnswer":{{"@type":"Answer","text":"{esc(a)}"}}}}"""
        for q, a in FAQS
    )
    return f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{items}]}}
</script>"""


def faq_block(heading="Common questions"):
    """Native <details> accordion: keyboard-accessible and fully functional
    with JS disabled, which a div-and-onclick implementation is not."""
    rows = "\n".join(f"""
        <details class="faq__item" data-reveal="{i * 0.04:.2f}">
          <summary class="faq__q">
            {esc(q)}
            <svg class="faq__ic" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
              <path d="M6.5 1v11M1 6.5h11" stroke="currentColor" stroke-width="1.7"/>
            </svg>
          </summary>
          <div class="faq__a"><p>{esc(a)}</p></div>
        </details>""" for i, (q, a) in enumerate(FAQS))

    return f"""
<section class="band band--tight">
  <div class="shell">
    <div style="max-width:52ch;margin-bottom:2.2rem" data-reveal>
      <span class="eyebrow">FAQ</span>
      <h2>{heading.split(' ')[0]} <span class="slant hl">{' '.join(heading.split(' ')[1:])}</span></h2>
    </div>
    <div class="faq">
{rows}
    </div>
  </div>
</section>
"""


def coating_html():
    """Scroll film: a sticky vehicle canvas the visitor orbits while the four
    coating stages scroll past. Poster-first — the still render carries the
    section on its own, and three.js plus the 5 MB model only load on approach.
    """
    panels = "".join(f"""
      <article class="coat__panel" data-stage>
        <div class="coat__copy">
          <span class="coat__num">Stage {i:02d} &mdash; 04</span>
          <h3 class="coat__h"><span class="slant">{esc(title)}</span></h3>
          <p>{esc(body)}</p>
        </div>
      </article>""" for i, (title, body) in enumerate(COATING_STAGES, start=1))

    pips = "".join(
        f'<button class="coat__pip" data-stage-pip role="tab" '
        f'aria-selected="{"true" if i == 0 else "false"}" '
        f'aria-label="{esc(t)}"></button>'
        for i, (t, _) in enumerate(COATING_STAGES)
    )

    return f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Ceramic coating</span>
    <h2>Four stages, <span class="slant hl">one finish</span></h2>
    <p class="lede">A coating is only as good as what goes under it. This is the
      process, start to finish.</p>
  </div>
</section>

<section class="coat" data-coating data-mode="poster" aria-label="The ceramic coating process">
  <div class="coat__stage">
    <img class="coat__poster" src="/assets/models/vehicle-poster.jpg" alt="" aria-hidden="true"
         loading="lazy" width="1400" height="950">
    <canvas class="coat__canvas" data-coating-canvas
            data-model="/assets/models/vehicle.glb" aria-hidden="true"></canvas>
    <div class="coat__scrim" aria-hidden="true"></div>
    <div class="coat__pips" role="tablist" aria-label="Coating stages">{pips}</div>
    <p class="coat__load">Loading the model&hellip;</p>
  </div>

  <div class="coat__panels">{panels}
  </div>
</section>
"""


def crumbs(trail):
    parts = []
    for i, (h, n) in enumerate(trail):
        last = i == len(trail) - 1
        parts.append(f'<span aria-current="page">{esc(n)}</span>' if last
                     else f'<a href="{h}">{esc(n)}</a>')
    return ('<div class="shell"><nav class="crumbs" aria-label="Breadcrumb">'
            + ' <span class="muted">/</span> '.join(parts) + "</nav></div>")


# --------------------------------------------------------------------------
# page: home
# --------------------------------------------------------------------------

def build_home():
    def tile_row(images):
        row = "".join(f"""
            <figure class="mq__tile" data-lightbox>
              <img src="{g}" alt="Detailing work by Formula Mobile Car Detailing Melbourne"
                   loading="lazy" width="800" height="600">
            </figure>""" for g in images)
        return row + row   # doubled for the seamless loop

    half = len(GALLERY) // 2
    tiles_top = tile_row(GALLERY[:half])
    tiles_bot = tile_row(GALLERY[half:])

    # Marquee: the track holds every review TWICE and translates exactly -50%,
    # so the loop is seamless. Duration scales with the count to hold speed.
    def review_card(body, who):
        return f"""
          <blockquote class="quote">
            <div class="rev__stars" aria-label="Rated 5 out of 5">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
            <p>&ldquo;{esc(body)}&rdquo;</p>
            <cite>{esc(who)}</cite>
          </blockquote>"""

    _revs = "".join(review_card(b, w) for b, w in TESTIMONIALS)
    quotes = _revs + _revs   # the second pass is what makes the seam invisible

    area_links = " ".join(
        f'<a href="/mobile-car-detailing/{slugify(s)}/">{esc(s)}</a>' for s in SUBURBS
    )

    return (
        head("Mobile Car Detailing Melbourne | Formula Mobile Car Detailing",
             "Mobile car detailing across metropolitan Melbourne. Full detailing, paint "
             "correction and ceramic coatings at your home or office. Over 20 years. "
             f"Call {PHONE_DISPLAY}.",
             "/", schema=local_business_schema() + faq_schema()
             + '<link rel="stylesheet" href="/assets/css/select.css">')
        + nav()
        + f"""
<section class="hero" data-hero>
{carousel_html(inline=True)}

  <div class="hero__splash" data-hero-splash>
    <div class="hero__fiber" aria-hidden="true"></div>
    <div class="hero__splashin">
      <img class="hero__mark" src="/assets/images/logo.png"
           alt="Formula Mobile Car Detailing" width="900" height="278" fetchpriority="high">
      <div class="hero__rule" aria-hidden="true"></div>
      <p class="hero__tag">Mobile Detailing &middot; Melbourne</p>
    </div>
  </div>

  <div class="hero__say">
    <span class="eyebrow">Mobile &middot; Metropolitan Melbourne</span>
    <h1 class="hero__h1">Melbourne&rsquo;s <span class="slant hl">finish</span></h1>
    <p class="hero__sub">Paint Protection &amp; Ceramic Coating Specialists</p>
  </div>

  <div class="hero__cue" aria-hidden="true">
    Scroll
    <svg width="10" height="13" viewBox="0 0 10 13" fill="none">
      <path d="M5 0v11M1 7.5L5 11.5 9 7.5" stroke="currentColor" stroke-width="1.4"/>
    </svg>
  </div>
</section>


<section class="band mesh band--raise">
  <div class="shell">
    <div class="grid grid--4">
      <div class="stat" data-reveal><span class="stat__n" data-count="20" data-suffix="+">20+</span><span class="stat__l">Years detailing</span></div>
      <div class="stat" data-reveal="0.08"><span class="stat__n" data-count="7">7</span><span class="stat__l">Services</span></div>
      <div class="stat" data-reveal="0.16"><span class="stat__n" data-count="10" data-suffix="H">10H</span><span class="stat__l">Graphene coating</span></div>
      <div class="stat" data-reveal="0.24"><span class="stat__n">100%</span><span class="stat__l">Mobile &mdash; we come to you</span></div>
    </div>
  </div>
</section>

{coating_html()}

<section class="band band--raise mesh">
  <div class="shell">
    <div style="max-width:52ch;margin-bottom:2.4rem" data-reveal>
      <span class="eyebrow">Recent work</span>
      <h2>The finish <span class="slant hl">speaks</span></h2>
    </div>
  </div>
  <div class="mq__rows">
    <div class="mq mq--tiles" style="--mq-dur:52s">
      <div class="mq__track">{tiles_top}
      </div>
    </div>
    <div class="mq mq--tiles mq--rev" style="--mq-dur:58s">
      <div class="mq__track">{tiles_bot}
      </div>
    </div>
  </div>
  <div class="shell">
    <p style="margin-top:2rem"><a class="btn btn--ghost" href="/gallery/">See the full gallery</a></p>
  </div>
</section>

<section class="band">
  <div class="shell">
    <div style="max-width:52ch;margin-bottom:2.4rem" data-reveal>
      <span class="eyebrow">What clients say</span>
      <h2>A cut above <span class="slant hl">everybody else</span></h2>
    </div>
  </div>
  <div class="mq" style="--mq-dur:{max(38, len(TESTIMONIALS) * 16)}s">
    <div class="mq__track">{quotes}
    </div>
  </div>
</section>

<section class="band band--raise mesh">
  <div class="shell">
    <div style="max-width:56ch;margin-bottom:2rem" data-reveal>
      <span class="eyebrow">Where we go</span>
      <h2>Across <span class="slant hl">metropolitan Melbourne</span></h2>
      <p class="lede">We're mobile. We come to your home or your office, with our own water
        and power &mdash; you don't need to go anywhere.</p>
    </div>
    <div class="arealinks" data-reveal>{area_links}</div>
  </div>
</section>

{faq_block()}

<section class="band">
  <div class="shell" style="text-align:center">
    <h2 data-reveal>Ready to book <span class="slant hl">your detail?</span></h2>
    <p class="lede" style="margin:0 auto 2rem" data-reveal="0.06">
      Talk to our operators for an obligation-free chat about what your vehicle needs.
    </p>
    <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap" data-reveal="0.12">
      <a class="btn btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
      <a class="btn btn--ghost btn--lg" href="/booking/">Book a detail</a>
    </div>
  </div>
</section>
"""
        + footer().replace(
            '<script src="/assets/js/enhance.js" defer></script>',
            '<script type="importmap">{"imports":{"three":"/assets/js/vendor/three.module.js"}}</script>\n'
            '<script src="/assets/js/coating.js" type="module"></script>\n'
            '<script src="/assets/js/select.js" defer></script>\n'
            '<script src="/assets/js/hero.js" defer></script>\n'
            '<script src="/assets/js/enhance.js" defer></script>')
    )


# --------------------------------------------------------------------------
# page: services index + detail
# --------------------------------------------------------------------------

def build_services_index():
    cards = "\n".join(f"""
        <a class="card card--media" href="/services/{s['slug']}/" data-reveal="{i*0.05:.2f}">
          <img src="{s['img']}" alt="{esc(s['name'])}" loading="lazy" width="600" height="450">
          <div class="card__pad">
            <span class="card__num">0{i}</span>
            <h3 class="card__title">{esc(s['name'])}</h3>
            <p>{esc(s['blurb'])}</p>
          </div>
        </a>""" for i, s in enumerate(SERVICES, start=1))

    trail = [("/", "Home"), ("/services/", "Services")]
    return (
        head("Car Detailing Services Melbourne | Formula Mobile Car Detailing",
             "Mini and full detailing, interior and exterior detailing, overspray removal, "
             "ceramic coatings and paint correction — mobile across Melbourne.",
             "/services/", schema=breadcrumb_schema(trail) + faq_schema())
        + nav("/services/")
        + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Our services</span>
    <h1>Everything from a <span class="slant hl">wash</span> to a <span class="slant hl">full correction</span></h1>
    <p class="lede">We can accommodate any request you have for your vehicle and put together
      a package that suits your needs and budget &mdash; whether that's a full detail, an
      exterior or interior detail, or even just a wash.</p>
    <p style="margin-top:1.6rem">
      <a class="btn btn--lg" href="/services/select/">
        Browse all seven
        <svg width="13" height="9" viewBox="0 0 13 9" fill="none" aria-hidden="true">
          <path d="M0 4.5h11M7.5 1L11 4.5 7.5 8" stroke="currentColor" stroke-width="1.6"/>
        </svg>
      </a>
    </p>
  </div>
</section>
<section class="band band--tight">
  <div class="shell">
    <div class="grid grid--3">
{cards}
    </div>
  </div>
</section>
{faq_block()}

<section class="band band--raise mesh">
  <div class="shell" style="text-align:center">
    <h2>Not sure what it needs?</h2>
    <p class="lede" style="margin:0 auto 2rem">Just call our experienced operators for an
      obligation-free chat.</p>
    <a class="btn btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
  </div>
</section>
"""
        + footer()
    )


def build_service(s):
    groups = ""
    for gtitle, items in s.get("groups", []):
        lis = "\n".join(f"          <li>{esc(x)}</li>" for x in items)
        groups += f"""
      <div class="card" data-reveal>
        <h3>{esc(gtitle)}</h3>
        <ul class="ticks">
{lis}
        </ul>
      </div>"""

    products = ""
    if s.get("products"):
        cards = "\n".join(f"""
        <div class="card" data-reveal>
          <h3>{esc(n)}</h3>
          <p>{esc(d)}</p>
          <ul class="ticks">{''.join(f'<li>{esc(m)}</li>' for m in meta)}</ul>
        </div>""" for n, d, meta in s["products"])
        products = f"""
<section class="band band--raise mesh">
  <div class="shell">
    <span class="eyebrow">Coatings we apply</span>
    <h2>The <span class="slant hl">products</span></h2>
    <div class="grid grid--2" style="margin-top:2rem">
{cards}
    </div>
  </div>
</section>"""

    others = "\n".join(
        f'<li><a href="/services/{o["slug"]}/">{esc(o["name"])}</a></li>'
        for o in SERVICES if o["slug"] != s["slug"]
    )

    trail = [("/", "Home"), ("/services/", "Services"),
             (f"/services/{s['slug']}/", s["name"])]
    schema = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Service","name":"{esc(s['name'])}",
"description":"{esc(s['blurb'])}","serviceType":"{esc(s['name'])}",
"provider":{{"@id":"{SITE}/#business"}},
"areaServed":{{"@type":"City","name":"Melbourne, Victoria"}},
"url":"{SITE}/services/{s['slug']}/"}}
</script>""" + breadcrumb_schema(trail)

    return (
        head(f"{s['name']} Melbourne | Formula Mobile Car Detailing",
             s["blurb"], f"/services/{s['slug']}/", s["img"], schema)
        + nav("/services/")
        + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <div class="grid grid--2" style="align-items:center;gap:3rem">
      <div>
        <span class="eyebrow">Service</span>
        <h1><span class="slant">{esc(s['name'])}</span></h1>
        <p class="lede">{esc(s['intro'])}</p>
        <div style="display:flex;gap:.8rem;flex-wrap:wrap;margin-top:1.6rem">
          <a class="btn" href="/booking/">Book this service</a>
          <a class="btn btn--ghost" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
        </div>
      </div>
      <div>
        <img src="{s['img']}" alt="{esc(s['name'])} in Melbourne" width="600" height="450"
             style="border-radius:var(--radius-lg);border:1px solid var(--border-soft)">
      </div>
    </div>
  </div>
</section>
<section class="band band--tight">
  <div class="shell">
    <div class="grid grid--2">
{groups}
    </div>
  </div>
</section>
{products}
<section class="band">
  <div class="shell">
    <h2>Other services</h2>
    <ul class="ticks" style="columns:2;margin-top:1rem">{others}</ul>
  </div>
</section>
"""
        + footer()
    )


# --------------------------------------------------------------------------
# remaining pages
# --------------------------------------------------------------------------

def carousel_html(inline=False):
    """The coverflow markup, shared by /services/select/ and the homepage hero.

    inline=True drops the scroll lock and the page-chrome header, and turns on
    autoplay. As a hero it must not eat the wheel — the visitor has to be able
    to scroll past into the rest of the page.
    """
    bgs, cards, pips = [], [], []

    for i, s in enumerate(SERVICES):
        img, grade = SELECT_LOOKS[s["slug"]]
        bgs.append(f"""
      <div class="sel__bg{' is-on' if i == 0 else ''}" data-bg style="--grade:{grade}">
        <img src="{img}" alt="" aria-hidden="true" {'fetchpriority="high"' if i == 0 else 'loading="lazy"'}>
      </div>""")

        cards.append(f"""
      <article class="sel__card" data-card aria-label="{esc(s['name'])}">
        <div class="sel__reticle" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
        <div class="sel__art">
          <img src="{s['img']}" alt="{esc(s['name'])}" loading="lazy" width="500" height="300">
        </div>
        <div class="sel__body">
          <span class="sel__idx">{i + 1:02d} / {len(SERVICES):02d}</span>
          <h2 class="sel__name">{esc(s['name'])}</h2>
          <p class="sel__blurb">{esc(s['blurb'])}</p>
          <a class="sel__go" href="/services/{s['slug']}/">
            Select
            <svg width="13" height="9" viewBox="0 0 13 9" fill="none" aria-hidden="true">
              <path d="M0 4.5h11M7.5 1L11 4.5 7.5 8" stroke="currentColor" stroke-width="1.6"/>
            </svg>
          </a>
        </div>
      </article>""")

        pips.append(
            f'        <button class="sel__pip" data-pip type="button" role="tab" '
            f'aria-selected="{"true" if i == 0 else "false"}" '
            f'aria-label="{esc(s["name"])}"></button>'
        )

    cls = "sel sel--inline" if inline else "sel"
    flags = ' data-select-auto="4600"' if inline else " data-select-lock"

    return f"""
<div class="{cls}" data-select{flags}>
  <div class="sel__bgs" aria-hidden="true">{''.join(bgs)}
  </div>
  <div class="sel__veil" aria-hidden="true"></div>

  <div class="sel__stage">
    <div class="sel__track" role="tablist" aria-label="Services">{''.join(cards)}
    </div>
  </div>

  <div class="sel__hud">
    <div class="sel__top"{'' if not inline else ' hidden'}>
      <a class="sel__back" href="/services/">
        <svg width="13" height="9" viewBox="0 0 13 9" fill="none" aria-hidden="true">
          <path d="M13 4.5H2M5.5 1L2 4.5 5.5 8" stroke="currentColor" stroke-width="1.6"/>
        </svg>
        All services
      </a>
      <a href="/" aria-label="Formula Mobile Car Detailing — home">
        <img src="/assets/images/logo.png" alt="Formula Mobile Car Detailing" width="900" height="278">
      </a>
      <a class="sel__back" href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a>
    </div>

    <div></div>

    <div class="sel__bottom">
      <span class="sel__counter"><b data-cur>01</b> / {len(SERVICES):02d}</span>
      <div class="sel__pips" role="tablist" aria-label="Choose a service">
{chr(10).join(pips)}
      </div>
      <span class="sel__hint">
        <svg width="11" height="13" viewBox="0 0 11 13" fill="none" aria-hidden="true">
          <rect x=".75" y=".75" width="9.5" height="11.5" rx="4.75" stroke="currentColor" stroke-width="1.2"/>
          <path d="M5.5 3.5v2.2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
        {'Drag' if inline else 'Scroll or drag'}<span class="sel__kbd"> &middot; or use &larr; &rarr;</span>
      </span>
    </div>
  </div>

  <button class="sel__arrow sel__arrow--prev" data-prev type="button" aria-label="Previous service">
    <svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">
      <path d="M15 5.5H2M6 1L2 5.5 6 10" stroke="currentColor" stroke-width="1.7"/>
    </svg>
  </button>
  <button class="sel__arrow sel__arrow--next" data-next type="button" aria-label="Next service">
    <svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">
      <path d="M0 5.5h13M9 1l4 4.5L9 10" stroke="currentColor" stroke-width="1.7"/>
    </svg>
  </button>
</div>
"""


def build_select():
    """Standalone selector — full viewport, wheel-driven, no page scroll."""
    trail = [("/", "Home"), ("/services/", "Services"),
             ("/services/select/", "Choose a service")]
    return f"""{head(
        "Choose a Service | Formula Mobile Car Detailing",
        "Browse all seven Formula Mobile Car Detailing services — mini and full detailing, "
        "interior, exterior, overspray removal, ceramic coatings and paint correction.",
        "/services/select/", SERVICES[0]["img"], breadcrumb_schema(trail))}
<link rel="stylesheet" href="/assets/css/select.css">
{carousel_html(inline=False)}
<script src="/assets/js/select.js" defer></script>
</body>
</html>
"""


def build_booking():
    """4-step booking wizard, adopting the flow from
    premiermobiledetailing.com.au/booking: Service -> Location -> Vehicle ->
    Details, with a progress rail, back/continue, and a phone fallback on
    failure. Options are Formula's own services and their own language.
    """

    def tiles(name, options):
        """`required` is deliberately NOT emitted on these radios.

        The inputs are visually hidden inside their tile, and Chrome refuses to
        submit a form containing an invalid control it cannot focus — it logs
        "not focusable" and stops dead, with nothing shown to the visitor. The
        choice is enforced by booking.js via data-requires-choice instead,
        which can point at the tile group and say something useful.
        """
        out = []
        for val, title, sub in options:
            out.append(f"""
          <label class="bk__tile">
            <input type="radio" name="{name}" value="{esc(val)}">
            <span class="bk__tiletitle">{esc(title)}</span>
            <span class="bk__tilesub">{esc(sub)}</span>
          </label>""")
        return "".join(out)

    def first_sentences(text, minimum=40):
        """One sentence, or two when the first is too short to say anything.
        "The complete service." alone tells a visitor nothing."""
        parts = [p.strip() for p in text.split(".") if p.strip()]
        out = parts[0]
        if len(out) < minimum and len(parts) > 1:
            out += ". " + parts[1]
        return out + "."

    services = [(s["name"], s["name"], first_sentences(s["blurb"])) for s in SERVICES]
    services.append(("Not sure yet", "Not sure yet", "Help me pick the right service."))

    # Formula is mobile; paint correction is the exception — their own copy says
    # it is "conducted in our specialty studio created for these applications".
    where = [
        ("Mobile — at your door", "Mobile — at your door",
         "We bring our own water and power to your home or office."),
        ("Studio — paint correction", "Studio — paint correction",
         "Correction work is done in our specialty studio."),
    ]

    paint = [
        ("New / Excellent", "New / Excellent", "Near-new, minimal marks."),
        ("Good", "Good", "Light swirls and minor marks."),
        ("Fair", "Fair", "Noticeable swirls, scratches or wash marks."),
        ("Poor", "Poor", "Heavy scratches, spider webbing or oxidised and dull."),
    ]

    interior = [
        ("Clean / Tidy", "Clean / Tidy", "Well kept, just needs a refresh."),
        ("Lightly messy", "Lightly messy", "Everyday use, crumbs and dust."),
        ("Dirty", "Dirty", "Stains, spills and built-up grime."),
        ("Full reset", "Full reset", "Heavily soiled — needs a deep clean."),
    ]

    trail = [("/", "Home"), ("/booking/", "Book")]
    rail = "".join(
        f'<li class="bk__dot" data-dot data-state="{"now" if i == 0 else "todo"}">'
        f'<span>{i + 1}</span>{esc(lbl)}</li>'
        for i, lbl in enumerate(["Service", "Where", "Vehicle", "Details"])
    )

    return (
        head("Book a Detail | Formula Mobile Car Detailing",
             "Book mobile car detailing across Melbourne — takes under a minute, and "
             "we'll call or text back to confirm a time.",
             "/booking/", SERVICES[1]["img"], breadcrumb_schema(trail))
        + nav()
        + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Booking</span>
    <h1>Book your <span class="slant hl">detail</span></h1>
    <p class="lede">Takes under a minute. We'll call or text back to confirm a time
      &mdash; no obligation, and no payment up front.</p>
  </div>
</section>

<section class="band band--tight">
  <div class="shell bk">
    <ol class="bk__rail">{rail}</ol>
    <p class="visually-hidden" data-live aria-live="polite"></p>

    <form class="bk__form card" method="post" action="/thank-you/" data-booking>

      <fieldset class="bk__step" data-step>
        <legend class="bk__legend">Choose your service</legend>
        <p class="bk__hint">Pick what you're after &mdash; not sure? Choose &ldquo;Not sure yet&rdquo;.</p>
        <div class="bk__tiles" data-requires-choice>{tiles("service", services)}</div>
      </fieldset>

      <fieldset class="bk__step" data-step>
        <legend class="bk__legend">Where are we working?</legend>
        <p class="bk__hint">We service metropolitan Melbourne.</p>
        <div class="bk__tiles bk__tiles--2" data-requires-choice>{tiles("location_type", where)}</div>
        <div class="field--split" style="margin-top:1.4rem">
          <div class="field">
            <label for="bk-suburb">Suburb</label>
            <input id="bk-suburb" name="suburb" type="text" autocomplete="address-level2" required>
          </div>
          <div class="field">
            <label for="bk-postcode">Postcode</label>
            <input id="bk-postcode" name="postcode" type="text" inputmode="numeric"
                   autocomplete="postal-code" pattern="[0-9]{{4}}" maxlength="4">
          </div>
        </div>
      </fieldset>

      <fieldset class="bk__step" data-step>
        <legend class="bk__legend">Tell us about the car</legend>
        <div class="field">
          <label for="bk-vehicle">Make, model and year</label>
          <input id="bk-vehicle" name="vehicle" type="text" placeholder="e.g. BMW M3, 2021" required>
        </div>
        <p class="bk__sublabel">Paint condition</p>
        <div class="bk__tiles bk__tiles--4" data-requires-choice>{tiles("paint_condition", paint)}</div>
        <p class="bk__sublabel">Interior condition</p>
        <div class="bk__tiles bk__tiles--4" data-requires-choice>{tiles("interior_condition", interior)}</div>
      </fieldset>

      <fieldset class="bk__step" data-step>
        <legend class="bk__legend">How do we reach you?</legend>
        <div class="field">
          <label for="bk-name">Name</label>
          <input id="bk-name" name="name" type="text" autocomplete="name" required>
        </div>
        <div class="field--split">
          <div class="field">
            <label for="bk-phone">Mobile</label>
            <input id="bk-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel"
                   pattern="[0-9 \\(\\)+\\-]{{6,}}" required>
          </div>
          <div class="field">
            <label for="bk-email">Email <span class="muted">(optional)</span></label>
            <input id="bk-email" name="email" type="email" autocomplete="email">
          </div>
        </div>
        <div class="field">
          <label for="bk-comments">Anything else? <span class="muted">(optional)</span></label>
          <textarea id="bk-comments" name="comments" rows="4"></textarea>
        </div>
      </fieldset>

      <p class="formerr" data-form-error role="alert" hidden></p>

      <div class="bk__nav">
        <button class="btn btn--ghost" type="button" data-back hidden>&larr; Back</button>
        <button class="btn" type="button" data-next-step>Continue &rarr;</button>
        <button class="btn btn--lg" type="submit" data-submit hidden>Request my booking</button>
      </div>
    </form>

    <p class="bk__alt muted">
      Prefer to talk? Call <a href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a>
      or email <a href="mailto:{EMAIL}">{EMAIL}</a>.
    </p>
  </div>
</section>

<script src="/assets/js/booking.js" defer></script>
"""
        + footer()
    )


def build_gallery():
    tiles = "\n".join(f"""
        <figure class="tile" data-lightbox data-reveal="{i*0.04:.2f}">
          <img src="{g}" alt="Car detailing work by Formula Mobile Car Detailing Melbourne"
               loading="lazy" width="800" height="600">
        </figure>""" for i, g in enumerate(GALLERY, start=1))
    trail = [("/", "Home"), ("/gallery/", "Gallery")]
    return (
        head("Gallery | Formula Mobile Car Detailing Melbourne",
             "Recent detailing, paint correction and ceramic coating work by Formula Mobile "
             "Car Detailing across Melbourne.",
             "/gallery/", GALLERY[0], breadcrumb_schema(trail))
        + nav("/gallery/") + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Gallery</span>
    <h1>Recent <span class="slant hl">work</span></h1>
    <p class="lede">A selection of vehicles we've detailed, corrected and coated.</p>
  </div>
</section>
<section class="band band--tight">
  <div class="shell"><div class="tiles">
{tiles}
  </div></div>
</section>
""" + footer())


def build_testimonials():
    quotes = "\n".join(f"""
        <blockquote class="quote" data-reveal="{i*0.06:.2f}">
          <p>&ldquo;{esc(b)}&rdquo;</p>
          <cite>{esc(w)}</cite>
        </blockquote>""" for i, (b, w) in enumerate(TESTIMONIALS, start=1))
    trail = [("/", "Home"), ("/testimonials/", "Reviews")]
    return (
        head("Reviews | Formula Mobile Car Detailing Melbourne",
             "What Melbourne clients say about Formula Mobile Car Detailing.",
             "/testimonials/", schema=breadcrumb_schema(trail))
        + nav("/testimonials/") + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Reviews</span>
    <h1>What clients <span class="slant hl">say</span></h1>
  </div>
</section>
<section class="band band--tight">
  <div class="shell"><div class="grid grid--3">
{quotes}
  </div></div>
</section>
""" + footer())


def build_contact():
    trail = [("/", "Home"), ("/contact/", "Contact")]
    return (
        head("Contact | Formula Mobile Car Detailing Melbourne",
             f"Get an obligation-free quote for mobile car detailing in Melbourne. "
             f"Call {PHONE_DISPLAY} or send an enquiry.",
             "/contact/", schema=breadcrumb_schema(trail))
        + nav("/contact/") + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Contact</span>
    <h1>Get a <span class="slant hl">quote</span></h1>
    <p class="lede">Tell us the vehicle and what it needs. Our operators will come back to
      you with a price &mdash; no obligation.</p>
  </div>
</section>
<section class="band band--tight">
  <div class="shell">
    <div class="grid grid--2" style="gap:3rem;align-items:start">
      <form class="card" method="post" action="/thank-you/" data-lead-form>
        <div class="field--split">
          <div class="field">
            <label for="fname">First name</label>
            <input id="fname" name="firstname" type="text" autocomplete="given-name" required>
          </div>
          <div class="field">
            <label for="lname">Last name</label>
            <input id="lname" name="lastname" type="text" autocomplete="family-name" required>
          </div>
        </div>
        <div class="field--split">
          <div class="field">
            <label for="email">Email</label>
            <input id="email" name="email" type="email" autocomplete="email" required>
          </div>
          <div class="field">
            <label for="phone">Phone</label>
            <!-- Parens and the hyphen MUST be escaped: browsers compile the
                 pattern with the regex `v` flag, where ( ) - are reserved
                 inside a character class. An invalid pattern throws on submit
                 and blocks the form outright. -->
            <input id="phone" name="phone" type="tel" autocomplete="tel"
                   inputmode="tel" pattern="[0-9 \\(\\)+\\-]{{6,}}" required>
          </div>
        </div>
        <div class="field">
          <label for="suburb">Suburb</label>
          <input id="suburb" name="suburb" type="text" autocomplete="address-level2" required>
        </div>
        <div class="field">
          <label for="service">Service</label>
          <select id="service" name="service" required>
            <option value="">Choose a service&hellip;</option>
            {''.join(f'<option>{esc(s["name"])}</option>' for s in SERVICES)}
            <option>Not sure &mdash; please advise</option>
          </select>
        </div>
        <div class="field">
          <label for="vehicle">Vehicle</label>
          <input id="vehicle" name="vehicle" type="text" placeholder="Make, model, year">
        </div>
        <div class="field">
          <label for="comments">Anything else?</label>
          <textarea id="comments" name="comments"></textarea>
        </div>
        <p class="formerr" data-form-error role="alert" hidden></p>
        <button class="btn btn--block btn--lg" type="submit">Send enquiry</button>
        <p class="muted" style="font-size:.8rem;margin-top:1rem;margin-bottom:0">
          {"Submissions post straight to the CRM." if GHL_WEBHOOK
           else "No CRM webhook is configured yet &mdash; set <code>GHL_WEBHOOK</code> in "
                "<code>tools/build_site.py</code> before launch. See the README."}
        </p>
      </form>
      <script src="/assets/js/lead-form.js" defer></script>

      <div>
        <div class="card" style="margin-bottom:1.4rem">
          <h3>Call us</h3>
          <p><a class="nav__call" href="tel:{PHONE_LINK}" style="font-size:1.9rem">{PHONE_DISPLAY}</a></p>
          <h4 style="margin-top:1.4rem">Email</h4>
          <p><a href="mailto:{EMAIL}">{EMAIL}</a></p>
          <h4 style="margin-top:1.4rem">Hours</h4>
          <p class="muted">Monday&ndash;Saturday 6:30am &ndash; 6:30pm<br>Sunday closed</p>
          <h4 style="margin-top:1.4rem">Where</h4>
          <p class="muted">We're mobile across metropolitan Melbourne &mdash; we come to your
            home or office.</p>
        </div>
        <div class="card" style="padding:0;overflow:hidden">
          <iframe title="Formula Mobile Car Detailing service area — metropolitan Melbourne"
            src="https://www.google.com/maps?q=Melbourne+VIC+Australia&output=embed"
            width="100%" height="320" style="border:0;display:block" loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
      </div>
    </div>
  </div>
</section>
""" + footer())


def build_franchising():
    points = [
        ("We are masters of our trade",
         "We pride ourselves on specialist skills and knowledge mastered over 20+ years in "
         "the industry, including highly specialised techniques to restore vehicles affected "
         "by fallout and malicious damage."),
        ("Comprehensive on-the-job training",
         "We'll train you in the art of interior and exterior detailing so you can become a "
         "pro at something you enjoy and build a profitable business at the same time."),
        ("A proven model",
         "The franchising system is based on 20 years in the car detailing industry. You get "
         "our industry experience and business expertise, plus ongoing support."),
        ("Low overheads, mobile by design",
         "We go to the customer, whether it's their office or their home. Lower overheads for "
         "you and a more exciting, more profitable business, with your own vehicle decked out "
         "with all the equipment you need."),
    ]
    cards = "\n".join(f"""
        <div class="card" data-reveal="{i*0.06:.2f}">
          <span class="card__num">0{i}</span>
          <h3 class="card__title">{esc(t)}</h3>
          <p>{esc(d)}</p>
        </div>""" for i, (t, d) in enumerate(points, start=1))
    trail = [("/", "Home"), ("/franchising/", "Franchising")]
    return (
        head("Franchising | Formula Mobile Car Detailing",
             "Join the Formula Mobile Car Detailing family. Comprehensive on-the-job "
             "training, a proven model built on 20 years, and low mobile overheads.",
             "/franchising/", schema=breadcrumb_schema(trail))
        + nav("/franchising/") + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Franchising</span>
    <h1>Be your <span class="slant hl">own boss</span></h1>
    <p class="lede">Love the idea of working with new products and cutting-edge technologies
      to improve the appearance of modern, prestige and vintage motor vehicles? Join the
      Formula Mobile Car Detailing family.</p>
  </div>
</section>
<section class="band band--tight">
  <div class="shell"><div class="grid grid--2">
{cards}
  </div></div>
</section>
<section class="band band--raise mesh">
  <div class="shell" style="text-align:center">
    <h2>Want to know <span class="slant hl">more?</span></h2>
    <p class="lede" style="margin:0 auto 2rem">Get in touch about running your own Formula
      Mobile Car Detailing franchise.</p>
    <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
      <a class="btn btn--lg" href="/contact/">Enquire about a franchise</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>
""" + footer())


def build_suburb(name):
    slug = slugify(name)
    trail = [("/", "Home"), ("/service-areas/", "Service areas"),
             (f"/mobile-car-detailing/{slug}/", name)]
    svc = "\n".join(f"""
        <a class="card card--media" href="/services/{s['slug']}/" data-reveal="{i*0.05:.2f}">
          <img src="{s['img']}" alt="{esc(s['name'])} in {esc(name)}" loading="lazy"
               width="600" height="450">
          <div class="card__pad">
            <h3 class="card__title">{esc(s['name'])}</h3>
            <p>{esc(s['blurb'])}</p>
          </div>
        </a>""" for i, s in enumerate(SERVICES[:3], start=1))

    nearby = [x for x in SUBURBS if x != name][:8]
    near = " ".join(f'<a href="/mobile-car-detailing/{slugify(x)}/">{esc(x)}</a>'
                    for x in nearby)

    schema = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Service",
"name":"Mobile Car Detailing {esc(name)}",
"serviceType":"Mobile car detailing",
"provider":{{"@id":"{SITE}/#business"}},
"areaServed":{{"@type":"City","name":"{esc(name)}, Victoria, Australia"}},
"url":"{SITE}/mobile-car-detailing/{slug}/"}}
</script>""" + breadcrumb_schema(trail)

    return (
        head(f"Mobile Car Detailing {name} | Formula Mobile Car Detailing",
             f"Mobile car detailing in {name}. Full detailing, paint correction and ceramic "
             f"coatings at your home or office. Over 20 years. Call {PHONE_DISPLAY}.",
             f"/mobile-car-detailing/{slug}/", schema=schema)
        + nav() + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Service area</span>
    <h1>Mobile car detailing<br><span class="slant hl">{esc(name)}</span></h1>
    <p class="lede">We bring the whole setup to you in {esc(name)} &mdash; our own water and
      power, so you don't need to go anywhere. Book us at home or at the office and watch the
      work happen.</p>
    <div style="display:flex;gap:.8rem;flex-wrap:wrap;margin-top:1.6rem">
      <a class="btn btn--lg" href="/booking/">Book in {esc(name)}</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>
<section class="band band--tight">
  <div class="shell">
    <h2>Popular in <span class="slant hl">{esc(name)}</span></h2>
    <div class="grid grid--3" style="margin-top:2rem">
{svc}
    </div>
  </div>
</section>
<section class="band band--raise mesh">
  <div class="shell">
    <h2>Also servicing</h2>
    <div class="arealinks" style="margin-top:1.4rem">{near}</div>
    <p style="margin-top:1.6rem"><a class="btn btn--ghost" href="/service-areas/">All service areas</a></p>
  </div>
</section>
""" + footer())


def build_areas_index():
    links = " ".join(
        f'<a href="/mobile-car-detailing/{slugify(s)}/">{esc(s)}</a>' for s in SUBURBS)
    trail = [("/", "Home"), ("/service-areas/", "Service areas")]
    return (
        head("Service Areas | Mobile Car Detailing Across Melbourne",
             "Formula Mobile Car Detailing services metropolitan Melbourne — see every "
             "suburb we cover.",
             "/service-areas/", schema=breadcrumb_schema(trail))
        + nav("/service-areas/") + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Where we go</span>
    <h1>Servicing <span class="slant hl">metropolitan Melbourne</span></h1>
    <p class="lede">We're fully mobile. Pick your suburb, or just call us &mdash; if you're in
      the Melbourne metro area, we'll come to you.</p>
  </div>
</section>
<section class="band band--tight">
  <div class="shell"><div class="arealinks">{links}</div></div>
</section>
""" + footer())


def build_thanks():
    return (
        head("Thank you | Formula Mobile Car Detailing",
             "Your enquiry has been received.", "/thank-you/")
        + nav()
        + f"""
<section class="band" style="padding-top:calc(var(--nav-h) + 6rem);text-align:center">
  <div class="shell">
    <span class="eyebrow">Received</span>
    <h1>Thanks &mdash; we'll <span class="slant hl">be in touch</span></h1>
    <p class="lede" style="margin:0 auto 2rem">One of our operators will get back to you.
      If it's urgent, give us a call.</p>
    <a class="btn btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
  </div>
</section>
""" + footer())


def build_sitemap_page():
    def ul(items):
        return "<ul class='ticks'>" + "".join(
            f'<li><a href="{h}">{esc(n)}</a></li>' for h, n in items) + "</ul>"
    return (
        head("Sitemap | Formula Mobile Car Detailing", "Every page on the site.", "/sitemap/")
        + nav()
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Sitemap</span>
    <h1>Every <span class="slant hl">page</span></h1>
    <div class="grid grid--3" style="margin-top:2rem">
      <div><h3>Main</h3>{ul([("/", "Home"), ("/services/", "Services"), ("/gallery/", "Gallery"), ("/testimonials/", "Reviews"), ("/service-areas/", "Service areas"), ("/franchising/", "Franchising"), ("/contact/", "Contact")])}</div>
      <div><h3>Services</h3>{ul([(f"/services/{s['slug']}/", s['name']) for s in SERVICES])}</div>
      <div><h3>Areas</h3>{ul([(f"/mobile-car-detailing/{slugify(s)}/", s) for s in SUBURBS])}</div>
    </div>
  </div>
</section>
""" + footer())


def build_privacy():
    return (
        head("Privacy Policy | Formula Mobile Car Detailing",
             "How Formula Mobile Car Detailing handles your information.", "/privacy/")
        + nav()
        + f"""
<section class="band band--tight">
  <div class="shell" style="max-width:70ch">
    <span class="eyebrow">Privacy</span>
    <h1>Privacy <span class="slant hl">policy</span></h1>
    <p class="lede">This is a placeholder. The client needs to supply or approve the final
      privacy policy wording before launch.</p>
    <p class="muted">What we collect via the enquiry form: your name, email, phone, suburb and
      the details you provide about your vehicle. We use it to respond to your enquiry.
      Analytics are collected via Google Analytics ({GA_ID}).</p>
    <p class="muted">Questions: <a href="mailto:{EMAIL}">{EMAIL}</a> or {PHONE_DISPLAY}.</p>
  </div>
</section>
""" + footer())


def build_404():
    return (
        head("Page not found | Formula Mobile Car Detailing", "That page doesn't exist.",
             "/404/")
        + nav()
        + f"""
<section class="band" style="padding-top:calc(var(--nav-h) + 6rem);text-align:center">
  <div class="shell">
    <span class="eyebrow">404</span>
    <h1>That page <span class="slant hl">isn't here</span></h1>
    <p class="lede" style="margin:0 auto 2rem">It may have moved. Try the services page, or
      call us.</p>
    <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
      <a class="btn btn--lg" href="/services/">Our services</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>
""" + footer())


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------

def main():
    routes = []

    write("/", build_home());                       routes.append(("/", "1.0"))
    write("/booking/", build_booking());            routes.append(("/booking/", "1.0"))
    write("/services/", build_services_index());    routes.append(("/services/", "0.9"))
    write("/services/select/", build_select());     routes.append(("/services/select/", "0.7"))
    for s in SERVICES:
        write(f"/services/{s['slug']}/", build_service(s))
        routes.append((f"/services/{s['slug']}/", "0.8"))
    write("/gallery/", build_gallery());            routes.append(("/gallery/", "0.7"))
    write("/testimonials/", build_testimonials());  routes.append(("/testimonials/", "0.7"))
    write("/contact/", build_contact());            routes.append(("/contact/", "0.9"))
    write("/franchising/", build_franchising());    routes.append(("/franchising/", "0.7"))
    write("/service-areas/", build_areas_index());  routes.append(("/service-areas/", "0.8"))
    for sub in SUBURBS:
        write(f"/mobile-car-detailing/{slugify(sub)}/", build_suburb(sub))
        routes.append((f"/mobile-car-detailing/{slugify(sub)}/", "0.6"))
    write("/thank-you/", build_thanks())
    write("/sitemap/", build_sitemap_page());       routes.append(("/sitemap/", "0.3"))
    write("/privacy/", build_privacy());            routes.append(("/privacy/", "0.3"))

    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_404())

    # sitemap.xml
    urls = "\n".join(
        f"  <url><loc>{SITE}{p}</loc><priority>{pr}</priority></url>" for p, pr in routes)
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"{urls}\n</urlset>\n")

    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    with open(os.path.join(OUT, "vercel.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("""{
  "cleanUrls": true,
  "trailingSlash": true,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "SAMEORIGIN" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "geolocation=(), microphone=(), camera=()" },
        { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" }
      ]
    },
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
""")

    print(f"pages:   {len(routes) + 2}")
    print(f"routes:  {len(routes)} in sitemap.xml")
    print(f"output:  {OUT}")


if __name__ == "__main__":
    main()
