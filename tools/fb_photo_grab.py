"""
Formula Mobile Car Detailing - Facebook photo sourcing.

Scrolls the page's photo grid with an authenticated session, checkpoints the
photo-id list to disk, then opens each photo's viewer page and downloads the
largest (uncropped) render available. Resumable: re-running skips files that
are already on disk.

usage: python fb_grab.py <storage_state.json>
"""
import json, os, re, struct, sys, time, urllib.parse, urllib.request
from playwright.sync_api import sync_playwright

PAGE = "Formulamobilecardetailing"
PAGE_ID = "100064761783855"
SET = f"pb.{PAGE_ID}.-2207520000"
OUT = r"C:\Users\dlint\formulamobile\facebook-photos"
SCRATCH = r"C:\Users\dlint\AppData\Local\Temp\claude\C--Users-dlint\5463c4d4-b7a5-46f4-9e8c-afd04b361a66\scratchpad"
IDS_FILE = os.path.join(SCRATCH, "photo_ids.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
STATE = sys.argv[1] if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) else None

ENTRIES = [
    f"https://www.facebook.com/{PAGE}/photos_by",
    f"https://www.facebook.com/{PAGE}/photos_of",
    f"https://www.facebook.com/{PAGE}/",
]

# Extract ids inside the browser and return only the small id array -- never
# ship the whole (very large) document over the wire.
ANCHOR_IDS = """() => [...document.querySelectorAll('a')]
    .map(a => (a.href.match(/fbid=(\\d+)/) || [])[1]).filter(Boolean)"""

PAYLOAD_IDS = """() => {
  const out = new Set();
  const re = /"(?:photo_id|fbid|subject_id)"\\s*:\\s*"?(\\d{12,})"?/g;
  let m; const h = document.documentElement.innerHTML;
  while ((m = re.exec(h))) out.add(m[1]);
  return [...out];
}"""

BIG = """() => {
  const c = [...document.querySelectorAll('img')]
    .map(e => ({s: e.src, w: e.naturalWidth, h: e.naturalHeight}))
    .filter(o => o.s.includes('fbcdn') && o.w > 400)
    .sort((a,b) => b.w*b.h - a.w*a.h);
  return c[0] || null;
}"""

META = """() => {
  const d = [...document.querySelectorAll('[aria-label]')]
    .map(e => e.getAttribute('aria-label'))
    .find(x => /^\\d{1,2} [A-Z][a-z]+ \\d{4}$/.test(x || ''));
  const og = document.querySelector('meta[property="og:description"]');
  return {date: d || null, caption: og ? og.content : null};
}"""


def jpeg_dims(b):
    try:
        i = 2
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


def harvest(pg, url, ids, max_passes=500):
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"   ! {url} -> {repr(e)[:80]}"); return
    pg.wait_for_timeout(5000)
    before, stagnant = len(ids), 0
    try:
        ids.update(pg.evaluate(PAYLOAD_IDS))
    except Exception:
        pass
    for i in range(max_passes):
        n0 = len(ids)
        try:
            ids.update(pg.evaluate(ANCHOR_IDS))
            pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        except Exception as e:
            print(f"   ! scroll {repr(e)[:60]}"); break
        pg.wait_for_timeout(1800)
        if len(ids) == n0:
            stagnant += 1
            if stagnant >= 10:
                break
        else:
            if len(ids) - before > 0 and i % 10 == 0:
                print(f"      ...{len(ids)} ids", flush=True)
            stagnant = 0
    try:
        ids.update(pg.evaluate(ANCHOR_IDS))
    except Exception:
        pass
    print(f"   {url.rstrip('/').split('/')[-1] or 'feed':12s} -> +{len(ids)-before:3d} (total {len(ids)})", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=[
            "--disable-dev-shm-usage", "--disable-extensions",
            "--disable-background-networking", "--renderer-process-limit=2",
            "--js-flags=--max-old-space-size=1024"])
        kw = dict(user_agent=UA, locale="en-US", viewport={"width": 1600, "height": 1000})
        if STATE:
            kw["storage_state"] = STATE
            print(f"session: {os.path.basename(STATE)}")
        ctx = b.new_context(**kw)
        pg = ctx.new_page()
        pg.set_default_timeout(45000)

        # ---- harvest (checkpointed) ----
        ids = set()
        if os.path.exists(IDS_FILE):
            ids = set(json.load(open(IDS_FILE)))
            print(f"resuming with {len(ids)} known ids")
        else:
            print("HARVEST")
            for e in ENTRIES:
                harvest(pg, e, ids)
                json.dump(sorted(ids), open(IDS_FILE, "w"), indent=0)
        ids = sorted(ids)
        # the scrolled grid leaves a huge DOM behind -- drop it before downloading
        pg.close()
        pg = ctx.new_page()
        pg.set_default_timeout(45000)
        print(f"\n{len(ids)} unique photo ids\n\nDOWNLOAD", flush=True)

        # ---- download (resumable) ----
        mpath = os.path.join(OUT, "manifest.json")
        manifest = {}
        if os.path.exists(mpath):
            for r in json.load(open(mpath, encoding="utf-8")).get("photos", []):
                manifest[r["fbid"]] = r

        ok = skip = fail = 0
        for i, fid in enumerate(ids, 1):
            name = f"{i:03d}_{fid}.jpg"
            dest = os.path.join(OUT, name)
            if fid in manifest and os.path.exists(os.path.join(OUT, manifest[fid]["file"])):
                skip += 1; continue
            url = f"https://www.facebook.com/photo.php?fbid={fid}&set={SET}&type=3"
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(3000)
                big = pg.evaluate(BIG)
                if not big:
                    pg.wait_for_timeout(3000)
                    big = pg.evaluate(BIG)
                if not big:
                    print(f"  {i:3d}/{len(ids)} {fid}  no image"); fail += 1; continue
                meta = pg.evaluate(META)
                sz, (w, h) = download(strip_ctp(big["s"]), dest)
                if w and big["w"] and w < big["w"]:      # keep the larger render
                    sz, (w, h) = download(big["s"], dest)
                print(f"  {i:3d}/{len(ids)} {name}  {w}x{h}  {sz//1024}KB", flush=True)
                manifest[fid] = {"file": name, "fbid": fid, "width": w, "height": h,
                                 "bytes": sz, "date": meta.get("date"),
                                 "caption": meta.get("caption"), "source": url}
                ok += 1
            except Exception as ex:
                print(f"  {i:3d}/{len(ids)} {fid}  FAIL {repr(ex)[:80]}", flush=True); fail += 1
            if ok % 20 == 0 and ok:
                json.dump({"page": PAGE, "count": len(manifest),
                           "photos": list(manifest.values())},
                          open(mpath, "w", encoding="utf-8"), indent=2)
            time.sleep(0.4)

        json.dump({"page": PAGE, "page_id": PAGE_ID,
                   "source": f"https://www.facebook.com/{PAGE}/photos_by",
                   "count": len(manifest), "photos": list(manifest.values())},
                  open(mpath, "w", encoding="utf-8"), indent=2)
        print(f"\ndone: {ok} new, {skip} already had, {fail} failed -> {OUT}")
        b.close()


main()
