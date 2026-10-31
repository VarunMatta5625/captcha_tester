"""Image and Apple Vision helpers for the red-letter captchas (since 2026-10-31: bold font on large gray blobs).

Imported by the notebook (`sys.path` gets ../scripts) and by label_vision.py, so the CNN and Vision
always see the same cleaned image.
"""
import io, os, re, subprocess, tempfile, zipfile

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = os.path.join(ROOT, "tools", "ocr")   # Apple Vision, accurate mode (built from tools/ocr.swift)
IMAGES_ZIP = os.path.join(ROOT, "data", "captchas.zip")   # the captchas as <id>.png, any folder inside (no loose copies)
ALPHABET = "2345689ABDEFGHJLMNQRTYabdefghijmnqrty"   # v1's classes; gold checking reports any others
LENGTH = 5
RED_MIN = 60   # letter pixel: red beats both green and blue by more than this (speckle is gray, r = g = b)
BLOB_MAX = 200   # blob pixel: not a letter and darker than this (mean of r, g, b); lighter speckle is paper


_zips = {}   # one (ZipFile, id -> member name) per process (label_vision.py's workers each open their own)


def _zip():
    if IMAGES_ZIP not in _zips:
        z = zipfile.ZipFile(IMAGES_ZIP)
        names = {os.path.basename(n)[:-4]: n for n in z.namelist()
                 if n.endswith(".png") and not os.path.basename(n).startswith(".")}
        _zips[IMAGES_ZIP] = z, names
    return _zips[IMAGES_ZIP]


def captcha_ids():
    """Every captcha id in the zip, in numeric order."""
    return sorted(_zip()[1], key=int)


def open_captcha(i):
    """Captcha <i> as a PIL image, read straight from the zip."""
    z, names = _zip()
    return Image.open(io.BytesIO(z.read(names[i])))


def clean(img):
    """Captcha (PIL image) -> uint8 HxW the CNN reads: letters 0, gray blobs 128, everything else 255.
    Keeping the blobs lets the model tell a stroke hidden under a blob from no stroke (new J vs 3, 6 vs 5).
    Same as extension/model.js clean(); change both or neither."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    letter = (r - g > RED_MIN) & (r - b > RED_MIN)
    blob = ~letter & (r + g + b < 3 * BLOB_MAX)
    return np.select([letter, blob], [0, 128], 255).astype(np.uint8)


def ink(img):
    """Captcha (PIL image) -> uint8 HxW, letters 0 (black) and everything else 255 (white).
    What Vision reads, and what the two-level models (v1-v3, v4_binary) were trained on."""
    return np.where(clean(img) == 0, 0, 255).astype(np.uint8)


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
