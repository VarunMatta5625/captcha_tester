"""Browser scenes for the README: each returns frames (PIL images) built from real runs of the shipped extension
against the local mock login page. Run through make_visuals.py."""
import io, re, time
from PIL import Image

import anno
from anno import canvas, paste_shot, red_box, badge, note, console_panel, arrow
from browser import session, set_settings, logger
from mock_site import Mock, DEMO_USER, DEMO_PASSWORD

SHOT_XY = (24, 74)
PANEL = (800, 74, 456, 520)
MOCK_NOTE = "Local mock login page, fake User ID and password"


def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")


def rect_of(pg, sel, pad=0):
    b = pg.locator(sel).bounding_box()
    return (SHOT_XY[0] + b["x"] - pad, SHOT_XY[1] + b["y"] - pad, SHOT_XY[0] + b["x"] + b["width"] + pad, SHOT_XY[1] + b["y"] + b["height"] + pad)


def frame(title, pg, boxes=(), notes=(), console=None, sub=MOCK_NOTE):
    """One 1280x640 frame: page screenshot left, console or notes right; boxes = [(selector, number)]."""
    im = canvas(title, sub)
    paste_shot(im, shot(pg), SHOT_XY)
    for sel, n in boxes:
        r = rect_of(pg, sel)
        red_box(im, r)
        badge(im, (r[0] - 6, r[1] - 6), n)
    y = PANEL[1]
    for n, text in notes:
        y += note(im, (PANEL[0] + 14, y), text, w=PANEL[2] - 14, n=n) + 18
    if console is not None:
        top = max(y, PANEL[1])
        console_panel(im, (PANEL[0], top), (PANEL[2], PANEL[1] + PANEL[3] - top), console)
    return im


def first_run():
    """Open the login page: captcha still loading, then the box fills itself."""
    mock = Mock(delay=0.9)
    with session(mock) as (ctx, ext, dl):
        set_settings(ctx, ext, autofill=False, autoLogin=False)   # first-run defaults of a fresh install differ; keep it to the paste
        pg = ctx.new_page()
        log = logger(pg)
        pg.goto("https://login.gitam.edu/Login.aspx", wait_until="commit")
        pg.wait_for_selector("#txtCaptchaInput")
        before = frame("1. Open the login page", pg, boxes=[("#txtCaptchaInput", 1)],
                       notes=[(1, "The captcha box starts empty while the image loads.")], console=[])
        pg.wait_for_function("document.getElementById('txtCaptchaInput').value.length === 5", timeout=10000)
        pg.wait_for_timeout(250)
        after = frame("2. The box fills itself", pg, boxes=[("#imgCaptcha", 1), ("#txtCaptchaInput", 2)],
                      notes=[(1, "The captcha image the site shows."), (2, "Read by the model inside the extension and typed in. Nothing leaves your computer.")],
                      console=[l for l in log if "Pasted" in l])
        return before, after, log


def refresh_loop(n=4):
    """Click Refresh several times; every new captcha is read."""
    mock = Mock()
    frames, logs = [], []
    with session(mock) as (ctx, ext, dl):
        set_settings(ctx, ext, autofill=False, autoLogin=False)
        pg = ctx.new_page()
        log = logger(pg)
        pg.goto("https://login.gitam.edu/Login.aspx")
        for k in range(n):
            pg.wait_for_function("document.getElementById('txtCaptchaInput').value.length === 5")
            pg.wait_for_timeout(200)
            frames.append(frame(f"Every refresh is read too ({k + 1} of {n})", pg,
                                boxes=[("#imgCaptcha", 1), ("#txtCaptchaInput", 2), ("#refresh", 3)],
                                notes=[(1, "New captcha."), (2, "Filled again within a fraction of a second."), (3, "Press Refresh as often as you like.")],
                                console=[l for l in log if "Pasted" in l][-6:]))
            if k < n - 1:
                pg.fill("#txtCaptchaInput", "")
                pg.click("#refresh")
                pg.wait_for_function("document.getElementById('txtCaptchaInput').value.length === 5 || true")
                pg.wait_for_timeout(100)
        return frames


def popup_setup():
    """The toolbar popup, shown as a page: type the fake credentials, tick the boxes, Save."""
    mock = Mock()
    frames = []
    with session(mock, viewport=(300, 700), scale=2) as (ctx, ext, dl):
        pg = ctx.new_page()
        pg.goto(f"chrome-extension://{ext}/popup.html")
        pg.wait_for_timeout(300)
        pg.set_viewport_size({"width": 300, "height": pg.evaluate("document.documentElement.scrollHeight")})

        def snap(title, boxes, notes):
            im = canvas(title, "Toolbar popup of the extension, fake credentials")
            s = Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")
            k = 1.0
            maxh = 640 - 74 - 16
            if s.height / 2 * 1.0 > maxh:
                k = maxh / (s.height / 2)
            s = s.resize((int(s.width / 2 * 1.0 * k * 1.0), int(s.height / 2 * k)), Image.LANCZOS) if k < 1 else s.resize((s.width // 2, s.height // 2), Image.LANCZOS)
            x0, y0 = 60, 74
            paste_shot(im, s, (x0, y0))
            for sel, n in boxes:
                b = pg.locator(sel).bounding_box()
                r = (x0 + b["x"] * k - 2, y0 + b["y"] * k - 2, x0 + (b["x"] + b["width"]) * k + 2, y0 + (b["y"] + b["height"]) * k + 2)
                red_box(im, r, width=3, pad=3)
                badge(im, (r[0] - 20, (r[1] + r[3]) / 2), n)
            y = 90
            for n, text in notes:
                y += note(im, (470, y), text, w=770, n=n) + 18
            return im

        frames.append(snap("1. Click the toolbar icon", [("#username", 1)], [(1, "The popup opens with empty fields. Nothing is saved yet, so only the captcha is filled.")]))
        pg.fill("#username", DEMO_USER); pg.fill("#password", DEMO_PASSWORD)
        frames.append(snap("2. Type your User ID and password", [("#username", 1), ("#password", 2)],
                           [(1, "User ID: 1 to 16 letters or digits (what the login page accepts)."), (2, "Password: 1 to 20 characters. Stored only in this browser, never synced.")]))
        frames.append(snap("3. Pick how far it should go", [("#autofill", 1), ("#autoLogin", 2), ("#signInAfterLogout", 3)],
                           [(1, "Auto populate credentials only: fills everything, you press LOGIN."),
                            (2, "Auto sign-in when the site is opened: also presses LOGIN. Ticking it ticks the box above."),
                            (3, "Also sign in after logging out: only available while auto sign-in is on.")]))
        pg.uncheck("#autofill")   # unticking the first box takes auto sign-in with it, and greys out the sub-box
        frames.append(snap("The boxes are linked", [("#autofill", 1), ("#autoLogin", 2), ("#signInAfterLogout", 3)],
                           [(1, "Untick credential fill ..."), (2, "... and auto sign-in unticks itself (it needs the credentials)."),
                            (3, "The sub-box is greyed out until auto sign-in is on again.")]))
        pg.check("#autoLogin")
        pg.fill("#minConfidence", "0.5")
        pg.click("#save"); pg.wait_for_timeout(400)
        frames.append(snap("4. Save", [("#minConfidence", 1), ("#save", 2), ("#status", 3)],
                           [(1, "Minimum confidence to press LOGIN (default 0.5). Below it the captcha is still filled and you press LOGIN."),
                            (2, "Save keeps everything in chrome.storage.local on this machine."),
                            (3, "The status line says what will happen next time.")]))
    return frames


def _creds(ctx, ext, **extra):
    set_settings(ctx, ext, username=DEMO_USER, password=DEMO_PASSWORD, autofill=True, autoLogin=True,
                 signInAfterLogout=False, minConfidence=0.5, **extra)


def auto_signin():
    """Auto sign-in end to end: open, fill, press LOGIN, signed in."""
    mock = Mock(delay=0.8)
    frames = []
    with session(mock) as (ctx, ext, dl):
        _creds(ctx, ext)
        pg = ctx.new_page()
        log = logger(pg)
        pg.goto("https://login.gitam.edu/Login.aspx", wait_until="commit")
        pg.wait_for_selector("#txtCaptchaInput")
        frames.append(frame("1. Type the address or open a bookmark", pg,
                            notes=[(1, "Nothing is filled yet. Auto sign-in starts as soon as the page loads.")], console=[]))
        pg.wait_for_url("https://gstudent.gitam.edu/**", timeout=15000)
        pg.wait_for_timeout(300)
        im = canvas("3. You are in", MOCK_NOTE)
        paste_shot(im, shot(pg), SHOT_XY)
        note(im, (PANEL[0] + 14, PANEL[1]), "The portal opened without you touching the login page.", w=PANEL[2] - 14, n=1)
        console_panel(im, (PANEL[0], PANEL[1] + 110), (PANEL[2], PANEL[3] - 110), list(log))
        frames.append(im)
        return frames, log


def rejected_and_saved():
    """The site rejects the read twice: one automatic retry, then it stops and the captchas are saved."""
    mock = Mock(reject_first=2)
    frames = []
    with session(mock) as (ctx, ext, dl):
        _creds(ctx, ext)
        pg = ctx.new_page()
        log = logger(pg)
        pg.goto("https://login.gitam.edu/Login.aspx")
        pg.wait_for_function("document.getElementById('lblmessage').textContent.includes('Invalid CAPTCHA')", timeout=15000)
        pg.wait_for_timeout(500)
        frames.append(frame("1. The site says \"Invalid CAPTCHA\"", pg, boxes=[("#lblmessage", 1)],
                            notes=[(1, "The model's read was rejected. The extension retries once with the new captcha.")],
                            console=[l for l in log if "Pasted" not in l]))
        pg.wait_for_function("document.querySelectorAll('#lblmessage').length && window.sessionStorage.getItem('captchaPasterAutoAttempts') === '2'", timeout=15000)
        pg.wait_for_timeout(1500)
        import os
        names = [m.group(1) for l in log for m in [re.search(r"saved (captcha_mistakes/\S+\.png)", l)] if m]
        files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
        frames.append(frame("2. Rejected twice: it stops", pg, boxes=[("#lblmessage", 1)],
                            notes=[(1, "Two LOGIN presses per tab is the limit. You take over from here.")],
                            console=[l for l in log if "Pasted" not in l]))
        im = canvas("3. Both rejected captchas were saved", "File names from the extension's log, images from the throwaway downloads folder")
        y = 84
        y += note(im, (40, y), "Each rejected read is saved as a PNG named with the time (UTC), what the model read and its confidence. The right answer is unknown: label these before training on them.", w=1200, size=22, n=1) + 24
        lines = ["~/Downloads/"] + [f"  {n}" for n in names] or ["(nothing saved)"]
        console_panel(im, (40, y), (1200, 40 + 24 * len(lines)), lines, title="Saved files (real names from this run)")
        x, y = 40, y + 70 + 24 * len(lines)
        import prep
        for i in mock.served[:2]:   # the two captchas the mock rejected, in the order they were sent
            pic = prep.open_captcha(i).convert("RGB")
            pic = pic.resize((pic.width * 3, pic.height * 3), Image.NEAREST)
            paste_shot(im, pic, (x, y))
            x += pic.width + 40
        saved = names
        frames.append(im)
        return frames, log, saved


def rules():
    """The 5.5 rules, four loads of the login page, real log lines."""
    cols = []
    mock = Mock()
    with session(mock) as (ctx, ext, dl):
        _creds(ctx, ext)
        pg = ctx.new_page(); L = logger(pg)
        # A: typed address / bookmark
        n0 = len(L)
        pg.goto("https://login.gitam.edu/Login.aspx")
        pg.wait_for_url("https://gstudent.gitam.edu/**", timeout=15000)
        cols.append(("Typed address, bookmark or link", True, L[n0:]))
        # C: logout from the portal, sub-box off
        n0 = len(L)
        pg.click("#logout"); pg.wait_for_url("https://login.gitam.edu/**"); pg.wait_for_timeout(2000)
        cols.append(("After a logout (sub-box off)", pg.url.startswith("https://gstudent"), L[n0:]))
        # D: logout, sub-box on
        set_settings(ctx, ext, signInAfterLogout=True)
        pg.goto("https://gstudent.gitam.edu/Home/Index")
        pg.click("#logout"); pg.wait_for_url("https://login.gitam.edu/**"); n0 = len(L) - 0
        pg.wait_for_url("https://gstudent.gitam.edu/**", timeout=15000)
        cols.append(("After a logout (sub-box on)", True, [l for l in L[n0 - 1:] if True]))
        # B: reload
        set_settings(ctx, ext, autoLogin=False, autofill=True, signInAfterLogout=False)
        pg2 = ctx.new_page(); L2 = logger(pg2)
        pg2.goto("https://login.gitam.edu/Login.aspx"); pg2.wait_for_timeout(1500)
        set_settings(ctx, ext, autoLogin=True, autofill=True)
        n0 = len(L2)
        pg2.reload(); pg2.wait_for_timeout(2000)
        cols.append(("Reload or back/forward", pg2.url.startswith("https://gstudent"), L2[n0:]))
    order = [0, 3, 1, 2]   # typed, reload, logout off, logout on
    im = canvas("When does auto sign-in press LOGIN?", "Real console output, local mock login page")
    x, w = 20, 300
    for idx in order:
        title, signed, log = cols[idx]
        keep = [l for l in log if "Pasted" not in l and "Credential" not in l and "elements not found" not in l]
        d = anno.ImageDraw.Draw(im)
        d.rounded_rectangle([x, 74, x + w, 144], radius=10, fill=(222, 245, 233) if signed else (255, 236, 214), outline=(0, 116, 103) if signed else (200, 120, 20), width=3)
        d.text((x + 14, 82), title, font=anno.font(17, True), fill=anno.INK)
        d.text((x + 14, 108), "Signs in" if signed else "Fills only, you press LOGIN", font=anno.font(17), fill=(0, 100, 80) if signed else (150, 80, 0))
        console_panel(im, (x, 156), (w, 460), keep, title="Console")
        x += w + 20
    return im, cols


def fill_only():
    """'Auto populate credentials only': everything is filled, you press LOGIN."""
    mock = Mock()
    with session(mock) as (ctx, ext, dl):
        set_settings(ctx, ext, username=DEMO_USER, password=DEMO_PASSWORD, autofill=True, autoLogin=False,
                     signInAfterLogout=False, minConfidence=0.5)
        pg = ctx.new_page()
        log = logger(pg)
        pg.goto("https://login.gitam.edu/Login.aspx")
        pg.wait_for_function("document.getElementById('txtCaptchaInput').value.length === 5")
        pg.wait_for_timeout(300)
        return frame("Credentials and captcha filled, you press LOGIN", pg,
                     boxes=[("#txtusername", 1), ("#password", 2), ("#txtCaptchaInput", 3), ("#Submit", 4)],
                     notes=[(1, "User ID filled."), (2, "Password filled (dots)."), (3, "Captcha read and typed."),
                            (4, "With only \"Auto populate credentials only\" ticked, this last click is yours.")],
                     console=list(log))


def install_steps():
    """chrome://extensions with the real extension (loaded here with a launch flag instead of the folder picker)."""
    mock = Mock()
    frames = []
    with session(mock) as (ctx, ext, dl):
        pg = ctx.new_page()
        pg.goto("chrome://extensions")
        pg.wait_for_timeout(1200)
        sub = "Real chrome://extensions page (throwaway browser profile)"
        frames.append(frame("1. Turn on Developer mode", pg, boxes=[("#devMode", 1)],
                            notes=[(1, "Open chrome://extensions (Edge: edge://extensions, Brave: brave://extensions). Switch on Developer mode, top right.")], sub=sub))
        pg.click("#devMode")
        pg.wait_for_timeout(800)
        frames.append(frame("2. Click \"Load unpacked\"", pg, boxes=[("#loadUnpacked", 1)],
                            notes=[(1, "A folder picker opens (an operating system window, so it is not in this screenshot). Choose the unzipped captcha-paster folder, the one that contains manifest.json.")], sub=sub))
        frames.append(frame("3. The extension is installed", pg, boxes=[("#dev-reload-button", 1)],
                            notes=[(1, "This card means it worked. After you update the files or the model, press this circular arrow to reload the extension.")], sub=sub))
    return frames
