"""
One-time Facebook login for fb_photo_grab.py.

Opens a browser window; you log in yourself. Nothing reads your Chrome profile
or credential store. The resulting session is saved and reused, so this is a
one-time step per Facebook account.

usage:
  python fb_login.py [--state <json>]

Run it again to switch to a different Facebook account, or point --state at a
separate file to keep several accounts side by side:
  python fb_login.py --state C:\\Users\\dlint\\.fb-scrape\\clientB.json
"""
import argparse, os, time
from playwright.sync_api import sync_playwright

DEFAULT_STATE = os.path.join(os.path.expanduser("~"), ".fb-scrape", "state.json")

ap = argparse.ArgumentParser()
ap.add_argument("--state", default=DEFAULT_STATE)
a = ap.parse_args()

state = os.path.abspath(a.state)
os.makedirs(os.path.dirname(state), exist_ok=True)
# a persistent browser dir per session file, so the login sticks
udd = os.path.splitext(state)[0] + "_profile"
os.makedirs(udd, exist_ok=True)

with sync_playwright() as p:
    try:
        ctx = p.chromium.launch_persistent_context(
            udd, channel="chrome", headless=False,
            args=["--no-first-run", "--no-default-browser-check"],
            viewport={"width": 1400, "height": 950}, locale="en-US")
    except Exception:
        ctx = p.chromium.launch_persistent_context(
            udd, headless=False, viewport={"width": 1400, "height": 950}, locale="en-US")

    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000)

    print(">>> Log into Facebook in the window that just opened.")
    print(">>> This continues automatically once you're in (5 min limit).\n", flush=True)

    ok = False
    for i in range(100):
        try:
            names = {c["name"] for c in ctx.cookies("https://www.facebook.com")}
            if "c_user" in names and not pg.query_selector('input[name="pass"]'):
                ok = True
                break
            if i % 4 == 0:
                print(f"  [{i*3:3d}s] waiting for login...", flush=True)
        except Exception:
            pass
        time.sleep(3)

    if ok:
        ctx.storage_state(path=state)
        uid = next((c["value"] for c in ctx.cookies("https://www.facebook.com")
                    if c["name"] == "c_user"), "?")
        print(f"\nLogged in (uid {uid}). Session saved -> {state}")
        print("You can close the window. Now run fb_photo_grab.py.")
    else:
        print("\nTimed out - no login detected. Nothing saved.")
    ctx.close()
