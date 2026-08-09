"""Opens a browser window. User logs into Facebook themselves.
Saves the resulting session so the scraper can reuse it. No access to
any existing Chrome profile or credential store."""
import os, time
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\dlint\AppData\Local\Temp\claude\C--Users-dlint\5463c4d4-b7a5-46f4-9e8c-afd04b361a66\scratchpad"
UDD = os.path.join(BASE, "fb_session")
STATE = os.path.join(BASE, "fb_state.json")
os.makedirs(UDD, exist_ok=True)

CHECK = """() => {
  const h = document.cookie || '';
  const loggedOut = !!document.querySelector('input[name="pass"]') ||
                    /(^|\\/)login/.test(location.pathname);
  return {url: location.href, loggedOut};
}"""

with sync_playwright() as p:
    try:
        ctx = p.chromium.launch_persistent_context(
            UDD, channel="chrome", headless=False,
            args=["--no-first-run", "--no-default-browser-check"],
            viewport={"width": 1400, "height": 950}, locale="en-US")
    except Exception:
        ctx = p.chromium.launch_persistent_context(
            UDD, headless=False, viewport={"width": 1400, "height": 950}, locale="en-US")

    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(4000)

    print(">>> A Chrome window has opened. Log into Facebook in it.")
    print(">>> Waiting up to 5 minutes; it continues automatically once you're in.\n", flush=True)

    ok = False
    for i in range(100):
        try:
            st = pg.evaluate(CHECK)
            cookies = {c["name"] for c in ctx.cookies("https://www.facebook.com")}
            if "c_user" in cookies and not st["loggedOut"]:
                ok = True
                break
            if i % 4 == 0:
                print(f"  [{i*3:3d}s] waiting for login...", flush=True)
        except Exception:
            pass
        time.sleep(3)

    if ok:
        ctx.storage_state(path=STATE)
        who = [c["value"] for c in ctx.cookies("https://www.facebook.com") if c["name"] == "c_user"]
        print(f"\nLOGGED IN (uid {who[0] if who else '?'}) -> session saved")
    else:
        print("\nTIMEOUT - no login detected.")
    ctx.close()
