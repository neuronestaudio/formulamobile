"""
Long-tail keyword landing pages, grouped into topic clusters.

Modelled on the Premier / Next Lvl sitemaps: a cluster per service line, each
page targeting one real search intent and cross-linking to its siblings.

Every page carries its own intro, three distinct points and its own FAQ answer.
None is a template with the keyword swapped — thin near-duplicates are an SEO
liability, not an asset, and Google treats them as such.

Sourcing: every technical claim traces to the client's own service copy in the
captured snapshot — the 4-stage exterior process, the coating specs (Graphene
Pro 10H N1 / Quartz 9H Pro / Quartz Ceramic / interior / glass), and the 3-6
stage correction processes. Nothing about price or turnaround appears anywhere,
because they publish neither.

Each entry is:
    (slug, h1, meta description, intro, [(point title, point body) x3],
     (faq question, faq answer))
"""

CLUSTERS = [
    # ----------------------------------------------------------------- ceramic
    ("Ceramic Coating Melbourne", "ceramic-coating", [
        ("ceramic-coating-melbourne", "Ceramic Coating Melbourne",
         "Ceramic coating across metropolitan Melbourne. Graphene Pro 10H and Quartz 9H Pro, applied at your place or in our studio.",
         "An automotive ceramic coating is an advanced industrial-grade liquid polymer sealer that chemically bonds to your vehicle's paint work. The semi-permanent layer creates a hydro barrier between the finish of your duco and the elements.",
         [("What it does",
           "Your vehicle stays cleaner for longer, washes and dries more easily, and holds a deep glossy shine. It resists scratches and abrasions, wash marks and swirls, and bird droppings."),
          ("What we apply",
           "Graphene Pro 10H N1 at up to 1000nm, Quartz 9H Pro at up to 800nm with grade 3 chemical resistance, and Quartz Ceramic Coating. Glass and interior surfaces have their own coatings."),
          ("What has to happen first",
           "A coating bonds to whatever surface it is laid on, so the paint is washed, clay barred and corrected before anything is applied.")],
         ("Where is the coating applied?",
          "In our studio. Correction and coating are conducted in our specialty studio, created for these applications \u2014 a coating needs controlled lighting to find the defects and a clean, stable environment to cure against.")),

        ("ceramic-coating-cost-melbourne", "Ceramic Coating Cost Melbourne",
         "What actually drives the cost of a ceramic coating in Melbourne, and why paint condition matters more than the coating itself.",
         "Coating price is not one number. It moves with the coating you choose, the size of the vehicle, and the biggest factor of all: how much correction the paint needs before anything goes on.",
         [("The coating itself",
           "Graphene Pro 10H N1 is our hardest and longest lasting. Quartz 9H Pro sits below it at up to five years, and Quartz Ceramic around three."),
          ("The correction underneath",
           "A coating locks in whatever the paint looks like when it goes on. Paint needing a 5 or 6 stage correction takes considerably longer to prepare than paint needing three."),
          ("The vehicle",
           "A ute or a seven-seat SUV carries far more panel area than a hatchback, and that tells at every stage of the process.")],
         ("Can you quote over the phone?",
          "We can talk you through a range, but paint condition decides the correction and the correction decides the job. Call 1300 132 750 and our operators will work through it with you.")),

        ("ceramic-coating-longevity-melbourne", "How Long Ceramic Coating Lasts",
         "How long each of our ceramic coatings lasts — Graphene Pro, Quartz 9H Pro, Quartz Ceramic and interior.",
         "Longevity depends on which coating goes on and how the car is looked after afterwards. These are our own figures, not industry averages.",
         [("Graphene Pro 10H N1",
           "10H hardness, up to 1000nm thick, and rated to stay for the life of the vehicle. The world's first N1 nano coating."),
          ("Quartz 9H Pro",
           "9H hardness, up to 800nm, grade 3 chemical resistance, up to five years. Its formula allows multiple layers to increase thickness."),
          ("Quartz Ceramic and interior",
           "Quartz Ceramic is 9H, up to 800nm, around three years. The interior coating protects both fabric and leather for up to twelve months.")],
         ("Does it need maintaining?",
          "Minimal maintenance, but not none. We will either walk you through the routine or put you on a scheduled maintenance program.")),

        ("ceramic-coating-maintenance-melbourne", "Ceramic Coating Maintenance",
         "How to keep a ceramic coating performing, and what still needs attention after it is on.",
         "A coating makes maintenance easier; it does not remove it. Contamination still lands on the car, it simply has far less to grip on to.",
         [("Washing",
           "The coating is hydrophobic, so water lifts dirt away as it runs off. Washing takes less time and carries far less risk of putting swirls back into the paint."),
          ("What still needs attention",
           "Bird droppings and tree sap are acidic. A coated panel resists them long enough to be washed off safely, but they should not be left to sit."),
          ("Scheduled care",
           "We can educate you on the appropriate maintenance procedures, or provide a scheduled maintenance program.")],
         ("Can I still use an automatic wash?",
          "We would not recommend it. Brush washes are what put the swirl marks and spider webbing into paint that correction later has to remove.")),

        ("ceramic-coating-near-me-melbourne", "Ceramic Coating Near Me",
         "Ceramic coating for Melbourne, applied in our own studio.",
         "Coating work is done at our studio, where the lighting and the environment are controlled — which is what a coating needs to cure properly.",
         [("A controlled environment",
           "A coating cures against dust, temperature and humidity. A studio controls all three; a driveway controls none of them."),
          ("Studio for correction",
           "Paint correction ahead of a coating is conducted in our specialty studio, created for these applications."),
          ("Over twenty years",
           "We have been correcting and coating vehicles in Melbourne for more than thirty years.")],
         ("Where are you based?",
          "Melbourne. Bookings come to our studio — call 1300 132 750 and our operators will confirm a time.")),

        ("ceramic-coating-new-car-melbourne", "Ceramic Coating a New Car",
         "Coating a new car in Melbourne, before daily driving starts leaving its mark.",
         "A new car is the most straightforward coating job there is, because there is little or no correction to do first. The paint is already close to its best.",
         [("Less correction needed",
           "On a new car the coating usually follows a wash and clay bar decontamination rather than a multi-stage machine correction."),
          ("Thinner clear coats",
           "Manufacturers now use thinner clear coats than they did twenty years ago. There is less material between the world and your colour coat."),
          ("New is not always flawless",
           "Transport and dealer prep can leave wash marks worth correcting before a coating locks them in.")],
         ("Should I coat it straight away?",
          "It is the ideal time. You are protecting paint at its best rather than restoring it later.")),

        ("ceramic-coating-wheels-glass-melbourne", "Wheel, Glass and Interior Coating",
         "Coatings for wheels, glass and interior surfaces — not just paint.",
         "Paint is not the only surface worth coating. Wheels take brake dust and heat, glass takes environmental build-up, and interiors take everything else.",
         [("Glass coatings",
           "The exterior of glass accumulates a build-up of environmental pollution that normal window cleaning will not remove. We have a process that lifts it off and leaves a smooth polished finish."),
          ("Interior coating",
           "A hybrid solvent base that works on both fabric and leather, protecting against stains, dirt, contaminants, water and oil for up to twelve months."),
          ("Applicable surfaces",
           "Our coatings are applicable to painted surfaces, metal surfaces and glass.")],
         ("Can you coat just the wheels?",
          "Talk to our operators about what you want covered. We can put together a package that suits the vehicle and the budget.")),

        ("graphene-coating-melbourne", "Graphene Coating Melbourne",
         "Graphene Pro 10H N1 — our hardest coating, rated to last the life of the vehicle.",
         "Graphene Pro 10H N1 mixes advanced nano-technology with the properties of graphene. It is the world's first N1 nano coating.",
         [("10H hardness",
           "The hardest coating we apply, giving the strongest resistance to scratches, abrasions and wash marks."),
          ("Up to 1000nm",
           "A genuinely thick layer of protection — more material between your paint and the world than a standard ceramic lays down."),
          ("Stays for life",
           "Where Quartz 9H Pro is measured in years, Graphene Pro is rated to last the life of the vehicle.")],
         ("Is graphene worth it over a standard ceramic?",
          "It depends how long you are keeping the car and what you want from it. Our operators will talk you through the difference honestly.")),

        ("ceramic-coating-vs-wax-melbourne", "Ceramic Coating vs Wax",
         "Why a ceramic coating is not simply a longer-lasting wax.",
         "A wax or sealant sits on top of the paint and washes away. A ceramic coating chemically bonds to the duco and becomes part of the surface.",
         [("Bonded, not applied",
           "An industrial-grade liquid polymer sealer chemically bonds to your paint work. It is a semi-permanent layer, not a topping."),
          ("Years, not weeks",
           "Our coatings run from around three years to the life of the vehicle. A traditional wax is measured in weeks."),
          ("Hardness",
           "Wax adds no meaningful hardness. A 9H or 10H coating resists the micro scratches that come from washing and daily driving.")],
         ("Do you still hand polish?",
          "Yes. Hand polishing with a quality liquid polish or wax is part of our detailing services where a coating is not what the customer is after.")),
    ]),

    # -------------------------------------------------------- paint correction
    ("Paint Correction Melbourne", "paint-correction", [
        ("paint-correction-melbourne", "Paint Correction Melbourne",
         "Paint correction in Melbourne — 3, 4, 5 and 6 stage processes in our specialty studio.",
         "Paint correction is a method applied to duco surfaces to eliminate most imperfections. It is conducted in our specialty studio, created for these applications.",
         [("What it removes",
           "Swirl marks caused by a poor cut and polish, environmental damage from being left exposed to the elements, and the marks, scuffs and scratches of day-to-day use."),
          ("Matched to the damage",
           "We run 3, 4, 5 and 6 stage processes. Which one your car needs depends on the severity and depth of the damage, the colour, and the type of duco the manufacturer applied."),
          ("Why it matters before coating",
           "A coating locks in whatever the paint looks like underneath it. Correction is the step that decides the result.")],
         ("How do I know how many stages I need?",
          "It is not something to guess at over the phone. Our operators inspect the paint and work out a course of action to suit the vehicle.")),

        ("swirl-mark-removal-melbourne", "Swirl Mark Removal Melbourne",
         "Removing swirl marks and spider webbing from Melbourne paint work.",
         "Swirl marks and spider webbing are fine scratches in the clear coat that scatter light. They are most visible on dark paint and in direct sun.",
         [("Where they come from",
           "Poor cut and polish work, automatic brush washes, and washing with the wrong technique or a dirty mitt."),
          ("How they come out",
           "Machine cutting removes the scratches and dullness, then machine glazing de-swirls the surface and puts a deep gloss back."),
          ("Keeping them out",
           "A ceramic coating adds hardness that resists the micro scratches daily washing puts back in.")],
         ("Can every swirl be removed?",
          "Most can. How far we go depends on how much clear coat there is to work with — which is why we inspect before committing to a process.")),

        ("scratch-removal-melbourne", "Car Scratch Removal Melbourne",
         "Scratch, scuff and mark removal from paint work across Melbourne.",
         "Marks, scuffs and scratches from general day-to-day use are one of the main things paint correction is for.",
         [("Depth decides the method",
           "The method we use is tailored to the severity and depth of the damage, the colour, and the type of duco the manufacturer applied to the vehicle."),
          ("Machine cut and glaze",
           "Machine cutting removes scratches, spider webbing and dullness. Machine glazing then de-swirls the surface and restores depth."),
          ("Honest assessment",
           "Some damage is through the clear coat and cannot be polished out. We will tell you that rather than charge you to find out.")],
         ("Will it match the rest of the panel?",
          "Correction works the existing paint rather than adding anything, so there is no colour match to get wrong.")),

        ("oxidised-paint-restoration-melbourne", "Oxidised and Dull Paint Restoration",
         "Bringing oxidised, dull and neglected Melbourne paint work back.",
         "We specialise in surface damage that may need our 4 stage process — whether brush marks, spider webbing, oxidised dull or just plain neglected paint work.",
         [("What oxidation is",
           "Environmental damage — a build-up of pollution, rain and sun damage caused by a vehicle being exposed to the elements and not garaged."),
          ("The four stage process",
           "Pressure wash, hand wash and rinse, clay bar to deep clean grime and foreign matter, machine cut to remove dullness, machine glaze to restore gloss, then hand polish to seal."),
          ("Most situations are fixable",
           "We have a process to fix most situations. Speak to our operators and we will work out a course of action to suit the vehicle.")],
         ("My paint has gone chalky. Is it too late?",
          "Often not. Bring it to our operators — oxidised and dull paint is exactly what the 4 stage process exists for.")),

        ("machine-polishing-melbourne", "Machine Polishing Melbourne",
         "Machine cutting and glazing, and where each fits in the process.",
         "Machine polishing is two distinct steps that do different jobs, and using one without the other is where a lot of poor results come from.",
         [("Machine cut",
           "Cuts the paint work to rid it of scratches, spider webbing and any dullness, bringing the gloss back."),
          ("Machine glaze",
           "De-swirls the surface and puts back a deep gloss — this is the step that removes the marks cutting itself can leave."),
          ("Then sealed",
           "Finally hand polished with a quality liquid polish, wax or both, to seal and protect the paint work from the everyday elements.")],
         ("Is a cut and polish the same as paint correction?",
          "A cut and polish is part of it. Full correction is a staged process matched to the depth of the damage, run in our specialty studio.")),

        ("cut-and-polish-melbourne", "Cut and Polish Melbourne",
         "Cut and polish for Melbourne vehicles, and when a full correction is the better call.",
         "A cut and polish improves gloss and removes light defects. A full paint correction goes considerably further, in stages matched to the damage.",
         [("What a cut and polish does",
           "Clay bar decontamination, machine work to lift dullness and light marks, then a hand polish to seal and protect."),
          ("When it is enough",
           "On paint in reasonable condition that has gone a little flat, a cut and polish will bring most of it back."),
          ("When it is not",
           "Deep swirl marks, spider webbing and heavier scratches need the staged correction process instead.")],
         ("Which one does my car need?",
          "Our operators will look at the paint and tell you honestly. There is no point paying for six stages if three will do it.")),
    ]),


    # ------------------------------------------------------------- detailing
]


def all_pages():
    """Flat list of (slug, h1) across every cluster."""
    out = []
    for _title, _key, pages in CLUSTERS:
        for p in pages:
            out.append((p[0], p[1]))
    return out
