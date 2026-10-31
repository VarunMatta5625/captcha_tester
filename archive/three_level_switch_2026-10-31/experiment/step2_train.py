"""Train one input variant on v4's labels; results -> results/<tag>.json, model -> models/<tag>.pt.

    python3 step2_train.py <binary|three|raw> <seed> [init_checkpoint]

Labels: v4's read of every non-gold captcha with confidence >= MIN_CONF (reads_v4.csv from step1_reads.py),
split 70/20/10 train/test/val with a fixed seed (same split for every run). Gold (data/gold.csv) is only scored.
Hyperparameters as the notebook's from-scratch config.
"""
import json, math, os, random, sys, time
from collections import Counter

import numpy as np
import torch
import torch.nn.functional as F

from common import (ALPHABET, CHAR_TO_IDX, DEVICE, EXP, IN_CH, LENGTH, PROJECT, CaptchaCNN, augment, load_raw, read_csv,
                    variant_input)

VARIANT, SEED = sys.argv[1], int(sys.argv[2])
INIT = sys.argv[3] if len(sys.argv) > 3 else None
TAG = f"{VARIANT}_s{SEED}" + ("_init-v4" if INIT else "")
MIN_CONF = 0.7
SPLIT_SEED = 0
CFG = dict(epochs=6, lr=5e-4, patience=3) if INIT else dict(epochs=10, lr=2e-3, patience=4)
CFG.update(batch=256, weight_decay=1e-4, dropout=0.3, smoothing=0.1, seed=SEED, min_conf=MIN_CONF, init=INIT)

ids, rgb = load_raw()
row_of = {i: k for k, i in enumerate(ids)}
X = torch.from_numpy(rgb).to(DEVICE)   # uint8 (N, H, W, 3), ~2 GB
gold = {r["id"]: r["label"] for r in read_csv(os.path.join(PROJECT, "data/gold.csv"))}
rows = [r for r in read_csv(os.path.join(EXP, "reads_v4.csv")) if r["id"] not in gold and float(r["conf"]) >= MIN_CONF]
random.Random(SPLIT_SEED).shuffle(rows)
n_train, n_test = int(0.7 * len(rows)), int(0.2 * len(rows))
splits = {"train": rows[:n_train], "test": rows[n_train:n_train + n_test], "val": rows[n_train + n_test:],
          "gold": [{"id": i, "read": t} for i, t in gold.items()]}
data = {k: (torch.tensor([row_of[r["id"]] for r in v]), torch.tensor([[CHAR_TO_IDX[c] for c in r["read"]] for r in v]))
        for k, v in splits.items()}
print(TAG, {k: len(v) for k, v in splits.items()}, CFG, flush=True)


def batches(split, bs, shuffle):
    idx, y = data[split]
    order = torch.randperm(len(idx)) if shuffle else torch.arange(len(idx))
    for k in range(0, len(idx), bs):
        j = order[k:k + bs]
        yield variant_input(X[idx[j].to(DEVICE)], VARIANT), y[j].to(DEVICE)


@torch.no_grad()
def predict(model, split):
    model.eval()
    return torch.cat([model(x).argmax(-1).cpu() for x, _ in batches(split, 1024, False)])


def evaluate(model, split):
    p, y = predict(model, split), data[split][1]
    return {"exact": (p == y).all(1).float().mean().item(), "char": (p == y).float().mean().item()}


random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
model = CaptchaCNN(len(ALPHABET), dropout=CFG["dropout"], in_ch=IN_CH[VARIANT]).to(DEVICE)
if INIT:
    model.load_state_dict(torch.load(INIT, map_location=DEVICE)["state_dict"])
opt = torch.optim.AdamW(model.parameters(), lr=CFG["lr"], weight_decay=CFG["weight_decay"])
steps = math.ceil(len(data["train"][0]) / CFG["batch"])
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=CFG["lr"], total_steps=CFG["epochs"] * steps)
best, best_state, stale, history = -1.0, None, 0, []
for epoch in range(1, CFG["epochs"] + 1):
    model.train()
    t, total = time.time(), torch.zeros((), device=DEVICE)
    for x, y in batches("train", CFG["batch"], True):
        loss = F.cross_entropy(model(augment(x)).flatten(0, 1), y.flatten(), label_smoothing=CFG["smoothing"])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        sched.step()
        total += loss.detach()
    val, g = evaluate(model, "val"), evaluate(model, "gold")
    history.append({"epoch": epoch, "loss": total.item() / steps, "val": val, "gold": g})
    print(f"{TAG} epoch {epoch:>2}  loss {total.item() / steps:.3f}  val {val['exact']:.2%}  gold {g['exact']:.2%}  "
          f"{time.time() - t:.0f}s", flush=True)
    if val["exact"] > best:
        best, stale = val["exact"], 0
        best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    else:
        stale += 1
        if stale >= CFG["patience"]:
            break
model.load_state_dict(best_state)

scores = {s: evaluate(model, s) for s in ("val", "test", "gold")}
p, y = predict(model, "gold"), data["gold"][1]
conf = Counter((ALPHABET[a], ALPHABET[b]) for pp, yy in zip(p, y) for a, b in zip(yy.tolist(), pp.tolist()) if a != b)
misses = [(r["id"], r["read"], "".join(ALPHABET[j] for j in p[k].tolist()))
          for k, r in enumerate(splits["gold"]) if not torch.equal(p[k], y[k])]
os.makedirs(os.path.join(EXP, "results"), exist_ok=True)
os.makedirs(os.path.join(EXP, "models"), exist_ok=True)
json.dump({"tag": TAG, "variant": VARIANT, "seed": SEED, "cfg": CFG, "scores": scores, "history": history,
           "gold_confusions": conf.most_common(), "gold_misses": misses,
           "best_epoch": max(history, key=lambda h: h["val"]["exact"])["epoch"]},
          open(os.path.join(EXP, "results", f"{TAG}.json"), "w"), indent=1)
torch.save({"state_dict": model.state_dict(), "alphabet": ALPHABET, "length": LENGTH,
            "widths": (32, 64, 128, 192), "config": CFG, "in_ch": IN_CH[VARIANT], "variant": VARIANT},
           os.path.join(EXP, "models", f"{TAG}.pt"))
print(f"{TAG} DONE  " + "  ".join(f"{s} {v['exact']:.2%}" for s, v in scores.items()), flush=True)
