"""Shared pieces for the input-variant experiment (mirrors notebooks/train_v4.ipynb, plus an in_ch parameter)."""
import csv, math, os, sys, time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

PROJECT = "/Users/varunmatta/Drive/Varun/Projects/captcha_tester"
EXP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))
import prep  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
ALPHABET, LENGTH = prep.ALPHABET, prep.LENGTH
CHAR_TO_IDX = {c: i for i, c in enumerate(ALPHABET)}
BLOB_MAX = 200   # three-level: a non-red pixel darker than this (mean of r, g, b) is a blob


class CaptchaCNN(nn.Module):
    def __init__(self, n_classes, length=LENGTH, widths=(32, 64, 128, 192), dropout=0.3, in_ch=1, W=150):
        super().__init__()
        layers, c_in = [], in_ch
        for c in widths:
            layers += [
                nn.Conv2d(c_in, c, 3, padding=1, bias=False), nn.BatchNorm2d(c), nn.ReLU(inplace=True),
                nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c), nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            ]
            c_in = c
        self.features = nn.Sequential(*layers)
        n_cols = W // 2 ** len(widths)
        self.shared = nn.Sequential(nn.Flatten(), nn.Dropout(dropout),
                                    nn.Linear(c_in * n_cols, 512), nn.ReLU(inplace=True), nn.Dropout(dropout))
        self.heads = nn.ModuleList(nn.Linear(512, n_classes) for _ in range(length))

    def forward(self, x):
        z = self.features(x).mean(dim=2)
        z = self.shared(z)
        return torch.stack([head(z) for head in self.heads], dim=1)


def load_ckpt_model(path):
    ckpt = torch.load(path, map_location=DEVICE)
    m = CaptchaCNN(len(ckpt["alphabet"]), ckpt["length"], ckpt["widths"], ckpt["config"]["dropout"],
                   in_ch=ckpt.get("in_ch", 1)).to(DEVICE)
    m.load_state_dict(ckpt["state_dict"])
    return m.eval()


def load_raw():
    """All captchas as uint8 RGB (N, 45, 150, 3), cached in the experiment folder."""
    path = os.path.join(EXP, "raw.npz")
    ids = np.array(prep.captcha_ids())
    if os.path.exists(path):
        c = np.load(path)
        if np.array_equal(c["ids"], ids):
            return ids, c["rgb"]
    from concurrent.futures import ThreadPoolExecutor
    t = time.time()
    with ThreadPoolExecutor(8) as ex:
        rgb = np.stack(list(ex.map(lambda i: np.asarray(prep.open_captcha(i).convert("RGB")), ids)))
    np.savez(path, ids=ids, rgb=rgb)
    print(f"decoded {len(ids)} captchas in {time.time() - t:.0f}s", flush=True)
    return ids, rgb


def variant_input(rgb_u8, variant):
    """uint8 RGB torch (B, H, W, 3) on DEVICE -> float (B, C, H, W): ink/dark = 1, paper = 0."""
    x = rgb_u8.to(torch.int16)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    red = (r - g > prep.RED_MIN) & (r - b > prep.RED_MIN)
    if variant == "binary":   # = prep.ink + to_input
        return red.float().unsqueeze(1)
    if variant == "three":    # letters 1, blobs 0.5, background 0
        blob = (~red) & (x.float().mean(-1) < BLOB_MAX)
        return (red.float() + 0.5 * blob.float()).unsqueeze(1)
    if variant == "raw":      # inverted RGB, so white paper = 0 like the other variants
        return (1 - x.float() / 255).permute(0, 3, 1, 2)
    raise ValueError(variant)


IN_CH = {"binary": 1, "three": 1, "raw": 3}


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def augment(x, max_shift=4, max_rot=4):
    b, _, h, w = x.shape
    rnd = lambda: torch.rand(b, device=x.device) * 2 - 1
    ang = rnd() * max_rot * math.pi / 180
    cos, sin = torch.cos(ang), torch.sin(ang)
    tx, ty = rnd() * max_shift * 2 / w, rnd() * max_shift * 2 / h
    theta = torch.stack([torch.stack([cos, -sin * h / w, tx], 1),
                         torch.stack([sin * w / h, cos, ty], 1)], 1)
    grid = F.affine_grid(theta, x.shape, align_corners=False)
    return F.grid_sample(x, grid, padding_mode="zeros", align_corners=False)
