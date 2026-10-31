"""Summarise every results/*.json, re-score the saved models on gold per captcha, and write report.md."""
import glob, json, os
from collections import Counter, defaultdict

import numpy as np
import torch

from common import ALPHABET, DEVICE, EXP, PROJECT, load_ckpt_model, load_raw, read_csv, variant_input

ids, rgb = load_raw()
row_of = {i: k for k, i in enumerate(ids)}
gold = {r["id"]: r["label"] for r in read_csv(os.path.join(PROJECT, "data/gold.csv"))}
gids = list(gold)
G = torch.from_numpy(rgb[[row_of[i] for i in gids]]).to(DEVICE)


@torch.no_grad()
def gold_reads(model, variant):
    p = model(variant_input(G, variant)).softmax(-1)
    c, i = p.max(-1)
    return ["".join(ALPHABET[j] for j in r) for r in i.cpu().tolist()], c.min(-1).values.cpu().numpy()


res = {}
for path in sorted(glob.glob(os.path.join(EXP, "results", "*.json"))):
    r = json.load(open(path))
    m = load_ckpt_model(os.path.join(EXP, "models", r["tag"] + ".pt"))
    r["reads"], r["confs"] = gold_reads(m, r["variant"])
    res[r["tag"]] = r

v4 = load_ckpt_model(os.path.join(PROJECT, "models/captcha_cnn_v4.pt"))
v4_reads, v4_conf = gold_reads(v4, "binary")
right = lambda reads: np.array([a == gold[i] for a, i in zip(reads, gids)])

out = ["# Input-variant experiment\n",
       "Labels: v4 reads with confidence >= 0.7 (93,185 non-gold captchas), 70/20/10 train/test/val, same split for",
       "every run. From scratch, 10 epochs max, best-val epoch kept. Gold = your 200 checked captchas (scored only).\n",
       f"v4 (teacher) on gold: {right(v4_reads).mean():.1%}\n",
       "| run | best epoch | val | test | gold | gold, best epoch of the 10 | gold, mean of epochs 3-10 |",
       "|---|---|---|---|---|---|---|"]
for t, r in res.items():
    h = r["history"]
    out.append(f"| {t} | {r['best_epoch']} | {r['scores']['val']['exact']:.2%} | {r['scores']['test']['exact']:.2%} | "
               f"{r['scores']['gold']['exact']:.1%} | {max(e['gold']['exact'] for e in h):.1%} | "
               f"{np.mean([e['gold']['exact'] for e in h if e['epoch'] >= 3]):.1%} |")

by_var = defaultdict(list)
for t, r in res.items():
    by_var[r["variant"]].append(r)
out += ["\n## Per variant (mean over seeds)\n", "| variant | seeds | val | gold | gold, mean of epochs 3-10 | gold misses (union over seeds) |",
        "|---|---|---|---|---|---|"]
for v, rs in by_var.items():
    union = set().union(*({i for i, ok in zip(gids, right(r["reads"])) if not ok} for r in rs))
    out.append(f"| {v} | {len(rs)} | {np.mean([r['scores']['val']['exact'] for r in rs]):.2%} | "
               f"{np.mean([r['scores']['gold']['exact'] for r in rs]):.1%} | "
               f"{np.mean([e['gold']['exact'] for r in rs for e in r['history'] if e['epoch'] >= 3]):.1%} | {len(union)} |")

out += ["\n## Gold confusions (true -> read), summed over seeds\n"]
for v, rs in by_var.items():
    c = Counter()
    for r in rs:
        c.update(tuple(x) for x, n in r["gold_confusions"] for _ in range(n))
    out.append(f"- **{v}**: " + ", ".join(f"{a}->{b} x{n}" for (a, b), n in c.most_common(12)))
c = Counter((a, b) for i, rd in zip(gids, v4_reads) for a, b in zip(gold[i], rd) if a != b)
out.append("- **v4 (teacher)**: " + ", ".join(f"{a}->{b} x{n}" for (a, b), n in c.most_common(12)))

out += ["\n## Every gold captcha any run gets wrong\n",
        "| id | truth | v4 | " + " | ".join(res) + " |", "|---|---|---|" + "---|" * len(res)]
wrong_any = [k for k, i in enumerate(gids) if v4_reads[k] != gold[i] or any(r["reads"][k] != gold[i] for r in res.values())]
for k in wrong_any:
    i = gids[k]
    cell = lambda s: "ok" if s == gold[i] else s
    out.append(f"| {i} | {gold[i]} | {cell(v4_reads[k])} | " + " | ".join(cell(r["reads"][k]) for r in res.values()) + " |")

# ensemble of all runs of a variant (mean softmax): a cheap extra data point
out += ["\n## Ensembles on gold (mean of softmax over that variant's seeds)\n"]
for v, rs in by_var.items():
    with torch.no_grad():
        x = variant_input(G, v)
        p = sum(load_ckpt_model(os.path.join(EXP, "models", r["tag"] + ".pt"))(x).softmax(-1) for r in rs) / len(rs)
    reads = ["".join(ALPHABET[j] for j in row) for row in p.argmax(-1).cpu().tolist()]
    out.append(f"- {v} ({len(rs)} models): {right(reads).mean():.1%}")

# real site rejections (style 3 only, saved by the extension; truth = my reading, not checked by the user)
mist = sorted(glob.glob(os.path.expanduser("~/Downloads/captcha_mistakes/2026*08*.png")))
truth = "3nJTr JMbe5 JAhJ3 J8NNt gjt9J Y8y9N 5g8Nf 8LarJ".split()
if len(mist) == len(truth):
    from PIL import Image
    M = torch.from_numpy(np.stack([np.asarray(Image.open(p).convert("RGB")) for p in mist])).to(DEVICE)
    out += ["\n## The 8 captchas the live site rejected (truth = Claude's reading, unchecked)\n"]
    def site(m, v):
        with torch.no_grad():
            i = m(variant_input(M, v)).argmax(-1).cpu().tolist()
        return ["".join(ALPHABET[j] for j in r) for r in i]
    rd = site(v4, "binary")
    out.append(f"- v4: {sum(a == b for a, b in zip(rd, truth))}/8  " + " ".join(rd))
    for t, r in res.items():
        rd = site(load_ckpt_model(os.path.join(EXP, "models", t + ".pt")), r["variant"])
        out.append(f"- {t}: {sum(a == b for a, b in zip(rd, truth))}/8  " + " ".join(rd))

open(os.path.join(EXP, "report.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
