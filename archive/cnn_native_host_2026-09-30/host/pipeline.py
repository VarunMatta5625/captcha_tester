"""Captcha pipeline from `Main file.ipynb`: clean -> Apple Vision OCR -> restrict.

Cleanup, PARAMS and the lookalike map are copied from the notebook so the extension reads
captchas exactly the way the notebook scores them. If you retune PARAMS there, copy them here too.
"""
import csv, glob, json, os, re, subprocess, tempfile
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
OCR = os.path.join(HERE, "ocr")   # Apple Vision, accurate mode (built from ocr.swift)
LOG = os.path.join(DATA, "ocr_review.json")   # the notebook's review log
ROUNDS = os.path.join(DATA, "rounds")         # older labeled rounds (label vs raw OCR)

PARAMS = dict(
    LETTER_MAX=35,  # pixel <= this counts as letter (dark gray, not pure black)
    LEVEL_TOL=6,    # pixel within this of its line's gray counts as line core
    WIN=3,          # half-size of window used to find the local line gray
    MAX_GAP=2,      # widest line cut (px) bridged inside a letter
    SCALE=2,        # upscale factor before OCR
    THICKEN=3,      # MinFilter size that fattens strokes (odd, 1 = off)
    BLUR=1.5,       # Gaussian blur radius (0 = off)
    LINE_MIN=30,    # darkest gray allowed when estimating a line's gray
    BG_MIN=250,     # pixel >= this counts as background
    BORDER=40,      # white border added around the output
    CLOSE=0,        # radius of mask closing (0 = off)
    MIN_BLOB=0,     # drop connected blobs smaller than this many pixels (0 = off)
)
DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]

# every character seen in the 152 hand-checked labels; a read using anything else is wrong
ALPHABET = "2345689ABDEFGHJLMNQRTYabdefghijmnqrty"
LENGTH = 5


# walk from (y, x) in one direction over line-core pixels (state 1)
# returns (steps taken, state of the pixel that ended the walk)
# if the run is longer than max_gap it gives up and returns (n, 1)
def _walk(state, y, x, dy, dx, max_gap):
    h, w = state.shape
    n = 0
    while True:
        y = y + dy
        x = x + dx
        if not (0 <= y < h and 0 <= x < w):
            return n, 0
        if state[y, x] != 1:
            return n, state[y, x]
        n = n + 1
        if n > max_gap:
            return n, 1

# stage 1: find the masks (slow part)
def find_masks(a, **overrides):
    p = dict(PARAMS)
    p.update(overrides)
    a = a.astype(int)
    letters = a <= p["LETTER_MAX"]
    noise = (a > p["LETTER_MAX"]) & (a < p["BG_MIN"])
    r = p["WIN"]

    # for each noise pixel, the most common gray in its window = gray of the line through it
    level = np.zeros_like(a)
    for y, x in zip(*np.where(noise)):
        win = a[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1]
        vals = win[(win > p["LINE_MIN"]) & (win < p["BG_MIN"])]
        if vals.size:
            v, c = np.unique(vals, return_counts=True)
            level[y, x] = v[np.argmax(c)]
    core = noise & (np.abs(a - level) <= p["LEVEL_TOL"])

    # 0 = background, 1 = line core, 2 = letter
    state = np.zeros_like(a)
    state[core] = 1
    state[letters] = 2

    # line core pixel whose shortest run is <= MAX_GAP with letter at both ends = a cut, fill it
    fill = np.zeros_like(core)
    for y, x in zip(*np.where(core)):
        best = None
        for dy, dx in DIRS:
            n1, e1 = _walk(state, y, x, dy, dx, p["MAX_GAP"])
            n2, e2 = _walk(state, y, x, -dy, -dx, p["MAX_GAP"])
            span = n1 + n2 + 1
            if best is None or span < best[0]:
                best = (span, e1, e2)
        if best[0] <= p["MAX_GAP"] and best[1] == 2 and best[2] == 2:
            fill[y, x] = True
    return letters, core, fill

# stage 2: heal small breaks, drop tiny specks (both off by default)
def tidy(mask, **overrides):
    p = dict(PARAMS)
    p.update(overrides)
    if p["CLOSE"] > 0:
        size = 2 * p["CLOSE"] + 1
        mask = ndimage.binary_closing(mask, structure=np.ones((size, size), dtype=bool))
    if p["MIN_BLOB"] > 0:
        labeled, count = ndimage.label(mask, structure=np.ones((3, 3)))
        keep = np.zeros(count + 1, dtype=bool)
        for k in range(1, count + 1):
            if (labeled == k).sum() >= p["MIN_BLOB"]:
                keep[k] = True
        mask = keep[labeled]
    return mask

# stage 3: boolean letter mask -> final image (upscale, thicken, blur, border)
def render(mask, **overrides):
    p = dict(PARAMS)
    p.update(overrides)
    im = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8))
    im = im.resize((im.width * p["SCALE"], im.height * p["SCALE"]), Image.LANCZOS)
    if p["THICKEN"] > 1:
        im = im.filter(ImageFilter.MinFilter(p["THICKEN"]))
    if p["BLUR"]:
        im = im.filter(ImageFilter.GaussianBlur(p["BLUR"]))
    im = ImageOps.expand(im, border=p["BORDER"], fill=255)
    return np.array(im)

def clean(a, **overrides):
    letters, core, fill = find_masks(a, **overrides)
    return render(tidy(letters | fill, **overrides), **overrides)


def ocr_many(images):
    """Cleaned image arrays -> raw texts, one Vision call for all (much faster than one call each)."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = [os.path.join(tmp, f"{i}.png") for i in range(len(images))]
        for c, p in zip(images, paths):
            Image.fromarray(c).save(p)
        out = subprocess.run([OCR] + paths, capture_output=True, text=True, check=True).stdout
    got = dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)
    return [got.get(p, "").strip() for p in paths]

def ocr(c):
    """Cleaned image array -> raw text Apple Vision reads."""
    return ocr_many([c])[0]


# Vision has no character whitelist and sometimes returns symbols, Cyrillic/Greek lookalikes, or
# letters the captcha never uses. Map those to the true character they most often stood for.
HOMOGLYPHS = dict(zip(   # fallback for lookalikes not seen in labeled data yet
    "АВЕЗКМНОРСТУХЅІЈЬаеіјорсухԁһԛѕзбΑΒΕΖΗΙΚΜΝΟΡΤΥΧαοιν",
    "ABE3KMHOPCTyXSIJbaeijopcyxdhqs36ABEZHIKMNOPTYXaoiv"))

def labeled_pairs():
    """(truth, raw OCR) from the old labeled rounds and from your reviews."""
    for f in glob.glob(os.path.join(ROUNDS, "r*", "results.csv")):
        with open(f) as fh:
            yield from ((r["label"], r["raw"]) for r in csv.DictReader(fh) if r["label"])
    if os.path.exists(LOG):
        with open(LOG) as fh:
            yield from ((r["truth"], r["raw"]) for r in json.load(fh)["reviews"].values())

def learn_map():
    """OCR char outside the captcha alphabet -> true char it most often stood for."""
    pairs = list(labeled_pairs())
    alphabet = set("".join(t for t, _ in pairs))
    votes = defaultdict(Counter)
    for truth, raw in pairs:
        if len(truth) == len(raw):   # only aligned reads say which char stood for which
            for g, t in zip(raw, truth):
                if g != t and g not in alphabet:
                    votes[g][t] += 1
    return {**HOMOGLYPHS, **{g: v.most_common(1)[0][0] for g, v in votes.items()}}

LOOKALIKE = learn_map()   # Chrome starts a fresh host per captcha, so new reviews count right away

def restrict(text):
    """Raw OCR -> only English letters/digits, at most 5."""
    text = "".join(LOOKALIKE.get(ch, ch) for ch in text)
    return re.sub(r"[^A-Za-z0-9]", "", text)[:LENGTH]


def decode(raw):
    """Raw Vision text -> captcha code, or '' unless it is exactly 5 alphabet chars."""
    text = restrict(raw)
    valid = len(text) == LENGTH and all(ch in ALPHABET for ch in text)
    return text if valid else ""

def solve(a):
    """Grayscale captcha array -> (code, raw)."""
    raw = ocr(clean(a))
    return decode(raw), raw
