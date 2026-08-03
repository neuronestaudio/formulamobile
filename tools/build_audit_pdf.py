#!/usr/bin/env python3
"""
Render docs/AUDIT.md into a branded, client-facing PDF.

Two steps: markdown -> styled HTML (docs/audit.html), then Chrome headless
prints it to docs/Formula-Mobile-Site-Audit.pdf.

Design: dark branded cover, light printable body. Dark PDFs look poor on
paper and eat toner; the cover carries the brand, the body carries the
argument. Severity words in section headings become coloured chips.

    python tools/build_audit_pdf.py
"""

import os
import re
import subprocess
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "AUDIT.md")
HTML = os.path.join(ROOT, "docs", "audit.html")
PDF = os.path.join(ROOT, "docs", "Formula-Mobile-Site-Audit.pdf")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

BRAND = "#f5342d"

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm; }
@page :first { margin: 0; }

*, *::before, *::after { box-sizing: border-box; }

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

body {
  margin: 0;
  font-family: "DM Sans", "Segoe UI", system-ui, sans-serif;
  font-size: 10.2pt;
  line-height: 1.62;
  color: #1c1d22;
  background: #fff;
}

/* ---------- cover ---------- */
.cover {
  position: relative;
  height: 297mm;
  width: 210mm;
  margin: 0;
  background: #0a0a0d;
  color: #fff;
  padding: 30mm 20mm;
  display: flex;
  flex-direction: column;
  page-break-after: always;
  overflow: hidden;
}
.cover::before {
  content: "";
  position: absolute;
  inset: 0;
  opacity: .5;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='56' height='64' viewBox='0 0 56 64'%3E%3Cpath d='M28 0l24 16v32L28 64 4 48V16z' fill='none' stroke='%23ffffff' stroke-opacity='.06' stroke-width='1'/%3E%3C/svg%3E");
}
.cover::after {
  content: "";
  position: absolute;
  left: -30%; bottom: -55%;
  width: 130%; height: 90%;
  background: radial-gradient(closest-side, rgba(245,52,45,.30), transparent 72%);
}
.cover > * { position: relative; z-index: 1; }

.cover__logo { width: 62mm; margin-bottom: auto; }
.cover__eyebrow {
  font-size: 8pt; font-weight: 700; letter-spacing: .26em;
  text-transform: uppercase; color: %BRAND%; margin-bottom: 6mm;
}
.cover h1 {
  font-family: "Bebas Neue", Impact, sans-serif;
  font-size: 46pt; line-height: .93; letter-spacing: .01em;
  text-transform: uppercase; margin: 0 0 6mm; font-weight: 400;
  /* must be explicit: the generic `h1` rule below sets a near-black colour,
     and it wins over inheritance from .cover — leaving this line invisible. */
  color: #fff;
}
.cover h1 em { font-style: italic; color: %BRAND%; }
.cover__sub {
  font-size: 12pt; color: rgba(255,255,255,.72);
  max-width: 105mm; margin: 0 0 12mm;
}
.cover__meta {
  border-top: 1px solid rgba(255,255,255,.16);
  padding-top: 6mm; display: flex; gap: 14mm; flex-wrap: wrap;
  font-size: 9pt; color: rgba(255,255,255,.55);
}
.cover__meta b { display: block; color: #fff; font-weight: 600; margin-top: 1mm; }

/* ---------- body ---------- */
.body { padding-top: 2mm; }

h1, h2, h3 {
  font-family: "Bebas Neue", Impact, sans-serif;
  font-weight: 400; text-transform: uppercase;
  letter-spacing: .02em; line-height: 1;
  color: #0a0a0d;
}
h1 { font-size: 24pt; margin: 0 0 5mm; }
h2 {
  font-size: 19pt; margin: 11mm 0 4mm;
  padding-bottom: 2.5mm; border-bottom: 2px solid #0a0a0d;
  page-break-after: avoid;
}
h3 { font-size: 13pt; margin: 7mm 0 2.5mm; page-break-after: avoid; }
h2:first-child, h1:first-child { margin-top: 0; }

p { margin: 0 0 3.2mm; }
strong { font-weight: 700; color: #0a0a0d; }
a { color: #b3231d; text-decoration: none; }

ul, ol { margin: 0 0 3.6mm; padding-left: 5.5mm; }
li { margin-bottom: 1.4mm; }
li::marker { color: %BRAND%; }

hr { border: 0; border-top: 1px solid #dcdde1; margin: 8mm 0; }

code {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 8.6pt; background: #f1f2f4;
  border: 1px solid #e2e3e7; border-radius: 3px;
  padding: .4mm 1.2mm; color: #2b2c31;
}

blockquote {
  margin: 0 0 4mm; padding: 3mm 4mm;
  background: #fbf3f2; border-left: 3px solid %BRAND%;
  border-radius: 0 4px 4px 0;
}
blockquote p:last-child { margin-bottom: 0; }

/* ---------- tables ---------- */
table {
  width: 100%; border-collapse: collapse;
  margin: 0 0 5mm; font-size: 9.1pt;
  page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; page-break-after: auto; }
th {
  text-align: left; background: #0a0a0d; color: #fff;
  font-size: 7.6pt; font-weight: 700; letter-spacing: .12em;
  text-transform: uppercase; padding: 2.4mm 3mm;
}
td { padding: 2.6mm 3mm; border-bottom: 1px solid #e4e5e9; vertical-align: top; }
tbody tr:nth-child(even) td { background: #fafafb; }
/* first column of the finding tables is the id (1.1, 2.3 ...) */
td:first-child { white-space: nowrap; font-weight: 700; color: %BRAND%; }
table th:first-child { width: 13mm; }

/* ---------- severity chips ---------- */
.sev {
  display: inline-block; vertical-align: middle;
  font-family: "DM Sans", system-ui, sans-serif;
  font-size: 7.4pt; font-weight: 700; letter-spacing: .13em;
  text-transform: uppercase; color: #fff;
  padding: 1mm 2.4mm; border-radius: 3px; margin-left: 3mm;
  position: relative; top: -1.5mm;
}
.sev--critical { background: #c1121f; }
.sev--high     { background: #d9601a; }
.sev--medium   { background: #b08900; }

/* keep the "what's actually fine" block visually distinct */
#whats-actually-fine + p + ul { background: #f3f8f4; border-left: 3px solid #2e7d4f;
  padding: 4mm 4mm 4mm 9mm; border-radius: 0 4px 4px 0; }
#whats-actually-fine + p + ul li::marker { color: #2e7d4f; }
"""


def to_html():
    md = open(SRC, encoding="utf-8").read()

    # Drop the H1 + the meta line beneath it — the cover carries them.
    md = re.sub(r"^#\s+.*?\n", "", md, count=1)
    md = re.sub(r"^\*\*Audited:\*\*.*?\n", "", md, count=1, flags=re.M)

    body = markdown.markdown(
        md,
        extensions=["tables", "attr_list", "toc", "sane_lists"],
        output_format="html5",
    )

    # "## 1. Broken in production — Critical" -> heading + severity chip
    def chip(m):
        head, sev = m.group(1), m.group(2)
        return (f'<h2>{head}<span class="sev sev--{sev.lower()}">{sev}</span></h2>')

    body = re.sub(
        r"<h2[^>]*>(.*?)\s*&mdash;\s*(Critical|High|Medium)\s*</h2>",
        chip, body,
    )
    body = re.sub(
        r"<h2[^>]*>(.*?)\s*—\s*(Critical|High|Medium)\s*</h2>",
        chip, body,
    )

    logo = "/assets/images/logo.png"
    logo_fs = os.path.join(ROOT, "www", "assets", "images", "logo.png").replace("\\", "/")

    html = f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<title>Formula Mobile Car Detailing — Site Audit</title>
<style>
@font-face {{ font-family:'Bebas Neue'; src:url('file:///{os.path.join(ROOT,"www","assets","fonts","bebas-neue-400.woff2").replace(chr(92),"/")}') format('woff2'); font-weight:400; }}
@font-face {{ font-family:'DM Sans'; src:url('file:///{os.path.join(ROOT,"www","assets","fonts","dm-sans-latin.woff2").replace(chr(92),"/")}') format('woff2'); font-weight:100 1000; }}
{CSS.replace("%BRAND%", BRAND)}
</style>
</head>
<body>

<section class="cover">
  <img class="cover__logo" src="file:///{logo_fs}" alt="Formula Mobile Car Detailing">
  <div class="cover__eyebrow">Website audit</div>
  <h1>Where the site<br>is <em>losing you<br>work</em></h1>
  <p class="cover__sub">A front-end, back-end, SEO and conversion review of
     formulamobilecardetailing.com.au — every finding verified against the live server.</p>
  <div class="cover__meta">
    <div>Prepared for<b>Formula Mobile Car Detailing</b></div>
    <div>Audited<b>2 August 2026</b></div>
    <div>Site<b>formulamobilecardetailing.com.au</b></div>
  </div>
</section>

<div class="body">
{body}
</div>

</body>
</html>
"""
    with open(HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return HTML


def to_pdf(html_path):
    chrome = next((c for c in CHROME_CANDIDATES if os.path.exists(c)), None)
    if not chrome:
        sys.exit("No Chrome/Edge found for PDF rendering.")

    url = "file:///" + html_path.replace("\\", "/")
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF}",
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)
    return PDF


if __name__ == "__main__":
    h = to_html()
    print(f"html -> {h}")
    p = to_pdf(h)
    print(f"pdf  -> {p}  ({os.path.getsize(p) // 1024} KB)")
