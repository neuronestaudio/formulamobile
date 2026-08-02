#!/usr/bin/env python3
"""Mirror formulamobilecardetailing.com.au into a browsable static site."""
import os, re, sys, time, json
import urllib.parse as up
import urllib.request as ur

HOST = "www.formulamobilecardetailing.com.au"
BASE = f"https://{HOST}/"
OUT = sys.argv[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PAGES = ["", "index", "services", "gallery", "testimonials", "contact", "franchising"]

seen_pages, seen_assets, external, failed = {}, {}, set(), []


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = ur.Request(url, headers={
                "User-Agent": UA,
                "Accept": "*/*",
                "Referer": BASE,
            })
            with ur.urlopen(req, timeout=45) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except Exception as e:
            if i == tries - 1:
                failed.append((url, str(e)))
                return None, None
            time.sleep(1.5 * (i + 1))


def local_path(url):
    """Map an absolute same-host URL to a repo-relative path."""
    p = up.urlparse(url)
    path = up.unquote(p.path).lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    # strip query from asset filenames (e.g. font.woff?v=4.6.1)
    return path


def save(relpath, data):
    dest = os.path.join(OUT, relpath.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)


def is_same_host(url):
    h = up.urlparse(url).netloc.lower()
    return h in ("", HOST, "formulamobilecardetailing.com.au")


SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "#", "sms:")


def norm(url, base):
    url = url.strip().strip('"\'')
    if not url or url.lower().startswith(SKIP_SCHEMES):
        return None
    if url.startswith("//"):
        url = "https:" + url
    return up.urljoin(base, url)


# ---------- asset extraction ----------
ATTR_RE = re.compile(
    r'(?:src|href|data-src|data-thumb|data-original|poster|data-bg)\s*=\s*["\']([^"\']+)["\']', re.I)
SRCSET_RE = re.compile(r'srcset\s*=\s*["\']([^"\']+)["\']', re.I)
CSSURL_RE = re.compile(r'url\(\s*["\']?([^)"\']+)["\']?\s*\)', re.I)
INLINE_BG_RE = re.compile(r'background(?:-image)?\s*:\s*[^;"\']*url\(\s*["\']?([^)"\']+)', re.I)

ASSET_EXT = re.compile(
    r'\.(css|js|png|jpe?g|gif|svg|webp|ico|bmp|woff2?|ttf|eot|otf|mp4|webm|ogg|mp3|wav|pdf|json|map|avif)$', re.I)


def collect_urls(text, base, css=False):
    out = set()
    if css:
        for m in CSSURL_RE.findall(text):
            u = norm(m, base)
            if u:
                out.add(u)
        for m in re.findall(r'@import\s+["\']([^"\']+)["\']', text, re.I):
            u = norm(m, base)
            if u:
                out.add(u)
        return out
    for m in ATTR_RE.findall(text):
        u = norm(m, base)
        if u:
            out.add(u)
    for m in SRCSET_RE.findall(text):
        for part in m.split(","):
            cand = part.strip().split()
            if cand:
                u = norm(cand[0], base)
                if u:
                    out.add(u)
    for m in CSSURL_RE.findall(text):
        u = norm(m, base)
        if u:
            out.add(u)
    return out


def get_asset(url, depth=0):
    key = url.split("#")[0]
    if key in seen_assets or key in external:
        return
    if not is_same_host(key):
        external.add(key)
        return
    rel = local_path(key.split("?")[0])
    data, ctype = fetch(key)
    if data is None:
        return
    seen_assets[key] = rel
    save(rel, data)
    print(f"  asset {rel} ({len(data)}b)")
    if rel.lower().endswith(".css") and depth < 4:
        try:
            css_text = data.decode("utf-8", "replace")
        except Exception:
            return
        for u in collect_urls(css_text, key, css=True):
            get_asset(u, depth + 1)


# ---------- pages ----------
def page_rel(url):
    p = up.urlparse(url)
    path = p.path.strip("/")
    if not path:
        return "index.html"
    if "." in os.path.basename(path):
        return path
    return path + ".html"


queue = [up.urljoin(BASE, p) for p in PAGES]
visited = set()

while queue:
    url = queue.pop(0)
    clean = url.split("#")[0]
    if clean in visited or not is_same_host(clean):
        continue
    visited.add(clean)
    data, ctype = fetch(clean)
    if data is None:
        continue
    if "html" not in (ctype or "").lower():
        get_asset(clean)
        continue
    rel = page_rel(clean)
    seen_pages[clean] = rel
    save(rel, data)
    print(f"PAGE {rel} ({len(data)}b)  <- {clean}")
    html = data.decode("utf-8", "replace")
    for u in collect_urls(html, clean):
        cu = u.split("#")[0]
        if not is_same_host(cu):
            external.add(cu)
            continue
        path_only = up.urlparse(cu).path
        if ASSET_EXT.search(path_only):
            get_asset(cu)
        else:
            base_q = cu.split("?")[0]
            if base_q not in visited:
                queue.append(base_q)

meta = {
    "pages": seen_pages,
    "assets": sorted(seen_assets.values()),
    "external": sorted(external),
    "failed": failed,
}
with open(os.path.join(OUT, "_mirror-manifest.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

print("\n=== SUMMARY ===")
print(f"pages:    {len(seen_pages)}")
print(f"assets:   {len(seen_assets)}")
print(f"external: {len(external)}")
print(f"failed:   {len(failed)}")
for u, e in failed:
    print("  FAIL", u, e)
