"""
Bulk-download a Facebook Page's photos at the largest resolution Facebook serves.

Needs a logged-in session first (see fb_login.py) -- logged out, Facebook only
exposes ~9 photos per page.

usage:
  python fb_photo_grab.py --page <slug-or-url> --out <folder> [--state <json>]

examples:
  python fb_photo_grab.py --page Formulamobilecardetailing --out D:\\photos\\formula
  python fb_photo_grab.py --page https://www.facebook.com/SomeOtherPage --out D:\\photos\\other

Resumable: re-run the same command and it skips anything already downloaded.
Delete <out>\\_photo_ids.json to force a fresh re-scan of the photo grid.
"""
import argparse, json, os, re, struct, sys, time, urllib.parse, urllib.request
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
DEFAULT_STATE = os.path.join(os.path.expanduser("~"), ".fb-scrape", "state.json")

# Run extraction inside the browser and return only the small result -- never
# ship the whole (very large) scrolled document over the wire.
ANCHORS = """() => [...document.querySelectorAll('a')]
    .map(a => a.href).filter(h => /fbid=\\d+/.test(h))"""

BIG = """() => {
  const c = [...document.querySelectorAll('img')]
    .map(e => ({s: e.src, w: e.naturalWidth, h: e.naturalHeight}))
    .filter(o => o.s.includes('fbcdn') && o.w > 400)
    .sort((a,b) => b.w*b.h - a.w*a.h);
  return c[0] || null;
}"""


def jpeg_dims(b):
    if not b.startswith(b"\xff\xd8"):
        return None, None
    i = 2
    try:
        while i < len(b):
            if b[i] != 0xFF:
                i += 1; continue
            m = b[i + 1]
            if m in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
                h, w = struct.unpack(">HH", b[i + 5:i + 9]); return w, h
            if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                i += 2; continue
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def strip_ctp(url):
    """ctp= is the delivery downscale (e.g. s206x206). Dropping it returns the
    full-size render; stp/cstp carry the signature so they must stay."""
    u = urllib.parse.urlsplit(url)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True) if k != "ctp"]
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, urllib.parse.urlencode(q), ""))


def download(url, path):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": "https://www.facebook.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    with open(path, "wb") as f:
        f.write(b)
    return len(b), jpeg_dims(b)


def slug_of(page):
    """Accept a bare slug, a profile.php?id=, or any facebook.com URL."""
    page = page.strip().rstrip("/")
    if "facebook.com" in page:
        u = urllib.parse.urlsplit(page)
        if "profile.php" in u.path:
            pid = dict(urllib.parse.parse_qsl(u.query)).get("id", "")
            return f"profile.php?id={pid}"
        parts = [p for p in u.path.split("/") if p]
        # drop a trailing tab like /photos_by
        if parts and parts[-1] in ("photos", "photos_by", "photos_of", "posts"):
            parts.pop()
        return parts[-1] if parts else page
    return page


def harvest(pg, url, found, max_passes=600):
    """Scroll the grid, collecting {fbid: viewer_url} until it stops yielding."""
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"   ! {url} -> {repr(e)[:80]}"); return
    pg.wait_for_timeout(5000)
    before, stagnant = len(found), 0
    for i in range(max_passes):
        n0 = len(found)
        try:
            for h in pg.evaluate(ANCHORS):
                m = re.search(r"fbid=(\d+)", h)
                if m:
                    found.setdefault(m.group(1), h)
            pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        except Exception as e:
            print(f"   ! scroll: {repr(e)[:70]}"); break
        pg.wait_for_timeout(1800)
        if len(found) == n0:
            stagnant += 1
            if stagnant >= 10:
                break
        else:
            stagnant = 0
            if i % 10 == 0:
                print(f"      ...{len(found)}", flush=True)
    print(f"   {url.rstrip('/').split('/')[-1]:12s} -> +{len(found)-before} (total {len(found)})",
          flush=True)


def main():
    ap = argparse.ArgumentParser(description="Download all photos from a Facebook Page.")
    ap.add_argument("--page", required=True, help="page slug or facebook.com URL")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--state", default=DEFAULT_STATE, help=f"session json (default {DEFAULT_STATE})")
    ap.add_argument("--rescan", action="store_true", help="re-scan the grid, ignoring the cached id list")
    a = ap.parse_args()

    slug = slug_of(a.page)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    ids_file = os.path.join(out, "_photo_ids.json")
    mpath = os.path.join(out, "manifest.json")

    if not os.path.exists(a.state):
        sys.exit(f"No session at {a.state}\nRun:  python fb_login.py\n"
                 "(logged out, Facebook only exposes ~9 photos)")

    print(f"page : {slug}\nout  : {out}\n")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=[
            "--disable-dev-shm-usage", "--disable-extensions",
            "--disable-background-networking", "--renderer-process-limit=2"])
        ctx = b.new_context(user_agent=UA, locale="en-US",
                            viewport={"width": 1600, "height": 1000},
                            storage_state=a.state)
        pg = ctx.new_page()
        pg.set_default_timeout(45000)

        # ---- harvest (checkpointed; the expensive part to lose) ----
        found = {}
        if os.path.exists(ids_file) and not a.rescan:
            found = json.load(open(ids_file))
            print(f"resuming with {len(found)} known photo ids "
                  f"(--rescan to re-scan the grid)\n")
        else:
            print("HARVEST")
            for tab in ("photos_by", "photos_of", ""):
                harvest(pg, f"https://www.facebook.com/{slug}/{tab}", found)
                json.dump(found, open(ids_file, "w"), indent=0)

        ids = sorted(found)
        pg.close()                      # drop the huge scrolled DOM
        pg = ctx.new_page()
        pg.set_default_timeout(45000)
        print(f"\n{len(ids)} photos\n\nDOWNLOAD", flush=True)

        # ---- download (resumable) ----
        manifest = {}
        if os.path.exists(mpath):
            for r in json.load(open(mpath, encoding="utf-8")).get("photos", []):
                manifest[r["fbid"]] = r

        ok = skip = fail = 0
        for i, fid in enumerate(ids, 1):
            name = f"{i:03d}_{fid}.jpg"
            if fid in manifest and os.path.exists(os.path.join(out, manifest[fid]["file"])):
                skip += 1; continue
            url = found.get(fid) or f"https://www.facebook.com/photo/?fbid={fid}"
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(3000)
                big = pg.evaluate(BIG) or (pg.wait_for_timeout(3000), pg.evaluate(BIG))[1]
                if not big:
                    print(f"  {i:3d}/{len(ids)} {fid}  no image"); fail += 1; continue
                sz, (w, h) = download(strip_ctp(big["s"]), os.path.join(out, name))
                if w and big["w"] and w < big["w"]:          # keep the larger render
                    sz, (w, h) = download(big["s"], os.path.join(out, name))
                print(f"  {i:3d}/{len(ids)} {name}  {w}x{h}  {sz//1024}KB", flush=True)
                manifest[fid] = {"file": name, "fbid": fid, "width": w, "height": h,
                                 "bytes": sz, "source": url}
                ok += 1
            except Exception as ex:
                print(f"  {i:3d}/{len(ids)} {fid}  FAIL {repr(ex)[:80]}", flush=True); fail += 1
            if ok and ok % 20 == 0:
                json.dump({"page": slug, "count": len(manifest),
                           "photos": list(manifest.values())},
                          open(mpath, "w", encoding="utf-8"), indent=2)
            time.sleep(0.4)

        json.dump({"page": slug,
                   "source": f"https://www.facebook.com/{slug}/photos_by",
                   "count": len(manifest), "photos": list(manifest.values())},
                  open(mpath, "w", encoding="utf-8"), indent=2)
        print(f"\ndone: {ok} new, {skip} already had, {fail} failed -> {out}")
        b.close()


main()
