"""README figures made from the model itself (no browser): cleaning animation, per-character confidence, accuracy chart.

    python3 tools/readme_visuals/model_visuals.py         (from the project root; needs data/captchas.zip)
"""
import csv, os, sys

import numpy as np
import torch
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "tools")]
import anno, prep                                  # noqa: E402
from anno import canvas, paste_shot, note, badge, font, INK, TEAL, RED   # noqa: E402
from check_extension import CaptchaCNN             # noqa: E402

OUT = os.path.join(ROOT, "docs", "images")
GOLD = {r["id"]: r["label"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "gold.csv")))}


def up(img, k=4):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def cleaning_gif():
    """raw -> letters only -> letters + blobs, for captchas whose letters sit under a blob."""
    ids = ["150", "2836", "8152"]
    frames, durs = [], []
    steps = [("raw", "The captcha as the site sends it: red letters, gray speckle and large gray blobs."),
             ("two", "Letters only (the old two-level cleaning). Wherever a blob covered a stroke there is now a hole."),
             ("three", "Letters 0, blobs 128, paper 255 (the cleaning the model reads). A hidden stroke now looks different from no stroke.")]
    for i in ids:
        raw = prep.open_captcha(i).convert("RGB")
        arrays = {"raw": raw, "two": Image.fromarray(prep.ink(raw)).convert("RGB"), "three": Image.fromarray(prep.clean(raw)).convert("RGB")}
        for k, (key, text) in enumerate(steps, 1):
            im = canvas(f"How the extension cleans a captcha ({k} of 3)", f"captcha {GOLD[i]}")
            paste_shot(im, up(arrays[key], 6), (190, 120))
            ImageDraw.Draw(im).text((640, 80), "", font=font(1))
            note(im, (190, 440), text, w=900, size=24, n=k)
            # tiny strip with the three stages side by side
            for j, kk in enumerate(("raw", "two", "three")):
                small = arrays[kk].resize((150, 45))
                im.paste(small, (190 + j * 170, 580))
                if kk == key:
                    ImageDraw.Draw(im).rectangle([189 + j * 170, 579, 190 + j * 170 + 150, 580 + 45], outline=RED, width=3)
            frames.append(im)
            durs.append(2200 if k < 3 else 2800)
    print("cleaning.gif", anno.save_gif(frames, os.path.join(OUT, "cleaning.gif"), durs) // 1024, "KB", len(frames), "frames")


def load_model():
    ck = torch.load(os.path.join(ROOT, "models", "captcha_cnn_v5.pt"), map_location="cpu")
    m = CaptchaCNN(len(ck["alphabet"]), ck["length"], ck["widths"], ck["image_size"][1])
    m.load_state_dict(ck["state_dict"]); m.eval()
    return m, ck["alphabet"]


def reading_png(cid="2836"):
    """What the network says for each of the five positions (top 3 characters, probability)."""
    m, alphabet = load_model()
    raw = prep.open_captcha(cid).convert("RGB")
    g = prep.clean(raw)
    with torch.no_grad():
        p = m((1 - torch.from_numpy(g).float() / 255)[None, None]).softmax(-1)[0]   # 5 x 37
    top = p.topk(3, dim=-1)
    best = [alphabet[j] for j in top.indices[:, 0].tolist()]
    conf = top.values[:, 0]
    weakest = int(conf.argmin())
    im = canvas("How it reads: five small decisions", f"captcha {GOLD[cid]}, shipped model v5")
    paste_shot(im, up(raw, 3), (24, 90))
    paste_shot(im, up(Image.fromarray(g).convert("RGB"), 3), (24, 90 + 45 * 3 + 20))
    d = ImageDraw.Draw(im)
    d.text((24, 90 + 45 * 6 + 38), "raw  /  cleaned", font=font(17), fill=INK)
    x0, colw = 500, 138
    for k in range(5):
        x = x0 + 14 + k * (colw + 8)
        d.text((x + colw / 2, 86), f"position {k + 1}", font=font(18, True), fill=INK, anchor="mt")
        d.rounded_rectangle([x, 116, x + colw, 400], radius=10, outline=RED if k == weakest else (190, 200, 198), width=4 if k == weakest else 2, fill="white")
        for r in range(3):
            ch = alphabet[top.indices[k, r]]; pr = float(top.values[k, r])
            y = 132 + r * 88
            d.text((x + 12, y), ch, font=font(40, True), fill=INK if r == 0 else (120, 130, 128))
            d.rounded_rectangle([x + 58, y + 10, x + 58 + 70, y + 30], radius=5, fill=(228, 233, 231))
            d.rounded_rectangle([x + 58, y + 10, x + 58 + max(2, int(70 * pr)), y + 30], radius=5, fill=TEAL if r == 0 else (150, 170, 166))
            d.text((x + 58, y + 36), f"{pr:.3f}", font=font(16, mono=True), fill=INK)
    note(im, (500, 430), f"The read is the best character at each position: {''.join(best)}. The confidence shown in the console is the weakest of the five best probabilities: {float(conf.min()):.3f} here (position {weakest + 1}, red). Below the minimum you set (default 0.5), the extension fills the box but leaves LOGIN to you.", w=750, size=20, n=1)
    im.save(os.path.join(OUT, "reading.png"), optimize=True)
    print("reading.png", ''.join(best), GOLD[cid], float(conf.min()))


def accuracy_png():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # gold accuracy of the model each extension shipped (checkpoint 'scores' in models/ and archive/; each style has its own gold set)
    rows = [("4.1\nv1 (ft 650)", 93.4, "Style 1"), ("5.0 / 5.1\nv2_ft", 98.5, "Style 2"),
            ("5.2\nv4", 97.0, "Style 3"), ("5.3 / 5.4 / 5.5\nv5", 100.0, "Style 3")]
    colors = {"Style 1": "#8a9a96", "Style 2": "#e0a030", "Style 3": "#007467"}
    fig, ax = plt.subplots(figsize=(12.8, 5.6), dpi=100)
    bars = ax.bar([r[0] for r in rows], [r[1] for r in rows], color=[colors[r[2]] for r in rows], width=0.55)
    for b, r in zip(bars, rows):
        ax.text(b.get_x() + b.get_width() / 2, r[1] + 0.25, f"{r[1]:.1f}%", ha="center", fontsize=15, fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, 90.6, r[2], ha="center", color="white", fontsize=13)
    ax.set_ylim(90, 101.5); ax.set_ylabel("Exact match on hand-checked gold (%)", fontsize=13)
    ax.set_title("Gold accuracy of the shipped model (every captcha style has its own gold set)", fontsize=15, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "accuracy.png")); print("accuracy.png")


if __name__ == "__main__":
    cleaning_gif(); reading_png(); accuracy_png()
