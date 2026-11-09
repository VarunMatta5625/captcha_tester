"""Rebuilds the figures in docs/images/ (used by docs/CHANGELOG.md) from the captcha zips and gold sets.

    python3 tools/make_doc_figures.py      (from the project root; needs the git-ignored captcha zips)
"""
import csv, io, os, sys, zipfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "images")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import prep  # noqa: E402

plt.rcParams.update({"font.family": "monospace", "font.size": 10})


def zip_reader(path):
    z = zipfile.ZipFile(path)
    names = {os.path.basename(n)[:-4]: n for n in z.namelist() if n.endswith(".png")}
    return lambda i: Image.open(io.BytesIO(z.read(names[str(i)]))).convert("RGB")


def gold(path):
    with open(path) as f:
        return [(r["id"], r["label"]) for r in csv.DictReader(f)]


STYLES = [
    ("Style 1 (until 2026-10-30)", os.path.join(ROOT, "archive/v1_2026-10-30/training/data/varun.zip"),
     os.path.join(ROOT, "archive/v1_2026-10-30/training/data/gold.csv")),
    ("Style 2 (2026-10-30 to 10-31)", os.path.join(ROOT, "archive/v2_2026-10-31/data/captchas.zip"),
     os.path.join(ROOT, "archive/v2_2026-10-31/data/gold.csv")),
    ("Style 3 (since 2026-10-31)", os.path.join(ROOT, "data/captchas.zip"), os.path.join(ROOT, "data/gold.csv")),
]

# 1. the three captcha styles, 4 gold examples each (true label under each)
fig, axes = plt.subplots(3, 4, figsize=(12, 3.6))
for row, (title, zpath, gpath) in zip(axes, STYLES):
    read = zip_reader(zpath)
    for ax, (i, label) in zip(row, gold(gpath)[10:14]):
        ax.imshow(read(i))
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlabel(label)
    row[0].set_ylabel(title.split(" (")[0], rotation=0, ha="right", va="center")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "styles.png"), dpi=110)
plt.close(fig)

# 2. cleaning: raw -> two-level ink -> three-level clean, on style-3 gold captchas old models got wrong
read3 = zip_reader(STYLES[2][1])
cases = [("150", "J2qgj", "J read as 3"), ("71755", "m6t2J", "6 read as 5"), ("83942", "D6TnY", "6 read as 5")]
fig, axes = plt.subplots(len(cases), 3, figsize=(10, 2.6))
for r, (i, label, why) in enumerate(cases):
    img = read3(i)
    for c, (arr, name) in enumerate([(np.asarray(img), "raw"), (prep.ink(img), "two-level (prep.ink)"),
                                     (prep.clean(img), "three-level (prep.clean)")]):
        ax = axes[r, c]
        ax.imshow(arr, cmap="gray", vmin=0, vmax=255)
        ax.set_xticks([]); ax.set_yticks([])
        if r == 0: ax.set_title(name)
    axes[r, 0].set_ylabel(f"{label}\n{why}", rotation=0, ha="right", va="center", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "cleaning.png"), dpi=110)
plt.close(fig)

# 3. the 8 style-3 captchas the live site rejected from extension 5.1, with what v2_ft read and the truth
sm = os.path.join(ROOT, "data/site_mistakes")
rows = list(csv.DictReader(open(os.path.join(sm, "labels.csv"))))
fig, axes = plt.subplots(2, 4, figsize=(12, 2.6))
for ax, r in zip(axes.flat, rows):
    ax.imshow(Image.open(os.path.join(sm, r["file"])).convert("RGB"))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel(f"read {r['model_read']} / true {r['truth']}", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "site_mistakes.png"), dpi=110)
plt.close(fig)
print("wrote", sorted(os.listdir(OUT)))
