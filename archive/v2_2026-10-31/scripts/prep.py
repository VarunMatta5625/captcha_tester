"""Image and Apple Vision helpers for the v2 captchas (red letters on gray speckle noise).

Imported by the notebook (`sys.path` gets ../scripts) and by label_vision.py, so the CNN and Vision
always see the same cleaned image.
"""
import io, os, re, subprocess, tempfile, zipfile

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = os.path.join(ROOT, "tools", "ocr")   # Apple Vision, accurate mode (built from tools/ocr.swift)
IMAGES_ZIP = os.path.join(ROOT, "data", "captchas.zip")   # the 100,000 captchas as captchas/<id>.png (no loose copies)
ALPHABET = "2345689ABDEFGHJLMNQRTYabdefghijmnqrty"   # v1's classes; gold checking reports any others
LENGTH = 5
RED_MIN = 60   # letter pixel: red beats both green and blue by more than this (speckle is gray, r = g = b)


_zips = {}   # one open ZipFile per process (label_vision.py's workers each open their own)


def _zip():
    if IMAGES_ZIP not in _zips:
        _zips[IMAGES_ZIP] = zipfile.ZipFile(IMAGES_ZIP)
    return _zips[IMAGES_ZIP]


def captcha_ids():
    """Every captcha id in the zip, in numeric order."""
    return sorted((os.path.basename(n)[:-4] for n in _zip().namelist() if n.endswith(".png")), key=int)


def open_captcha(i):
    """Captcha <i> as a PIL image, read straight from the zip."""
    return Image.open(io.BytesIO(_zip().read(f"captchas/{i}.png")))


def ink(img):
    """Captcha (PIL image) -> uint8 HxW, letters 0 (black) and everything else 255 (white)."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.where((r - g > RED_MIN) & (r - b > RED_MIN), 0, 255).astype(np.uint8)


def for_vision(img):
    """ink() image -> what Vision reads best: 2x upscale, fatter strokes (fills speckle holes), soft edges."""
    im = Image.fromarray(img)
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    return ImageOps.expand(im, border=40, fill=255)


def vision_reads(imgs):
    """ink() images -> raw Vision texts, one OCR call for all of them."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = [os.path.join(tmp, f"{k}.png") for k in range(len(imgs))]
        for img, p in zip(imgs, paths):
            for_vision(img).save(p)
        out = subprocess.run([OCR] + paths, capture_output=True, text=True, check=True).stdout
    got = dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)
    return [got.get(p, "").strip() for p in paths]


# Vision has no character whitelist and sometimes returns Cyrillic/Greek lookalikes; map them back.
HOMOGLYPHS = dict(zip(
    "АВЕЗКМНОРСТУХЅІЈЬаеіјорсухԁһԛѕзбΑΒΕΖΗΙΚΜΝΟΡΤΥΧαοιν",
    "ABE3KMHOPCTyXSIJbaeijopcyxdhqs36ABEZHIKMNOPTYXaoiv"))
# learned in v1 from typed reviews (pipeline.learn_map): Vision char outside the alphabet -> what it stood for.
# Applied after HOMOGLYPHS. If gold shows the new captchas use 0/O/1/7/S/I, drop those entries.
LEARNED = dict(zip("|7]:IwO¡)Sô10/дcт,Ìг", "iTjiiMDij56fDjqemrjr"))


def decode(raw):
    """Raw Vision text -> captcha text, or "" unless it is exactly LENGTH alphabet characters."""
    mapped = (HOMOGLYPHS.get(ch, ch) for ch in raw)
    text = re.sub(r"[^A-Za-z0-9]", "", "".join(LEARNED.get(ch, ch) for ch in mapped))
    return text if len(text) == LENGTH and all(ch in ALPHABET for ch in text) else ""
