"""Rebuilds the README screenshots and GIFs in docs/images/ from real runs against a local mock login page.

    python3 tools/readme_visuals/make_visuals.py [scene ...]       (from the project root)

Needs: playwright for Python with Chromium (`python3 -m playwright install chromium`), data/captchas.zip (git-ignored)
and ffmpeg is not needed. The browser has no network except the mock hosts; fake credentials only.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anno, scenes
from mock_site import ROOT

OUT = os.path.join(ROOT, "docs", "images")
os.makedirs(OUT, exist_ok=True)


def png(im, name):
    im.save(os.path.join(OUT, name), optimize=True)
    print(f"{name}: {os.path.getsize(os.path.join(OUT, name)) // 1024} KB")


def gif(frames, name, durations):
    print(f"{name}: {anno.save_gif(frames, os.path.join(OUT, name), durations) // 1024} KB, {len(frames)} frames")


def run(which):
    if "first_run" in which:
        before, after, _ = scenes.first_run()
        png(before, "first-run-1.png"); png(after, "first-run-2.png")
        gif([before, after, after], "first-run.gif", [1400, 2200, 1200])
    if "refresh" in which:
        fr = scenes.refresh_loop()
        for k, f in enumerate(fr, 1):
            png(f, f"refresh-{k}.png")
        gif(fr, "refresh.gif", [1500] * len(fr))


    if "popup" in which:
        fr = scenes.popup_setup()
        for k, f in enumerate(fr, 1):
            png(f, f"popup-{k}.png")
        gif(fr, "popup.gif", [2400] * len(fr))
    if "hero" in which:
        from PIL import Image, ImageDraw
        def load(n, title):
            im = Image.open(os.path.join(OUT, n)).convert("RGB")
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, anno.W, 54], fill=anno.TEAL)
            d.text((22, 12), title, font=anno.font(26, True), fill="white")
            d.text((anno.W - 22, 18), "Real extension, local mock login page, fake credentials", font=anno.font(18), fill=(207, 233, 229), anchor="ra")
            return im
        story = [("first-run-1.png", "Open the login page", 1500), ("first-run-2.png", "The captcha is read and typed for you", 2400),
                 ("refresh-2.png", "Refresh the captcha: it is read again", 1500), ("refresh-3.png", "Refresh the captcha: it is read again", 1500),
                 ("popup-5.png", "Optional: save your login once", 2600), ("signin-1.png", "Open the page: auto sign-in starts", 1500),
                 ("signin-2.png", "You are in, no clicks needed", 3200)]
        gif([load(n, t) for n, t, _ in story], "demo.gif", [d for _, _, d in story])
    if "install" in which:
        fr = scenes.install_steps()
        for k, f in enumerate(fr, 1):
            png(f, f"install-{k}.png")
        gif(fr, "install.gif", [2500] * len(fr))
    if "fill" in which:
        png(scenes.fill_only(), "fill-only.png")
    if "signin" in which:
        fr, _ = scenes.auto_signin()
        for k, f in enumerate(fr, 1):
            png(f, f"signin-{k}.png")
        gif(fr, "signin.gif", [2000, 3500])
    if "reject" in which:
        fr, _, saved = scenes.rejected_and_saved()
        for k, f in enumerate(fr, 1):
            png(f, f"reject-{k}.png")
        gif(fr, "reject.gif", [2600, 2600, 4200])
    if "rules" in which:
        im, cols = scenes.rules()
        png(im, "rules.png")
        for t, ok, log in cols:
            print(t, ok, log)


if __name__ == "__main__":
    run(sys.argv[1:] or ["first_run", "refresh", "popup"])
