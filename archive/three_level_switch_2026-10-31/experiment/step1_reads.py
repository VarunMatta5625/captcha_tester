"""v4 reads every captcha -> reads_v4.csv (id, read, conf, vision); then how candidate label rules do on gold."""
import csv, os
from collections import Counter

import numpy as np
import torch

from common import ALPHABET, DEVICE, EXP, PROJECT, load_ckpt_model, load_raw, read_csv, variant_input

ids, rgb = load_raw()
model = load_ckpt_model(os.path.join(PROJECT, "models/captcha_cnn_v4.pt"))
reads, confs = [], []
with torch.no_grad():
    for k in range(0, len(ids), 2048):
        x = variant_input(torch.from_numpy(rgb[k:k + 2048]).to(DEVICE), "binary")
        c, i = model(x).softmax(-1).max(-1)
        reads += ["".join(ALPHABET[j] for j in r) for r in i.cpu().tolist()]
        confs += c.min(-1).values.cpu().tolist()
vision = {r["id"]: r["vision"] for r in read_csv(os.path.join(PROJECT, "data/labels_vision.csv"))}
with open(os.path.join(EXP, "reads_v4.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "read", "conf", "vision"])
    for i, r, c in zip(ids, reads, confs):
        w.writerow([i, r, f"{c:.4f}", vision[i]])

read_of = dict(zip(ids, reads)); conf_of = dict(zip(ids, confs))
gold = {r["id"]: r["label"] for r in read_csv(os.path.join(PROJECT, "data/gold.csv"))}
print(f"v4 on gold: {np.mean([read_of[i] == t for i, t in gold.items()]):.1%}")

def agree(i):
    return vision[i] and vision[i] == read_of[i]

rules = {"agree (v4 == Vision)": agree}
for t in (0.5, 0.7, 0.8, 0.9, 0.95):
    rules[f"conf >= {t}"] = (lambda t: lambda i: conf_of[i] >= t)(t)
    rules[f"agree or conf >= {t}"] = (lambda t: lambda i: agree(i) or conf_of[i] >= t)(t)
non_gold = [i for i in ids if i not in gold]
print(f"{'rule':<26} {'gold kept':>9} {'wrong':>6} {'label err':>9} {'100k kept':>9}")
for name, keep in rules.items():
    kept = [i for i in gold if keep(i)]
    wrong = sum(read_of[i] != gold[i] for i in kept)
    n_all = sum(1 for i in non_gold if keep(i))
    print(f"{name:<26} {len(kept):>9} {wrong:>6} {wrong / max(len(kept), 1):>9.1%} {n_all:>9}")
print("v4 gold misses:", [(i, read_of[i], gold[i], f"{conf_of[i]:.2f}", vision[i] or "-")
                          for i in gold if read_of[i] != gold[i]])
