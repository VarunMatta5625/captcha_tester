"""Drawing helpers for the README visuals: canvas, titles, red boxes, numbered steps, arrows, console panel, GIFs."""
import io, os
from PIL import Image, ImageDraw, ImageFont

RED = (229, 37, 27)
TEAL = (0, 116, 103)
INK = (17, 24, 39)
PAPER = (246, 248, 247)
W, H = 1280, 640


def font(size, bold=False, mono=False):
    if mono:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size, index=1 if bold else 0)
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=1 if bold else 0)


def canvas(title, subtitle=""):
    """Landscape 1280x640 frame with a teal title strip."""
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 54], fill=TEAL)
    d.text((22, 12), title, font=font(26, True), fill="white")
    if subtitle:
        d.text((W - 22, 18), subtitle, font=font(18), fill=(207, 233, 229), anchor="ra")
    return im


def paste_shot(im, shot_bytes_or_img, xy, border=True):
    shot = Image.open(io.BytesIO(shot_bytes_or_img)).convert("RGB") if isinstance(shot_bytes_or_img, bytes) else shot_bytes_or_img
    im.paste(shot, xy)
    if border:
        ImageDraw.Draw(im).rectangle([xy[0] - 1, xy[1] - 1, xy[0] + shot.width, xy[1] + shot.height], outline=(190, 200, 198), width=2)
    return xy[0], xy[1], shot.width, shot.height


def red_box(im, rect, width=4, pad=6):
    x0, y0, x1, y1 = rect
    ImageDraw.Draw(im).rounded_rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad], radius=8, outline=RED, width=width)


def badge(im, xy, n, r=17):
    d = ImageDraw.Draw(im)
    x, y = xy
    d.ellipse([x - r, y - r, x + r, y + r], fill=RED, outline="white", width=3)
    d.text((x, y), str(n), font=font(21, True), fill="white", anchor="mm")


def arrow(im, p0, p1, width=4, color=RED):
    import math
    d = ImageDraw.Draw(im)
    d.line([p0, p1], fill=color, width=width)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-0.45, 0.45):
        d.line([p1, (p1[0] - 18 * math.cos(a + s), p1[1] - 18 * math.sin(a + s))], fill=color, width=width)


def note(im, xy, text, w=420, size=19, fill=(255, 255, 255), outline=RED, color=INK, n=None):
    """Rounded callout card with wrapped text (and an optional red number badge on its corner)."""
    d = ImageDraw.Draw(im)
    f = font(size)
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            t = (cur + " " + word).strip()
            if d.textlength(t, font=f) > w - 24:
                lines.append(cur); cur = word
            else:
                cur = t
        lines.append(cur)
    h = len(lines) * (size + 5) + 18
    d.rounded_rectangle([xy[0], xy[1], xy[0] + w, xy[1] + h], radius=10, fill=fill, outline=outline, width=3)
    for k, ln in enumerate(lines):
        d.text((xy[0] + 12, xy[1] + 9 + k * (size + 5)), ln, font=f, fill=color)
    if n is not None:
        badge(im, (xy[0], xy[1]), n)
    return h


def console_panel(im, xy, size, lines, title="Console (real log lines from this run)"):
    """Dark DevTools-like panel. lines = list of strings; long ones wrap; the [CAPTCHA] prefix is tinted."""
    x, y = xy
    w, h = size
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=(30, 33, 38))
    d.text((x + 14, y + 8), title, font=font(15, True), fill=(160, 170, 180))
    f = font(15, mono=True)
    cy = y + 36
    for ln in (l for l in lines if "elements not found" not in l):   # the redirect stub page has no captcha: noise
        wrapped, cur = [], ""
        for ch in ln:
            if d.textlength(cur + ch, font=f) > w - 28:
                wrapped.append(cur); cur = "  " + ch
            else:
                cur += ch
        wrapped.append(cur)
        for k, part in enumerate(wrapped):
            if cy > y + h - 20:
                return
            col = (126, 231, 135) if "Pasted" in ln else (255, 203, 107) if "warn" in ln.lower() or "stopped" in ln or "paused" in ln or "below" in ln else (210, 215, 220)
            d.text((x + 14, cy), part, font=f, fill=col)
            cy += 20
        cy += 3


def save_gif(frames, path, durations, colors=128):
    """Frames (PIL RGB) -> optimised looping GIF, one adaptive palette for the whole animation."""
    frames = [f.convert("RGB") for f in frames]
    # one palette for every frame: build it from a montage of all of them
    montage = Image.new("RGB", (frames[0].width // 2, (frames[0].height // 2) * len(frames)))
    for k, f in enumerate(frames):
        montage.paste(f.resize((f.width // 2, f.height // 2)), (0, k * (f.height // 2)))
    pal = montage.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    out = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out[0].save(path, save_all=True, append_images=out[1:], duration=durations, loop=0, optimize=True, disposal=1)
    return os.path.getsize(path)
