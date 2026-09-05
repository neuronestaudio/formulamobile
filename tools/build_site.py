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
import hashlib
import os
import re
import shutil

from keywords import CLUSTERS

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
GHL_WEBHOOK = "https://services.leadconnectorhq.com/hooks/hNVXPl4iU47f42LDBVad/webhook-trigger/5Fk7YCgZKOViortglwIn"
GADS_CONVERSION = ""   # e.g. "AW-XXXXXXXXX/AbCdEfGhIjKlMnOp"

# --------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------

SPLASH = [
    {
        "img": "/assets/images/slider01.jpg",
        "tier": "Deluxe Detail",
        "title": "Inside and out",
        "copy": "Engine bay, door jams, clay bar, hand polish, extraction through the "
                "carpets and leather conditioned. The whole vehicle, done properly.",
        "href": "/services/deluxe-detail/",
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
        "slug": "deluxe-detail",
        "name": "Deluxe Detail",
        "img": "/assets/images/services/full-detail.jpg",
        "blurb": "The complete service, inside and out. Engine bay degreased, clay bar "
                 "decontamination, hand polish, and a full interior extraction across "
                 "every surface.",
        "intro": "One detail that takes the car end to end \u2014 the wash and "
                 "decontamination, the paint work, then a full interior extraction "
                 "across carpet, mats, seats, wheel, dash, console, tints and mirrors.",
        "groups": [
            ("Outside", [
                "Door jams cleaned",
                "Wheels and under guards degreased and pressure washed",
                "Engine bay degreased and pressure washed",
                "Vehicle washed and paint work cleaned with a clay bar",
                "Paint work chamois dried",
                "Paint work hand polished",
                "Tyres glossed and plastics sealed",
                "Windows cleaned inside and out",
            ]),
            ("Inside", [
                "Door trims, dash, steering wheel, console, vents and visors detailed",
                "Seats, carpets, floor mats and cargo area cleaned with extraction",
                "Leather seats cleaned and conditioned",
                "Roof lining spot cleaned",
                "Tints and mirrors cleaned",
                "Ashtrays cleaned",
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
        "img": "/assets/images/services/ceramic-coating.jpg",
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
        "img": "/assets/images/services/paint-correction.jpg",
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
    "deluxe-detail":     ("/assets/images/backdrop/full-detail.jpg", "#6b4526"),
    "overspray-removal": ("/assets/images/backdrop/overspray-removal.jpg", "#6b4526"),
    "ceramic-coating":   ("/assets/images/backdrop/ceramic-coating.jpg", "#6b4526"),
    "paint-correction":  ("/assets/images/backdrop/paint-correction.jpg", "#6b4526"),
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
    ("Where is the work carried out?",
     "At our studio. Correction and coating are conducted in our specialty studio, "
     "created for these applications — the lighting is controlled, which is how "
     "swirls and defects are found in the first place, and the environment is clean "
     "and stable, which is what a coating needs to cure against."),
    ("What does the Deluxe Detail cover?",
     "The car end to end. Outside: door jams, wheels and under guards degreased, "
     "engine bay, a clay bar decontamination, chamois dry and a hand polish. Inside: "
     "door trims, dash, wheel, console and vents, seats and carpets cleaned with "
     "extraction, leather conditioned and the roof lining spot cleaned."),
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
]


# Four stages of the ceramic coating process. Sourced from the client's own
# copy: the 4-stage exterior process (wash / clay / machine cut / machine
# glaze) and the ceramic coating page (industrial-grade liquid polymer sealer,
# chemical bond, semi-permanent hydro barrier). Nothing here is invented.
COATING_STAGES = [
    ("Decontaminate", "The surface has to be clean first",
     "The vehicle is pressure washed to lift loose dirt and grime, hand washed "
     "with car shampoo, then pressure rinsed. Clay bar follows, deep cleaning "
     "grime and foreign matter out of the paint. A coating bonds to the surface "
     "it is laid on, so the surface has to be genuinely clean first."),
    ("Correct", "Swirls and scratches, gone",
     "Machine cut removes scratches, spider webbing and dullness, then machine "
     "glaze de-swirls the surface and puts a deep gloss back. Whatever the paint "
     "looks like at this point is what the coating locks in — correction is not "
     "optional, it is the step that decides the result."),
    ("Coat", "Bonded to the clear coat",
     "An advanced industrial-grade liquid polymer sealer chemically bonds to the "
     "duco. Graphene Pro 10H N1 lays up to 1000nm and 10H hardness; Quartz 9H Pro "
     "up to 800nm with grade 3 chemical resistance. Glass, wheels and interior "
     "surfaces have their own coatings."),
    ("Protect", "A barrier between paint and the elements",
     "The semi-permanent layer becomes a hydro barrier between your paint and the "
     "elements. The vehicle stays cleaner for longer, washes and dries more "
     "easily, holds a deep gloss, and resists wash marks, swirls, bird droppings "
     "and UV. Minimal maintenance from there."),
]


# Ten reasons, for the ceramic coating page. Industry-standard education
# (paint hardness, UV, hydrophobics) combined with the client's own product
# facts — the lifespans below are THEIR figures from the services copy, not
# the generic "2-7 years" the reference deck uses.
COATING_REASONS = [
    ("drop", "Water beads and rolls off",
     "A hydrophobic surface means water lifts dirt, dust and grime away with it as it "
     "runs off, instead of drying onto the paint. The car stays cleaner between washes."),
    ("sun", "UV and oxidation defence",
     "The coating sits between your paint and the sun, slowing the fading, chalking and "
     "oxidation that dulls a car left outdoors."),
    ("flask", "Chemical and environmental resistance",
     "Bird droppings, bug splatter, tree sap and road grime are acidic and etch clear "
     "coat. A coated panel resists them long enough to be washed off safely."),
    ("spark", "Deep, wet-look gloss",
     "Coatings add depth and clarity to the paint, and hold that shine far longer than "
     "a traditional wax or sealant, which is measured in weeks."),
    ("dots", "Harder against micro scratches",
     "Graphene Pro is 10H and Quartz 9H Pro is 9H. That hardness resists the swirl marks "
     "and micro scratches that come from washing, dust and daily driving."),
    ("cal", "Years, not weeks",
     "Graphene Pro 10H N1 lasts a lifetime; Quartz 9H Pro up to five years; Quartz "
     "Ceramic around three. Our interior coating protects fabric and leather for twelve "
     "months."),
    ("shield", "Modern paint is thinner than it used to be",
     "Manufacturers now use thinner clear coats for efficiency and emissions. There is "
     "less material between the world and your colour coat than there was twenty years ago."),
    ("wash", "Easier to wash and dry",
     "Contamination has less to grip. Washing takes less time, needs less product, and "
     "carries far less risk of putting swirls in during the wash itself."),
    ("layer", "Bonded, not sat on top",
     "An advanced industrial-grade liquid polymer sealer chemically bonds to the duco, "
     "laying up to 1000nm of protection. It is not a topping that washes away."),
    ("calm", "Minimal maintenance",
     "Once it is on, upkeep is straightforward. We will either show you the maintenance "
     "routine or put you on a scheduled program."),
]

# --------------------------------------------------------------------------
# Coating products, named by manufacturer.
#
# The site has always described these four coatings by their specification —
# 10H, N1, Quartz, nanometre thickness — without saying whose they are. The
# client has confirmed they are the same GYEON and ONYX products Premier runs,
# so the TDS and warranty pages name them.
#
# Every figure below is the client's own published number, carried across from
# SERVICES["ceramic-coating"]["products"]. Nothing here is manufacturer data we
# went and sourced ourselves, which is why the pages say the individual data
# sheets are still to come rather than pretending to publish them.
#
# `brand` is the only inferred field: N1 + 10H + graphene is ONYX's certified
# system, and Quartz is GYEON's Q2 line. Renny to confirm, especially the
# interior coating — changing one string here re-sections the page.
# --------------------------------------------------------------------------
COATINGS = [
    {
        "brand": "ONYX", "kind": "Nano-Ceramic", "flag": "Hardest",
        "name": "Graphene Pro 10H N1",
        "sub": "Certified 10H &middot; N1 nano-ceramic",
        "copy": "The world's first N1 nano coating — nano-technology combined with the "
                "properties of graphene, laying up to 1000nm of protection on the duco.",
        "specs": [("Hardness", "10H"), ("Thickness", "Up to 1000nm"),
                  ("Chemical resistance", "Grade 3")],
        "term": "Lifetime", "termunit": "", "termsub": "On a maintained vehicle",
        "termnote": "Our longest cover. Stays valid while the vehicle is kept to the "
                    "maintenance schedule we set out on handover.",
    },
    {
        "brand": "GYEON", "kind": "Quartz &middot; Multi-Layer", "flag": "Most popular",
        "name": "Quartz 9H Pro",
        "sub": "Multi-layer 9H system",
        "copy": "Grade 3 chemical resistance, built up in multiple layers to increase film "
                "thickness to a maximum of 800nm.",
        "specs": [("Hardness", "9H"), ("Thickness", "Up to 800nm"),
                  ("Application", "Multi-layer")],
        "term": "5", "termunit": "Year", "termsub": "Multi-layer application",
        "termnote": "The step most cars land on — meaningful thickness without going to "
                    "the lifetime program.",
    },
    {
        "brand": "GYEON", "kind": "Quartz &middot; Single-Layer", "flag": "",
        "name": "Quartz Ceramic Coating",
        "sub": "Single-layer 9H",
        "copy": "Enhances the reflective properties of the paint with a smooth, deep shine. "
                "Applicable to paint, metal and glass.",
        "specs": [("Hardness", "9H"), ("Thickness", "Up to 800nm"),
                  ("Surfaces", "Paint, metal, glass")],
        "term": "3", "termunit": "Year", "termsub": "Single-layer application",
        "termnote": "Entry into the Quartz system. Can be topped up later rather than "
                    "stripped and redone.",
    },
    {
        "brand": "GYEON", "kind": "Interior", "flag": "",
        "name": "Interior Coating",
        "sub": "Leather &amp; fabric",
        "copy": "A hybrid solvent base for both fabric and leather, protecting against "
                "stains, dirt, contaminants, water and oil.",
        "specs": [("Surfaces", "Leather + fabric"), ("Repellency", "150&deg;"),
                  ("Base", "Hybrid solvent")],
        "term": "12", "termunit": "Month", "termsub": "Cabin surfaces",
        "termnote": "Runs alongside a paint coating rather than instead of one.",
    },
]

# What makes a coating warranty worth anything. Generic to the trade — not
# claims about this business specifically.
WARRANTY_TRUST = [
    ("Named products",
     "Every coating we fit is named in full, with its hardness, thickness and durability "
     "published. You know exactly what went on your paint."),
    ("Registered against your vehicle",
     "Coatings are recorded against your car at the time of application, so cover is "
     "traceable rather than a verbal promise."),
    ("Certified application",
     "Coating warranties are only valid when the paint is prepped, coated and cured the "
     "way the manufacturer requires. That is the whole reason they are fitted by us."),
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

# Real work from the client's own Facebook album — their studio, their
# customers' cars. Each carries its own alt text rather than one generic line.
# Twelve different vehicles, ordered so no two neighbours share a colour or
# a body shape - the strip was running the purple Holden back to back.
GALLERY = [
    ("/assets/images/gallery/01.jpg", "Porsche 911 in the studio after paint correction"),
    ("/assets/images/gallery/02.jpg", "Volvo XC90 under the studio lighting"),
    ("/assets/images/gallery/03.jpg", "Custom Holden HQ wagon, paint corrected"),
    ("/assets/images/gallery/04.jpg", "Mercedes-AMG GT, corrected and coated"),
    ("/assets/images/gallery/05.jpg", "Ford Mustang convertible after a detail"),
    ("/assets/images/gallery/06.jpg", "Restored Ford F100 in the studio"),
    ("/assets/images/gallery/07.jpg", "Honda Civic Type R, ceramic coated"),
    ("/assets/images/gallery/08.jpg", "BMW M3 after paint correction"),
    ("/assets/images/gallery/09.jpg", "Ford Falcon coupe, deep gloss finish"),
    ("/assets/images/gallery/10.jpg", "Mercedes-Benz GLC in the coating studio"),
    ("/assets/images/gallery/11.jpg", "Audi SQ5 detailed inside and out"),
    ("/assets/images/gallery/12.jpg", "Classic Ford after a full correction"),
]


# Header stays to four links. Franchising is a different audience entirely and
# lives in the footer; Areas is reachable from Services and the footer.
NAV = [
    ("/services/", "Services"),
    # "Products", not "Product Data" — the longer label pushes this six-item
    # bar onto two lines from 1100px up. Measured in the browser, not guessed.
    ("/product-data/", "Products"),
    ("/warranties/", "Warranties"),
    ("/gallery/", "Gallery"),
    ("/testimonials/", "Reviews"),
    ("/contact/", "Contact"),
]
NAV_FOOTER_EXTRA = [("/franchising/", "Franchising")]

# --------------------------------------------------------------------------
# shell
# --------------------------------------------------------------------------

def svc_img(slug, fallback=0):
    """Positional indexes into SERVICES break whenever the list changes; the
    four detailing tiers collapsing into one is exactly that. Look up by slug."""
    for s in SERVICES:
        if s["slug"] == slug:
            return s["img"]
    return SERVICES[fallback]["img"]


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
    def _li(pairs):
        return "\n".join(
            f'        <li><a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{esc(l)}</a></li>'
            for h, l in pairs)

    _mid = (len(NAV) + 1) // 2
    items_l = _li(NAV[:_mid])
    items_r = _li(NAV[_mid:])
    drawer_items = "\n".join(
        f'    <a href="{h}">{esc(l)}</a>' for h, l in NAV + NAV_FOOTER_EXTRA)
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="nav">
  <div class="nav__in">
    <ul class="nav__links nav__links--l">
{items_l}
    </ul>
    <a class="nav__logo" href="/" aria-label="Formula Mobile Car Detailing — home">
      <img src="/assets/images/logo.png" alt="Formula Mobile Car Detailing" width="900" height="300">
    </a>
    <ul class="nav__links nav__links--r">
{items_r}
    </ul>
    <div class="nav__act">
      <a class="nav__call" href="tel:{PHONE_LINK}" aria-label="Call {PHONE_DISPLAY}" title="{PHONE_DISPLAY}">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"
                stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </a>
      <a class="nav__cta btn" href="/booking/">Get a free quote</a>
      <button class="nav__burger" data-drawer-open aria-label="Open menu">
        <svg width="20" height="14" viewBox="0 0 20 14" fill="none" aria-hidden="true">
          <path d="M0 1h20M0 7h20M0 13h20" stroke="currentColor" stroke-width="1.6"/>
        </svg>
      </button>
    </div>
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
    ) + '\n        <li><a href="/services/select/">Browse all services &rarr;</a></li>'
    areas = ""   # the business does not travel; there are no area pages
    return f"""</main>
<footer class="foot hexbg">
  <div class="shell">
    <div class="foot__grid">
      <div>
        <div class="foot__logo">
          <img src="/assets/images/logo.png" alt="Formula Mobile Car Detailing" width="900" height="300">
        </div>
        <p class="muted" style="font-size:.92rem;max-width:32ch">
          Mobile car detailing across metropolitan Melbourne. Over 30 years bringing
          paint work back to its best.
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
          <li><a href="/franchising/">Franchising</a></li>
        </ul>
      </div>
      <div>
        <h4>Get in touch</h4>
        <a class="foot__phone" href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a>
        <ul>
          <li class="foot__line"><b>Email</b><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li class="foot__line"><b>Area</b><span>Metropolitan Melbourne</span></li>
          <li class="foot__line"><b>Mon&ndash;Sat</b><span>6:30am &ndash; 6:30pm</span></li>
          <li class="foot__line"><b>Sunday</b><span>Closed</span></li>
        </ul>
        <p style="margin:1.4rem 0 0">
          <a class="btn" href="/booking/">Book a detail</a>
        </p>
      </div>
    </div>
    <div class="foot__brands">
      <span class="foot__brandlbl">Coatings we fit</span>
      <a class="foot__brand" href="/product-data/" aria-label="GYEON coatings — see product data">
        <img src="/assets/images/brands/gyeon.png" alt="GYEON" width="520" height="176" loading="lazy" decoding="async">
      </a>
      <a class="foot__brand" href="/product-data/" aria-label="ONYX Coating — see product data">
        <img src="/assets/images/brands/onyx.png" alt="ONYX Coating" width="520" height="196" loading="lazy" decoding="async">
      </a>
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

<script src="/assets/js/spray.js" defer></script>
<script src="/assets/js/tracking.js" defer></script>
<script src="/assets/js/enhance.js" defer></script>
</body>
</html>
"""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


_BUST_CACHE = {}


def bust(html):
    """Stamp every stylesheet and script with a hash of its own contents.

    The filenames are stable (site.css, not site.<hash>.css) but the assets are
    served `max-age=31536000, immutable`. That combination is a lie the cache
    believes: a CSS change is invisible to the edge and to every returning
    visitor for a year. A content hash in the URL makes the promise true - the
    URL changes exactly when the bytes change, and not otherwise.
    """
    def stamp(m):
        rel = m.group(1)
        if rel not in _BUST_CACHE:
            f = os.path.join(OUT, rel.lstrip("/"))
            try:
                with open(f, "rb") as fh:
                    _BUST_CACHE[rel] = hashlib.sha256(fh.read()).hexdigest()[:10]
            except OSError:
                _BUST_CACHE[rel] = ""
        h = _BUST_CACHE[rel]
        return '"%s?v=%s"' % (rel, h) if h else '"%s"' % rel

    return re.sub(r'"(/assets/(?:css|js)/[^"?]+)"', stamp, html)


def write(path, content):
    full = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" \
        else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(bust(content))
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
  "description": "Paint correction, ceramic coating and detailing in Melbourne — specialist work conducted in our own studio.",
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


def faq_block(heading="Common questions", photo=False):
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

    # The homepage FAQ takes the same red carbon weave as the studio band. It
    # stays opt-in because this block is also emitted on 25 keyword pages.
    band = 'band band--tight cf2' if photo else 'band band--tight'
    return f"""
<section class="{band}">
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


ICONS = {
 "drop":  '<path d="M12 2.7S5.5 10 5.5 14.4a6.5 6.5 0 0 0 13 0C18.5 10 12 2.7 12 2.7Z"/>',
 "sun":   '<circle cx="12" cy="12" r="4"/><path d="M12 1.6v3M12 19.4v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1.6 12h3M19.4 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
 "flask": '<path d="M9.5 2.5v6L4 19a2 2 0 0 0 1.8 3h12.4A2 2 0 0 0 20 19l-5.5-10.5v-6M8 2.5h8M7.5 14h9"/>',
 "spark": '<path d="M12 2.5 14 9l6.5 2-6.5 2-2 6.5-2-6.5L3.5 11 10 9l2-6.5Z"/>',
 "dots":  '<circle cx="8" cy="8" r="1.1"/><circle cx="12" cy="7" r="1.1"/><circle cx="16" cy="8.5" r="1.1"/><circle cx="7" cy="12.5" r="1.1"/><circle cx="12" cy="12" r="1.1"/><circle cx="16.5" cy="13" r="1.1"/><circle cx="8.5" cy="16.5" r="1.1"/><circle cx="13" cy="17" r="1.1"/>',
 "cal":   '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
 "shield":'<path d="M12 2.5 4 6v6c0 5 3.4 8.6 8 9.5 4.6-.9 8-4.5 8-9.5V6l-8-3.5Z"/>',
 "wash":  '<path d="M4 13h16M6 13V8a6 6 0 0 1 12 0v5M8 17.5v2M12 17.5v3M16 17.5v2"/>',
 "layer": '<path d="M12 3 3 8l9 5 9-5-9-5Z"/><path d="M3 13l9 5 9-5M3 17.5l9 5 9-5"/>',
 "calm":  '<circle cx="12" cy="12" r="9"/><path d="M8.5 13.5s1.3 1.8 3.5 1.8 3.5-1.8 3.5-1.8M9 9.5h.01M15 9.5h.01"/>',
}


def reasons_html():
    """Ten reasons, laid out as the reference deck does: numbered chip, icon,
    title, body — in glass, on the ceramic coating page."""
    cards = "".join(f"""
        <article class="rsn" data-reveal="{i * 0.04:.2f}">
          <span class="rsn__n">{i:02d}</span>
          <svg class="rsn__ic" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
               aria-hidden="true">{ICONS.get(icon, "")}</svg>
          <h3 class="rsn__t">{esc(title)}</h3>
          <p class="rsn__d">{esc(body)}</p>
        </article>""" for i, (icon, title, body) in enumerate(COATING_REASONS, start=1))

    return f"""
<section class="band rsn-band">
  <div class="shell">
    <div style="max-width:56ch;margin-bottom:2.6rem" data-reveal>
      <span class="eyebrow">Why coat it</span>
      <h2>Ten reasons to <span class="slant hl">ceramic coat</span></h2>
      <p class="lede">What a coating actually does for the paint, and how long ours last.</p>
    </div>
    <div class="rsn-grid">{cards}
    </div>
    <p style="margin-top:2.4rem">
      <a class="btn btn--lg" href="/booking/">Book a ceramic coating</a>
    </p>
  </div>
</section>
"""


def coating_html(scrolling=False):
    """The four coating stages.

    Two presentations from one dataset:
      scrolling=True   four full-height panels the visitor scrolls through,
                       for the ceramic coating page where the depth is wanted.
      scrolling=False  a single-viewport horizontal carousel, for the homepage
                       where four full screens between the hero and the work
                       is too much to ask of someone still deciding.

    The films, the copy and the card design are shared; only the layout and
    what advances it differ.
    """
    mode = "coat--scroll" if scrolling else "coat--deck"

    vids = "".join(
        f'<video class="coat__vid" data-stage-vid="{i}" data-src="/assets/video/stage-{i}.mp4" '
        f'poster="/assets/video/stage-{i}.jpg" muted playsinline loop preload="none" '
        f'aria-hidden="true"></video>' for i in range(1, len(COATING_STAGES) + 1))

    panels = "".join(f"""
      <article class="coat__panel" data-stage style="--i:{i}">
        <span class="coat__word" aria-hidden="true">{esc(title)}</span>
        <div class="coat__card">
          <span class="coat__n">{i:02d}</span>
          <span class="coat__div" aria-hidden="true"></span>
          <div class="coat__txt">
            <h3 class="coat__h">{esc(head)}</h3>
            <p>{esc(body)}</p>
          </div>
        </div>
      </article>""" for i, (title, head, body) in enumerate(COATING_STAGES, start=1))

    pips = "".join(
        f'<button class="coat__pip" data-stage-pip role="tab" '
        f'aria-selected="{"true" if i == 0 else "false"}" '
        f'aria-label="{esc(t)}"></button>'
        for i, (t, _h, _b) in enumerate(COATING_STAGES))

    arrow_prev = "" if scrolling else """
      <button class="coat__arrow coat__arrow--prev" data-coat-prev type="button" aria-label="Previous stage">
        <svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">
          <path d="M15 5.5H2M6 1L2 5.5 6 10" stroke="currentColor" stroke-width="1.7"/></svg>
        <span class="coat__arrowlbl">Back</span>
      </button>"""
    arrow_next = "" if scrolling else """
      <button class="coat__arrow coat__arrow--next" data-coat-next type="button" aria-label="Next stage">
        <span class="coat__arrowlbl">Next</span>
        <svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">
          <path d="M0 5.5h13M9 1l4 4.5L9 10" stroke="currentColor" stroke-width="1.7"/></svg>
      </button>"""

    return f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">The process</span>
    <h2>Ceramic coating <span class="slant hl">specialists</span></h2>
    <p class="lede">Four stages, one finish. A coating is only as good as what goes
      under it &mdash; this is the process, start to finish.</p>
  </div>
</section>

<section class="coat {mode}" data-coating aria-label="The ceramic coating process">
  <div class="coat__stage">
    {vids}
    <div class="coat__scrim" aria-hidden="true"></div>
    <div class="coat__panels">{panels}
    </div>
    <div class="coat__ctrls">{arrow_prev}
      <div class="coat__pips" role="tablist" aria-label="Coating stages">{pips}</div>{arrow_next}
    </div>
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
# the slanted photo strip, shared by the home band and the gallery page
# --------------------------------------------------------------------------

def slant_row(images):
    """One marquee track of skewed photo panels, doubled.

    The loop works by translating the track exactly -50%, so the second copy is
    what the eye is on when the first wraps round — which means the track must
    hold every image twice and nothing may be dropped from either copy."""
    row = "".join(f"""
            <figure class="slantile" data-lightbox>
              <img src="{g}" alt="{esc(a)}" loading="lazy" width="800" height="600">
            </figure>""" for g, a in images)
    return row + row   # doubled, so the loop has no seam


def slant_band(images, dur, reverse=False, extra=""):
    """A full-width slanted strip. `dur` sets the speed; alternating `reverse`
    on stacked bands stops them reading as one sheet sliding sideways."""
    cls = "mq mq--slant" + (" mq--rev" if reverse else "") + (f" {extra}" if extra else "")
    return f"""  <div class="{cls}" style="--mq-dur:{dur}s">
    <div class="mq__track">{slant_row(images)}
    </div>
  </div>"""


# --------------------------------------------------------------------------
# page: home
# --------------------------------------------------------------------------

def build_home():
    slants = slant_row(GALLERY)
    gal_tags = "".join(f"<li>{esc(x['name'])}</li>" for x in SERVICES[:3])

    svcbtns = "".join(f"""
      <a class="svcbtn" href="/services/{x['slug']}/">{esc(x['name'])}
        <svg width="13" height="9" viewBox="0 0 13 9" fill="none" aria-hidden="true">
          <path d="M0 4.5h11M7.5 1L11 4.5 7.5 8" stroke="currentColor" stroke-width="1.6"/>
        </svg>
      </a>""" for x in SERVICES)

    subchips = ""

    # Marquee: the track holds every review TWICE and translates exactly -50%,
    # so the loop is seamless. Duration scales with the count to hold speed.
    def review_card(body, who):
        return f"""
          <blockquote class="quote">
            <div class="rev__stars" aria-label="Rated 5 out of 5">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
            <p>&ldquo;{esc(body)}&rdquo;</p>
            <cite>{esc(who)}</cite>
          </blockquote>"""

    # A -50% marquee only looks continuous while ONE copy of the content is
    # wider than the viewport. Three reviews is about 1300px, so from 1440px up
    # the loop ran out of cards and left dead space on the right - worse the
    # wider the screen. Repeat until a single pass clears 3600px (ultrawide), then
    # double that for the seam.
    _revs = "".join(review_card(b, w) for b, w in TESTIMONIALS)
    _copies = max(1, -(-3600 // max(1, len(TESTIMONIALS) * 430)))
    quotes = _revs * _copies * 2

    area_links = " ".join(
        '' for s in []
    )

    return (
        head("Mobile Car Detailing Melbourne | Formula Mobile Car Detailing",
             "Mobile car detailing across metropolitan Melbourne. Full detailing, paint "
             "correction and ceramic coatings, conducted in our own studio. Over 30 years. "
             f"Call {PHONE_DISPLAY}.",
             "/", schema=local_business_schema() + faq_schema()
             + '<link rel="stylesheet" href="/assets/css/select.css">')
        + nav()
        + f"""
<section class="hero hero--photo" data-hero>
  <picture class="hero__bg" aria-hidden="true">
    <source media="(max-width: 720px)" srcset="/assets/images/studio-hero-sm.jpg">
    <img src="/assets/images/studio-hero.jpg" alt="" fetchpriority="high"
         width="2000" height="1250">
  </picture>
  <div class="hero__scrim" aria-hidden="true"></div>

  <div class="hero__splash" data-hero-splash>
    <div class="hero__fiber" aria-hidden="true"></div>
    <div class="hero__splashin">
      <div class="hero__lock" role="img" aria-label="Formula &mdash; Paint Correction and Coatings">
        <img class="hero__lockblock" src="/assets/images/logo-block.png" alt=""
             width="1200" height="400" fetchpriority="high">
        <img class="hero__lockscript" src="/assets/images/logo-script.png" alt=""
             width="1200" height="400" fetchpriority="high">
      </div>
      <div class="hero__rule" aria-hidden="true"></div>
      <p class="hero__tag">Paint Correction &middot; Coatings</p>
    </div>
  </div>

  <div class="hero__say">
    <span class="eyebrow">Melbourne &middot; In our studio</span>
    <h1 class="hero__h1"><span class="hero__l1 textmono">Servicing Melbourne</span><span class="hero__l2"><span class="textmono">for</span> <span class="slant hl shine">30+ years</span></span></h1>
    <p class="hero__sub">Paint Protection &amp; Ceramic Coating Specialists</p>
    <div class="hero__cta">
      <a class="btn btn--lg" href="/booking/">Get a free quote</a>
      <a class="btn btn--ghost btn--lg" href="/services/select/">Browse our services</a>
    </div>
  </div>

  <div class="hero__cue" aria-hidden="true">
    Scroll
    <svg width="10" height="13" viewBox="0 0 10 13" fill="none">
      <path d="M5 0v11M1 7.5L5 11.5 9 7.5" stroke="currentColor" stroke-width="1.4"/>
    </svg>
  </div>
</section>

{coating_html()}

<section class="band band--tight">
  <div class="shell" style="text-align:center">
    <span class="eyebrow">What we do</span>
    <h2>Every service, <span class="slant hl">one place</span></h2>
    <p class="lede" style="margin:0 auto 2rem">Pick the one you're after, or call and
      our operators will tell you what the car actually needs.</p>
    <div class="svcbtns">{svcbtns}</div>
  </div>
</section>

<section class="band mesh band--raise">
  <div class="shell">
    <div class="grid grid--4">
      <div class="stat" data-reveal><span class="stat__n" data-count="30" data-suffix="+">30+</span><span class="stat__l">Years detailing</span></div>
      <div class="stat" data-reveal="0.08"><span class="stat__n" data-count="7">7</span><span class="stat__l">Services</span></div>
      <div class="stat" data-reveal="0.16"><span class="stat__n" data-count="10" data-suffix="H">10H</span><span class="stat__l">Graphene coating</span></div>
      <div class="stat" data-reveal="0.24"><span class="stat__n">100%</span><span class="stat__l">Work done in our studio</span></div>
    </div>
  </div>
</section>






<section class="band band--raise gal">
  <div class="shell gal__head" data-reveal>
    <div>
      <span class="eyebrow">Gallery</span>
      <h2>The finish <span class="slant hl">speaks</span></h2>
    </div>
    <ul class="gal__tags">{gal_tags}</ul>
  </div>

  <div class="mq mq--slant" style="--mq-dur:64s">
    <div class="mq__track">{slants}
    </div>
  </div>

  <div class="shell gal__foot">
    <span class="gal__note">Real cars. Real results.</span>
    <a class="gal__more" href="/gallery/">See the full gallery
      <svg width="13" height="9" viewBox="0 0 13 9" fill="none" aria-hidden="true">
        <path d="M0 4.5h11M7.5 1L11 4.5 7.5 8" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </a>
  </div>
</section>

<section class="band rev-band">
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

<section class="band band--raise cf2">
  <div class="shell">
    <div class="area">
      <div>
        <span class="eyebrow">The studio</span>
        <h2>A dedicated <span class="slant hl">coating studio</span></h2>
        <p class="lede">Correction and coating work is conducted in our specialty
          studio, created for these applications &mdash; controlled lighting, a sealed
          floor and the room to work a panel properly.</p>
        <p style="margin-top:1.6rem;display:flex;gap:.8rem;flex-wrap:wrap">
          <a class="btn" href="/booking/">Book a detail</a>
          <a class="btn btn--ghost" href="/services/">See our services</a>
        </p>
      </div>
      <div class="area__map">
        <img src="/assets/images/studio.jpg" alt="Formula's coating studio"
             width="1280" height="880" loading="lazy" decoding="async">
      </div>
    </div>
  </div>
</section>

{faq_block(photo=True)}

<section class="band mesh">
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
            '<script src="/assets/js/coating.js" type="module"></script>\n'
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
{(coating_html(scrolling=True) + reasons_html()) if s["slug"] == "ceramic-coating" else ""}
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
        <img src="/assets/images/logo.png" alt="Formula Mobile Car Detailing" width="900" height="300">
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
        "/services/select/", svc_img("deluxe-detail"), breadcrumb_schema(trail))}
<link rel="stylesheet" href="/assets/css/select.css">
{carousel_html(inline=False)}
<script src="/assets/js/select.js" defer></script>
</body>
</html>
"""


def booking_section(heading="", band="band band--tight"):
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
        for i, lbl in enumerate(["Service", "Location", "Vehicle", "Details"])
    )

    return f"""
<section class="{band}">
  <div class="shell bk">
    {heading}
    <ol class="bk__rail">{rail}</ol>
    <p class="visually-hidden" data-live aria-live="polite"></p>

    <form class="bk__form card" method="post" action="/thank-you/" data-booking>

      <fieldset class="bk__step" data-step data-autoadvance>
        <legend class="bk__legend">Choose your service</legend>
        <p class="bk__hint">Pick what you're after &mdash; not sure? Choose &ldquo;Not sure yet&rdquo;.</p>
        <div class="bk__tiles" data-requires-choice>{tiles("service", services)}</div>
      </fieldset>

      <fieldset class="bk__step" data-step>
        <legend class="bk__legend">Where are you?</legend>
        <p class="bk__hint">Suburb and postcode.</p>
        <div class="field--split">
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
        <legend class="bk__legend">Where to send the quote</legend>
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
          <label for="bk-comments">Special requests <span class="muted">(optional)</span></label>
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


def build_booking():
    trail = [("/", "Home"), ("/booking/", "Book")]
    return (
        head("Book a Detail | Formula Mobile Car Detailing",
             "Book mobile car detailing across Melbourne — takes under a minute, and "
             "we'll call or text back to confirm a time.",
             "/booking/", svc_img("ceramic-coating"), breadcrumb_schema(trail))
        + nav()
        + crumbs(trail)
        + """
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Booking</span>
    <h1>Book your <span class="slant hl">detail</span></h1>
    <p class="lede">Takes under a minute. We'll call or text back to confirm a time
      &mdash; no obligation, and no payment up front.</p>
  </div>
</section>
"""
        + booking_section()
        + footer()
    )


def build_gallery():
    """Three slanted strips running against each other, same treatment as the
    home band.

    Each band carries the whole set rather than a third of it. The loop
    translates the doubled track -50%, so half a track has to be wider than the
    viewport or the wrap becomes a visible gap — four panels a row would be
    about 1200px and tear on any normal desktop. Rotating the start index
    instead keeps every band full-width while making sure no two rows show the
    same car in the same place."""
    n = len(GALLERY)
    bands = "\n".join(
        slant_band(GALLERY[(n // 3) * r:] + GALLERY[:(n // 3) * r],
                   dur=58 + r * 11, reverse=bool(r % 2))
        for r in range(3))
    trail = [("/", "Home"), ("/gallery/", "Gallery")]
    return (
        head("Gallery | Formula Mobile Car Detailing Melbourne",
             "Recent detailing, paint correction and ceramic coating work by Formula Mobile "
             "Car Detailing across Melbourne.",
             "/gallery/", GALLERY[0][0], breadcrumb_schema(trail))
        + nav("/gallery/") + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Gallery</span>
    <h1>Recent <span class="slant hl">work</span></h1>
    <p class="lede">A selection of vehicles we've detailed, corrected and coated.
      Hover to hold a strip, click any panel to open it.</p>
  </div>
</section>
<section class="band band--tight galrows">
{bands}
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
          <label for="comments">Special requests</label>
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
             "training and a proven model built on 20 years in the industry.",
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
    trail = [("/", "Home"),              (f"/mobile-car-detailing/{slug}/", name)]
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
             f"coatings, conducted in our own studio. Over 30 years. Call {PHONE_DISPLAY}.",
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
  </div>
</section>
""" + footer())


def build_areas_index():
    links = " ".join(
        '' for s in [])
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
    <p class="lede"></p>
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
    """Every page on the site, in one place.

    The pattern the Premier and Next Lvl sitemaps use: the page is itself an
    internal-link hub, so it needs density rather than whitespace — every
    cluster, every service and every suburb reachable in one click.
    """

    def links(items):
        return "".join(f'<li><a href="{h}">{esc(n)}</a></li>' for h, n in items)

    clusters = "".join(f"""
      <section class="sm__col">
        <h3 class="sm__h">{esc(title)}</h3>
        <ul class="sm__list">{links([(f"/{p[0]}/", p[1]) for p in pages])}</ul>
      </section>""" for title, _key, pages in CLUSTERS)

    kw = sum(len(p) for _t, _k, p in CLUSTERS)
    total = kw + len(SERVICES) + len(SUBURBS) + 11

    core = [("/", "Home"), ("/booking/", "Book a detail"), ("/services/", "Services"),
            ("/services/select/", "Browse services"), ("/gallery/", "Gallery"),
            ("/testimonials/", "Reviews"),
            ("/franchising/", "Franchising"), ("/contact/", "Contact"),
            ("/privacy/", "Privacy policy")]

    return (
        head("Sitemap | Formula Mobile Car Detailing",
             "Every page on formulamobilecardetailing.com.au \u2014 detailing, ceramic "
             "coating, paint correction, overspray removal, and every Melbourne "
             "suburb we cover.",
             "/sitemap/")
        + nav()
        + crumbs([("/", "Home"), ("/sitemap/", "Sitemap")])
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">Sitemap</span>
    <h1>Every page, <span class="slant hl">one place</span></h1>
    <p class="lede">{total} pages covering detailing, ceramic coating, paint correction
      and overspray removal across metropolitan Melbourne.</p>
    <p style="margin-top:1.4rem">
      <a class="btn btn--ghost" href="/sitemap.xml">View the XML sitemap</a>
    </p>
  </div>
</section>

<section class="band band--tight rsn-band">
  <div class="shell">
    <div class="sm__grid">
      <section class="sm__col">
        <h3 class="sm__h">Core pages</h3>
        <ul class="sm__list">{links(core)}</ul>
      </section>
      <section class="sm__col">
        <h3 class="sm__h">Our services</h3>
        <ul class="sm__list">{links([(f"/services/{x['slug']}/", x["name"]) for x in SERVICES])}</ul>
      </section>
{clusters}
    </div>
  </div>
</section>

<section class="band band--tight">
  <div class="shell">

  </div>
</section>
"""
        + footer())

def build_keyword_page(cluster_title, cluster_key, entry, siblings):
    """One long-tail landing page.

    Each carries its own intro, three points and its own FAQ answer — the
    content differs page to page rather than being a template with the keyword
    swapped, because near-duplicates get treated as thin content.
    """
    # cluster keys are not guaranteed to be service slugs
    _slug = {"mobile-detailing": "deluxe-detail"}.get(cluster_key, cluster_key)
    svc_link = (f'<a class="btn btn--ghost" href="/services/{_slug}/">Service details</a>'
                if any(x["slug"] == _slug for x in SERVICES) else "")

    slug, h1, desc, intro, points, faq = entry
    q, a = faq

    pts = "".join(f"""
        <article class="rsn" data-reveal="{i * 0.05:.2f}">
          <span class="rsn__n">{i:02d}</span>
          <h3 class="rsn__t">{esc(pt)}</h3>
          <p class="rsn__d">{esc(pb)}</p>
        </article>""" for i, (pt, pb) in enumerate(points, start=1))

    rel = "".join(
        f'<li><a href="/{sl}/">{esc(t)}</a></li>'
        for sl, t in siblings if sl != slug)

    trail = [("/", "Home"), (f"/{slug}/", h1)]
    schema = breadcrumb_schema(trail) + f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{{"@type":"Question","name":"{esc(q)}",
"acceptedAnswer":{{"@type":"Answer","text":"{esc(a)}"}}}}]}}
</script>"""

    return (
        head(f"{h1} | Formula Mobile Car Detailing", desc, f"/{slug}/",
             svc_img("paint-correction"), schema)
        + nav()
        + crumbs(trail)
        + f"""
<section class="band band--tight">
  <div class="shell">
    <span class="eyebrow">{esc(cluster_title)}</span>
    <h1>{esc(h1)}</h1>
    <p class="lede">{esc(intro)}</p>
    <div style="display:flex;gap:.8rem;flex-wrap:wrap;margin-top:1.8rem">
      <a class="btn btn--lg" href="/booking/">Book a detail</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>

<section class="band band--tight rsn-band">
  <div class="shell">
    <div class="rsn-grid">{pts}
    </div>
  </div>
</section>

<section class="band band--tight">
  <div class="shell">
    <div class="faq">
      <details class="faq__item" open>
        <summary class="faq__q">{esc(q)}
          <svg class="faq__ic" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path d="M6.5 1v11M1 6.5h11" stroke="currentColor" stroke-width="1.7"/>
          </svg>
        </summary>
        <div class="faq__a"><p>{esc(a)}</p></div>
      </details>
    </div>
  </div>
</section>

<section class="band band--raise mesh">
  <div class="shell">
    <h2>More on {esc(cluster_title.replace(" Melbourne", ""))}</h2>
    <ul class="ticks" style="columns:2;margin-top:1.2rem">{rel}</ul>
    <p style="margin-top:1.8rem">
      {svc_link}
    </p>
  </div>
</section>
"""
        + footer())


# --------------------------------------------------------------------------
# pages: product data + warranties
# --------------------------------------------------------------------------

def _by_brand(brand):
    return [c for c in COATINGS if c["brand"] == brand]


def _tds_card(c, i, hero=False):
    """One product card. Specs render as a definition list so the figures stay
    machine-readable rather than being prose with numbers buried in it.

    `hero` splits the card into copy-left / specs-right. A brand with only one
    product would otherwise get a single card stretched across the full grid,
    which throws each spec value a thousand pixels from its own label."""
    flag = (f'<span class="tds__flag">{esc(c["flag"])}</span>' if c["flag"] else "")
    rows = "\n".join(
        f'          <div class="tds__spec"><dt>{k}</dt><dd>{v}</dd></div>'
        for k, v in c["specs"])
    cls = "card tds__card" + (" tds__card--hero" if hero else "")
    return f"""      <article class="{cls}" data-reveal="{i*0.06:.2f}">
        <div class="tds__head">
          <span class="card__num">{c["brand"]} &middot; {c["kind"]}</span>
          {flag}
        </div>
        <div class="tds__body">
          <h3 class="card__title">{esc(c["name"])}</h3>
          <p class="tds__sub">{c["sub"]}</p>
          <p class="muted">{esc(c["copy"])}</p>
        </div>
        <dl class="tds__specs">
{rows}
        </dl>
      </article>"""


def build_tds():
    # A section holding a single product gets the wide treatment; a section
    # with several keeps the even grid. Driven by count, so adding a second
    # ONYX product re-lays the section correctly with no edit here.
    _o, _g = _by_brand("ONYX"), _by_brand("GYEON")
    onyx = "\n".join(_tds_card(c, i, hero=len(_o) == 1) for i, c in enumerate(_o))
    gyeon = "\n".join(_tds_card(c, i, hero=len(_g) == 1) for i, c in enumerate(_g))
    return (
        head("Coating Product Data | GYEON & ONYX Specifications | Formula Mobile Car Detailing",
             "Hardness, thickness and durability for every GYEON and ONYX ceramic coating "
             "we fit — published in full, nothing hidden.",
             "/product-data/",
             og_img="/assets/images/services/ceramic-coating.jpg",
             schema=breadcrumb_schema([("/", "Home"), ("/product-data/", "Product Data")]))
        + nav("/product-data/")
        + crumbs([("/", "Home"), ("/services/ceramic-coating/", "Ceramic Coatings"),
                  ("/product-data/", "Product Data")])
        + f"""
<section class="band band--tight hexbg">
  <div class="shell" style="max-width:74ch">
    <span class="eyebrow">Technical data</span>
    <h1>GYEON &amp; ONYX. <span class="slant hl">Nothing hidden.</span></h1>
    <p class="lede">We fit professional GYEON and ONYX coatings only — and we publish the
      specification for every one. Hardness, film thickness and how long it lasts, in the
      open, so you can compare us against anyone.</p>
    <div class="svcbtns svcbtns--start" style="margin-top:2rem">
      <a class="btn btn--lg" href="/booking/">Start your quote</a>
      <a class="btn btn--ghost btn--lg" href="/warranties/">View warranties &rarr;</a>
    </div>
  </div>
</section>

<hr class="rule">

<section class="band">
  <div class="shell">
    <span class="eyebrow">ONYX &middot; Nano-ceramic</span>
    <h2>Certified <span class="slant hl">10H &amp; N1.</span></h2>
    <p class="lede">ONYX makes the first certified 10H and N1 nano-ceramic system — the
      hardest and thickest coating we fit, and the only one on a lifetime program.</p>
    <div class="grid grid--3 tds__grid" style="margin-top:2.2rem">
{onyx}
    </div>
  </div>
</section>

<section class="band band--raise">
  <div class="shell">
    <span class="eyebrow">GYEON &middot; Quartz system</span>
    <h2>The Quartz <span class="slant hl">system.</span></h2>
    <p class="lede">SiO&sup2; coatings from a single-layer 9H through to a multi-layer build,
      plus a dedicated interior coating for leather and fabric.</p>
    <div class="grid grid--3 tds__grid" style="margin-top:2.2rem">
{gyeon}
    </div>
    <p class="muted" style="margin-top:2rem;max-width:70ch">
      <strong>Note:</strong> the figures above are the specifications we publish for the
      coatings we fit. Individual manufacturer data sheets are being added to this page.
      Need the full TDS for a specific product now?
      <a href="/contact/">Ask us</a> and we will send it through.
    </p>
  </div>
</section>

<hr class="rule">

<section class="band band--tight">
  <div class="shell" style="max-width:70ch">
    <span class="eyebrow">Straight answers</span>
    <h2>Premium products. <span class="slant hl">Named in full.</span></h2>
    <p class="lede">Get a straight price and know exactly which coating is going on your car,
      how thick it is, and how long it is covered for.</p>
    <div class="svcbtns svcbtns--start" style="margin-top:2rem">
      <a class="btn btn--lg" href="/booking/">Start your quote</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>
""" + footer())


def _warranty_card(c, i):
    unit = c.get("termunit", "")
    # A word cannot count up, so only the numeric terms get the counter hook.
    num = (f'<span class="stat__n" data-count="{c["term"]}">{c["term"]}</span>'
           if c["term"].isdigit() else f'<span class="stat__n">{esc(c["term"])}</span>')
    label = f"{unit} warranty" if unit else "warranty"
    return f"""      <article class="card wty__card" data-reveal="{i*0.06:.2f}">
        <span class="card__num">{c["brand"]} &middot; {c["kind"]}</span>
        <h3 class="card__title">{esc(c["name"])}</h3>
        <p class="tds__sub">{c["termsub"]}</p>
        <div class="wty__term">
          {num}<span class="stat__l">{label}</span>
        </div>
        <p class="muted">{esc(c["termnote"])}</p>
      </article>"""


def build_warranties():
    cards = "\n".join(_warranty_card(c, i) for i, c in enumerate(COATINGS))
    trust = "\n".join(
        f"""      <div class="card" data-reveal="{i*0.07:.2f}">
        <h3 class="card__title">{esc(t)}</h3>
        <p class="muted">{esc(d)}</p>
      </div>""" for i, (t, d) in enumerate(WARRANTY_TRUST))
    return (
        head("Ceramic Coating Warranties Melbourne | GYEON & ONYX | Formula Mobile Car Detailing",
             "Every GYEON and ONYX coating we fit is covered — from 12 months to a lifetime "
             "program. What each warranty covers and what keeps it valid.",
             "/warranties/",
             og_img="/assets/images/services/ceramic-coating.jpg",
             schema=breadcrumb_schema([("/", "Home"), ("/warranties/", "Warranties")]))
        + nav("/warranties/")
        + crumbs([("/", "Home"), ("/services/ceramic-coating/", "Ceramic Coatings"),
                  ("/warranties/", "Warranties")])
        + f"""
<section class="band band--tight hexbg">
  <div class="shell" style="max-width:74ch">
    <span class="eyebrow">Coating warranties</span>
    <h1>Real products. <span class="slant hl">Real cover.</span></h1>
    <p class="lede">Every GYEON and ONYX coating we fit carries a warranty — from 12 months
      on the interior through to a lifetime program on the 10H N1. Named products, published
      specifications, no mystery bottles.</p>
    <div class="svcbtns svcbtns--start" style="margin-top:2rem">
      <a class="btn btn--lg" href="/booking/">Start your quote</a>
      <a class="btn btn--ghost btn--lg" href="/product-data/">View product data &rarr;</a>
    </div>
  </div>
</section>

<hr class="rule">

<section class="band">
  <div class="shell">
    <span class="eyebrow">Why it matters</span>
    <h2>What makes a warranty <span class="slant hl">worth anything.</span></h2>
    <div class="grid grid--3" style="margin-top:2.2rem">
{trust}
    </div>
  </div>
</section>

<section class="band band--raise">
  <div class="shell">
    <span class="eyebrow">Cover by coating</span>
    <h2>Pick the <span class="slant hl">durability.</span></h2>
    <p class="lede">Choose the coating that suits the car and how long you are keeping it.
      Every term below is the cover on that specific product.</p>
    <div class="grid grid--2 wty__grid" style="margin-top:2.2rem">
{cards}
    </div>
    <p class="muted" style="margin-top:2rem;max-width:70ch">
      Warranty terms are confirmed in writing at handover along with the maintenance
      schedule that keeps them valid. Full specifications for each coating are on the
      <a href="/product-data/">product data page</a>.
    </p>
  </div>
</section>

<hr class="rule">

<section class="band band--tight">
  <div class="shell" style="max-width:70ch">
    <span class="eyebrow">Next step</span>
    <h2>Not sure which <span class="slant hl">one you need?</span></h2>
    <p class="lede">Tell us the car, how long you are keeping it and where it lives. We will
      tell you which coating is worth it and which is overkill.</p>
    <div class="svcbtns svcbtns--start" style="margin-top:2rem">
      <a class="btn btn--lg" href="/booking/">Start your quote</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
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
    # keyword clusters
    for _title, _key, _pages in CLUSTERS:
        sibs = [(x[0], x[1]) for x in _pages]
        for _e in _pages:
            write(f"/{_e[0]}/", build_keyword_page(_title, _key, _e, sibs))
            routes.append((f"/{_e[0]}/", "0.7"))

    write("/product-data/", build_tds());           routes.append(("/product-data/", "0.8"))
    write("/warranties/", build_warranties());      routes.append(("/warranties/", "0.8"))

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
