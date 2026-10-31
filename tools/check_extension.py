"""Check a checkpoint the way the extension will run it, before shipping.

    python3 tools/check_extension.py [models/<model>.pt]      (default: models/captcha_cnn_v4.pt)

Exports the checkpoint to a temporary folder (export_model.py), then reads gold (data/gold.csv) and the site's
rejections (data/site_mistakes/labels.csv) twice: with PyTorch (prep.clean or prep.ink, per the checkpoint's
`levels`) and with the extension's own model.js + model.wasm in Node (check_extension.mjs). Every read must match;
prints both scores. Needs node.
"""
import csv, json, os, subprocess, sys, tempfile

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "scripts")]
import export_model, prep  # noqa: E402


class CaptchaCNN(nn.Module):   # same network as the notebooks (inference only)
    def __init__(self, n_classes, length, widths, W):
        super().__init__()
        layers, c_in = [], 1
        for c in widths:
            layers += [nn.Conv2d(c_in, c, 3, padding=1, bias=False), nn.BatchNorm2d(c), nn.ReLU(),
                       nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c), nn.ReLU(), nn.MaxPool2d(2)]
            c_in = c
        self.features = nn.Sequential(*layers)
        self.shared = nn.Sequential(nn.Flatten(), nn.Dropout(), nn.Linear(c_in * (W // 2 ** len(widths)), 512),
                                    nn.ReLU(), nn.Dropout())
        self.heads = nn.ModuleList(nn.Linear(512, n_classes) for _ in range(length))

    def forward(self, x):
        z = self.shared(self.features(x).mean(dim=2))
        return torch.stack([head(z) for head in self.heads], dim=1)


def main(path):
    ck = torch.load(path, map_location="cpu")
    levels = ck.get("levels", 2)
    h, w = ck["image_size"]
    model = CaptchaCNN(len(ck["alphabet"]), ck["length"], ck["widths"], w)
    model.load_state_dict(ck["state_dict"])
    model.eval()

    gold = list(csv.DictReader(open(os.path.join(ROOT, "data", "gold.csv"))))
    site_dir = os.path.join(ROOT, "data", "site_mistakes")
    site_csv = os.path.join(site_dir, "labels.csv")
    site = list(csv.DictReader(open(site_csv))) if os.path.exists(site_csv) else []
    imgs = ([prep.open_captcha(r["id"]).convert("RGB") for r in gold] +
            [Image.open(os.path.join(site_dir, r["file"])).convert("RGB") for r in site])
    labels = [r["label"] for r in gold] + [r["truth"] for r in site]

    g = np.stack([(prep.clean if levels == 3 else prep.ink)(im) for im in imgs])
    with torch.no_grad():
        conf, idx = model((1 - torch.from_numpy(g).float() / 255).unsqueeze(1)).softmax(-1).max(-1)
    reads = ["".join(ck["alphabet"][j] for j in r) for r in idx.tolist()]

    with tempfile.TemporaryDirectory() as tmp:
        export_model.OUT = tmp
        export_model.main(path)
        np.stack([np.asarray(im.convert("RGBA")) for im in imgs]).tofile(os.path.join(tmp, "images.rgba"))
        json.dump({"reads": reads, "conf": conf.min(-1).values.tolist()}, open(os.path.join(tmp, "torch.json"), "w"))
        js = subprocess.run(["node", os.path.join(ROOT, "tools", "check_extension.mjs"), tmp],
                            check=True, capture_output=True, text=True).stdout
    js = json.loads(js)

    n_gold = len(gold)
    score = lambda rs, a, b: sum(r == t for r, t in zip(rs[a:b], labels[a:b]))
    same = sum(a == b for a, b in zip(js["reads"], reads))
    print(f"{os.path.basename(path)}: levels {levels}, JS == PyTorch on {same}/{len(reads)}, "
          f"max confidence diff {js['max_conf_diff']:.1e}, {js['ms']:.1f} ms/captcha in Node")
    for name, rs in (("PyTorch", reads), ("JS", js["reads"])):
        print(f"  {name:<7} gold {score(rs, 0, n_gold)}/{n_gold}, site rejections {score(rs, n_gold, None)}/{len(site)}")
    for k, (a, b) in enumerate(zip(js["reads"], reads)):
        if a != b:
            print(f"  MISMATCH {(gold + site)[k]}: JS {a}, PyTorch {b}")
    sys.exit(0 if same == len(reads) else 1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "models", "captcha_cnn_v4.pt"))
