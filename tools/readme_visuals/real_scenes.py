"""README scenes that open the actual login page in a throwaway Chromium profile (not your own browser). The page is
loaded and the extension fills it; nothing is ever submitted. Fake credentials go into the extension's settings only
for the "fill" picture, with auto sign-in off.

Only login.gitam.edu, cdn.gitam.edu and cdn.jsdelivr.net (the page's own assets) are reachable; everything else is
aborted. Run through make_visuals.py (scene names: real_first, real_refresh, real_fill).
"""
import io, json, os, tempfile
from contextlib import contextmanager

from PIL import Image
from playwright.sync_api import sync_playwright

import anno
from anno import canvas, paste_shot, red_box, badge, note, console_panel
from mock_site import ROOT

EXT = os.path.join(ROOT, "extension")
URL = "https://login.gitam.edu/Login.aspx"
ALLOWED = ("login.gitam.edu", "cdn.gitam.edu", "cdn.jsdelivr.net")
CARD = (858, 58, 1276, 656)     # the login card inside a 1280x720 viewport
K = 0.88                        # scale of the card crop in the frame
XY = (30, 76)


def _route(route):
    host = route.request.url.split("/")[2]
    if route.request.method != "GET" or host not in ALLOWED:
        return route.abort()
    return route.continue_()


@contextmanager
def real(with_extension=True):
    prof = tempfile.mkdtemp(prefix="cp_real_")
    args = ["--headless=new"]
    if with_extension:
        args += [f"--disable-extensions-except={EXT}", f"--load-extension={EXT}"]
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(prof, channel="chromium", headless=True, args=args,
                                                   viewport={"width": 1280, "height": 720})
        ctx.route("**/*", _route)   # GET only, allow-listed hosts only: a login can never be sent from here
        ext_id = None
        if with_extension:
            if not ctx.service_workers:
                ctx.wait_for_event("serviceworker", timeout=15000)
            ext_id = ctx.service_workers[0].url.split("/")[2]
        try:
            yield ctx, ext_id
        finally:
            ctx.close()


def open_page(ctx):
    pg = ctx.new_page()
    log = []
    pg.on("console", lambda m: log.append(m.text) if m.text.startswith("[CAPTCHA]") else None)
    pg.goto(URL, wait_until="load")
    return pg, log


def card(pg):
    im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB").crop(CARD)
    return im.resize((int(im.width * K), int(im.height * K)), Image.LANCZOS)


def rect(pg, sel):
    b = pg.locator(sel).bounding_box()
    return (XY[0] + (b["x"] - CARD[0]) * K, XY[1] + (b["y"] - CARD[1]) * K,
            XY[0] + (b["x"] + b["width"] - CARD[0]) * K, XY[1] + (b["y"] + b["height"] - CARD[1]) * K)


def frame(title, pg, boxes=(), notes=(), console=None, sub="Illustration"):
    im = canvas(title, sub)
    paste_shot(im, card(pg), XY)
    for sel, n in boxes:
        r = rect(pg, sel)
        red_box(im, r, width=3, pad=4)
        badge(im, (r[0] - 16, (r[1] + r[3]) / 2), n)
    x0, y = 450, 76
    for n, text in notes:
        y += note(im, (x0, y), text, w=800, n=n) + 16
    if console is not None:
        console_panel(im, (x0, y + 4), (800, 640 - y - 24), console)
    return im


def wait_filled(pg):
    pg.wait_for_function("document.getElementById('txtCaptchaInput').value.length === 5", timeout=15000)
    pg.wait_for_timeout(300)


def first_run():
    with real(with_extension=False) as (ctx, _):
        pg, _ = open_page(ctx)
        pg.wait_for_timeout(500)
        before = frame("1. Without the extension: the captcha box is empty", pg, boxes=[("#txtCaptchaInput", 1)],
                       notes=[(1, "The login page with no extension installed. You would type the five characters yourself.")],
                       console=[])
    with real() as (ctx, _):
        pg, log = open_page(ctx)
        wait_filled(pg)
        after = frame("2. With the extension: the box fills itself", pg,
                      boxes=[("#imgCaptcha", 1), ("#txtCaptchaInput", 2)],
                      notes=[(1, "The captcha image the site shows."),
                             (2, "Read by the model inside the extension and typed in. Nothing leaves your computer.")],
                      console=[l for l in log if "Pasted" in l])
    return before, after


def refresh(n=4):
    frames = []
    with real() as (ctx, _):
        pg, log = open_page(ctx)
        for k in range(n):
            wait_filled(pg)
            frames.append(frame(f"Every refresh is read too ({k + 1} of {n})", pg,
                                boxes=[("#imgCaptcha", 1), ("#txtCaptchaInput", 2)],
                                notes=[(1, "Click the captcha image to get a new one."), (2, "Filled again within a fraction of a second.")],
                                console=[l for l in log if "Pasted" in l][-6:]))
            if k < n - 1:
                pg.fill("#txtCaptchaInput", "")
                pg.click("#imgCaptcha")
                pg.wait_for_timeout(400)
    return frames


def fill_only():
    """Fake credentials saved in the throwaway profile, auto sign-in OFF: the form is filled, nothing is sent."""
    with real() as (ctx, ext):
        s = ctx.new_page()
        s.goto(f"chrome-extension://{ext}/options.html")
        s.evaluate("v => chrome.storage.local.set(v)", {"username": "demo1234", "password": "demo-password", "autofill": True,
                   "autoLogin": False, "signInAfterLogout": False, "minConfidence": 0.5})
        s.close()
        pg, log = open_page(ctx)
        wait_filled(pg)
        return frame("Credentials and captcha filled, you press LOGIN", pg,
                     boxes=[("#txtusername", 1), ("#password", 2), ("#txtCaptchaInput", 3), ("#Submit", 4)],
                     notes=[(1, "User ID filled (a fake one here)."), (2, "Password filled (it is shown as dots)."), (3, "Captcha read and typed."),
                            (4, "With only \"Auto populate credentials only\" ticked, this last click is yours. With auto sign-in on, the extension clicks it for you.")],
                     console=list(log))
