"""Starts Chromium with the shipped extension in a throwaway profile; only the mock hosts are reachable."""
import json, os, tempfile
from contextlib import contextmanager
from playwright.sync_api import sync_playwright

from mock_site import ROOT

EXT = os.path.join(ROOT, "extension")


@contextmanager
def session(mock, viewport=(760, 520), scale=1):
    """Yields (ctx, ext_id, downloads_dir). Profile and download folder are fresh temp folders."""
    prof = tempfile.mkdtemp(prefix="cp_profile_")
    dl = tempfile.mkdtemp(prefix="cp_downloads_")
    os.makedirs(os.path.join(prof, "Default"), exist_ok=True)
    json.dump({"download": {"default_directory": dl, "prompt_for_download": False},
               "savefile": {"default_directory": dl}}, open(os.path.join(prof, "Default", "Preferences"), "w"))
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            prof, channel="chromium", headless=True, viewport={"width": viewport[0], "height": viewport[1]},
            device_scale_factor=scale, accept_downloads=True,
            args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--headless=new",
                  "--host-resolver-rules=MAP * ~NOTFOUND"])   # belt and braces: no hostname resolves at all)
        ctx.route("**/*", mock.handle)   # everything not mocked is aborted: no real network
        if not ctx.service_workers:
            ctx.wait_for_event("serviceworker", timeout=15000)
        ext_id = ctx.service_workers[0].url.split("/")[2]
        # keep downloads (the saved captchas) in the throwaway folder instead of Playwright's own temp dir
        cdp = ctx.new_cdp_session(ctx.service_workers[0]) if False else None
        page0 = ctx.pages[0] if ctx.pages else ctx.new_page()
        cdp = ctx.new_cdp_session(page0)
        cdp.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": dl})
        try:
            yield ctx, ext_id, dl
        finally:
            ctx.close()


def set_settings(ctx, ext_id, **settings):
    """Write extension settings the way the options page does (chrome.storage.local), from an extension page."""
    pg = ctx.new_page()
    pg.goto(f"chrome-extension://{ext_id}/options.html")
    pg.evaluate("s => chrome.storage.local.set(s)", settings)
    pg.close()


def logger(pg):
    lines = []
    pg.on("console", lambda m: lines.append(m.text) if m.text.startswith("[CAPTCHA]") else None)
    return lines
