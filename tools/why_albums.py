# -*- coding: utf-8 -*-
"""Copied from the CDS site (tools/why/albums.py): Pndulum creative with no detailer
branding, so the slides are shared. Reasons 1 and 7 carry FORMULA's own lifespan figures.

The four text-behind-vehicle education albums shown in the homepage #why-ceramic
section. Single source of truth for convert.py and build_why.py.

Each slide: (source number, keyword on the slide, the slide's headline). The headline
doubles as the alt text and the lightbox caption, so the copy baked into the artwork
also exists as real text. Pndulum creative; the slides carry no detailer branding.

Prado slide 05 (WHEELS) is left out: its body copy has a typo baked into the artwork
("prope protection"). Add (5, "Wheels", "...") back once a corrected PNG exists.
"""
ALBUMS = [
    ("shark6", "BYD Shark 6", "Ceramic coating, explained", [
        (1, "Shark 6", "Ceramic coating explained: a protective layer over the paint that reduces grime build-up and makes cleaning easier"),
        (2, "Modern", "Protect newer paint early, before road film, dust and moisture get a hold"),
        (3, "Gloss", "Enhanced gloss and richer depth, without changing the colour of the paint"),
        (4, "Durability", "Daily contamination is easier to manage: road film, bug splatter, bird mess and fallout clean away sooner"),
        (5, "Hydrophobic", "Water beads and releases more easily, carrying loose grime away with it"),
        (6, "Cleaner", "Routine washing becomes easier, quicker and gentler on the finish"),
        (7, "Protect", "Support against UV exposure, oxidation and weathering"),
        (8, "Clarity", "Cleaner presentation after rain: the surface sheds water and stays tidier"),
        (9, "Ready?", "Protect your BYD Shark 6 before daily driving leaves its mark"),
    ]),
    ("modely", "Tesla Model Y", "Why EV paint needs it early", [
        (1, "Model Y", "Tesla Model Y ceramic coating guide"),
        (2, "Ceramic coating", "Ceramic coating: easier cleaning, lasting gloss"),
        (3, "Model Y", "Keep the new-car finish, longer"),
        (4, "Softer EV paint?", "Softer EV paint: water-based chemistry, thinner application, more prone to swirls and chips"),
        (5, "Why protect it early?", "Why protect it early: road film builds up fast, wash marring shows sooner, prevention beats correction"),
        (6, "Water beading", "Water beading: less dirt sticks, easier washes"),
        (7, "Easier to clean", "Easier to clean: hydrophobic protection helps grime release faster"),
        (8, "Protect your Model Y", "Protect your Model Y: less maintenance, better gloss, a longer-lasting finish"),
    ]),
    ("model3", "Tesla Model 3", "A detailing diagnosis, panel by panel", [
        (43, "Model 3", "Detailing diagnosis: dark paint, white seats, glass and trim all benefit from tailored protection"),
        (44, "Rear", "Rear sections trap road film"),
        (45, "Trim", "Gloss trim marks easily"),
        (46, "Cabin", "Minimal cabins show touch marks"),
        (47, "Seats", "White seats need gentle maintenance"),
        (48, "Front", "Front ends collect the mess first"),
        (49, "Gloss", "Sharper reflections need safer washing"),
        (50, "Glass", "Large glass areas show spotting"),
        (51, "Profile", "Daily driving leaves its mark"),
        (52, "Protection", "Protection makes upkeep easier"),
    ]),
    ("prado", "LandCruiser Prado", "Big panels, daily driving", [
        (2, "Presence", "Big panels reward proper protection"),
        (3, "Rear", "The rear end wears road film quickly"),
        (4, "Finish", "Sharper reflections start with better prep"),
        (7, "Protected", "A protected finish suits daily driving"),
        (8, "Detail", "Small details lift the whole finish"),
    ]),
]
SOURCE_NAME = {"shark6": "BYD Shark 6", "modely": "Tesla Model Y", "model3": "Tesla Model 3", "prado": "Toyota LandCruiser Prado"}

# ---------------------------------------------------------------------------------------
# The section is organised by REASON, not by vehicle: eight compact pills, each with its one
# line of copy and a carousel mixed across all four albums. (title, pill label, ghost keyword
# drawn behind the slide row, copy, [(album slug, 1-based slide index), ...]).
# Slides are ordered to alternate cars; every one of the 32 slides appears at least once -
# build_why.py fails if one is orphaned. The copy is the section's original eight cards.
REASONS = [
    ("Years of protection", "Protection", "Protection",
     "Bonds to the clear coat and outlasts wax and sealant by years, not months: Graphene Pro 10H N1 is rated for life, Quartz 9H Pro up to five years.",
     [("shark6", 1), ("modely", 3), ("prado", 4), ("model3", 10), ("shark6", 9), ("modely", 8)]),
    ("Hydrophobic", "Hydrophobic", "Hydrophobic",
     "Rain and water bead up and sheet straight off, carrying dirt and grime away with them.",
     [("modely", 6), ("shark6", 5), ("model3", 8), ("shark6", 8), ("prado", 1)]),
    ("Easier to wash", "Easy wash", "Effortless",
     "Dirt, mud and road salt struggle to stick, so every wash is faster, safer and needed less often.",
     [("shark6", 6), ("modely", 7), ("model3", 2), ("prado", 2), ("modely", 2), ("model3", 9)]),
    ("UV & fade defence", "UV defence", "UV shield",
     "Blocks the UV radiation that oxidises paint and leaves it looking dull, chalky and faded.",
     [("shark6", 7), ("modely", 4), ("shark6", 2), ("modely", 5)]),
    ("Stain resistance", "Stain resistance", "Resistant",
     "Bird droppings, bug splatter, tree sap and acidic fallout are far less likely to etch the clear coat.",
     [("shark6", 4), ("model3", 6), ("model3", 4), ("model3", 5), ("model3", 8)]),
    ("Deeper gloss", "Deep gloss", "Gloss",
     "Magnifies the reflectivity of your paint for a rich, wet, mirror-like finish that turns heads.",
     [("model3", 7), ("shark6", 3), ("prado", 3), ("model3", 3), ("prado", 5), ("modely", 2)]),
    ("No more waxing", "No waxing", "No wax",
     "No re-waxing or resealing every few months \u2014 even our entry Quartz Ceramic runs around three years.",
     [("modely", 8), ("model3", 10), ("shark6", 6), ("prado", 4)]),
    ("Holds resale value", "Resale value", "Value",
     "Keeps the paint sharp and pristine, so the car presents better and holds its value longer.",
     [("modely", 1), ("model3", 1), ("prado", 1), ("modely", 3), ("shark6", 9), ("prado", 5)]),
]
