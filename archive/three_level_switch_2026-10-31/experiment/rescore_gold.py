"""Experiment models on the corrected gold (19263, 79474 fixed)."""
import glob, json, os
import numpy as np, torch
from common import ALPHABET, DEVICE, PROJECT, load_ckpt_model, read_csv, variant_input, prep
gold = {r["id"]: r["label"] for r in read_csv(os.path.join(PROJECT, "data/gold.csv"))}
G = torch.from_numpy(np.stack([np.asarray(prep.open_captcha(i).convert("RGB")) for i in gold])).to(DEVICE)
def acc(m, v):
    with torch.no_grad():
        idx = m(variant_input(G, v)).argmax(-1).cpu().tolist()
    return np.mean(["".join(ALPHABET[j] for j in r) == t for r, t in zip(idx, gold.values())])
print(f"v4 binary: {acc(load_ckpt_model(os.path.join(PROJECT, 'models/captcha_cnn_v4_binary.pt')), 'binary'):.1%}")
for p in sorted(glob.glob("results/*.json")):
    r = json.load(open(p))
    print(f"{r['tag']:<20} old gold {r['scores']['gold']['exact']:.1%}  fixed gold {acc(load_ckpt_model('models/' + r['tag'] + '.pt'), r['variant']):.1%}")
