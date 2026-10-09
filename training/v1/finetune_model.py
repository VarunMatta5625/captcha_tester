# Fine-tune the saved baseline on your reviewed captchas (model_reviews.json).
# Run from the training notebook (after cells 1-6) with:  %run -i finetune_model.py
# Starts from the baseline every time, using all reviews so far. Saves to a new file.
import json

REVIEWS = "model_reviews.json"
FT_PATH = "captcha_cnn_ft.pt"
FT = dict(
    epochs=2, lr=2e-4, weight_decay=1e-4, batch=256, smoothing=0.1,
    repeat=None,   # times each reviewed captcha is shown per epoch; None = set from review count below
    anchors=5000,  # plus 5000 ordinary training captchas, so it doesn't forget the rest
    seed=SEED,
)


def load_model(path=MODEL_PATH):
    ckpt = torch.load(path, map_location=DEVICE)
    m = CaptchaCNN(len(ckpt["alphabet"]), ckpt["length"], ckpt["widths"],
                   ckpt["config"]["dropout"]).to(DEVICE)
    m.load_state_dict(ckpt["state_dict"])
    return m.eval(), ckpt


gold_ids = {r["id"] for r in gold}
reviews = json.load(open(REVIEWS))
ids = [i for i in reviews if i not in gold_ids]   # gold is never trained on
truth = {i: reviews[i]["truth"] for i in ids}
n_wrong = sum(not reviews[i]["model_right"] for i in ids)
print(f"{len(ids)} reviewed captchas, model was wrong on {n_wrong}")
# keep reviews from outweighing the 5000 ordinary captchas as they pile up
FT["repeat"] = FT["repeat"] or (20 if len(ids) <= 250 else 10 if len(ids) <= 500 else 5)
print(f"each review repeated {FT['repeat']}x per epoch")

anchor_pool = random.Random(FT["seed"]).sample(split_rows["train"], FT["anchors"])
anchor_rows = [r for r in anchor_pool if r["id"] not in truth]
rev_idx = torch.tensor([row_of[i] for i in ids])
rev_y = torch.tensor([encode(truth[i]) for i in ids])
anchor_idx = torch.tensor([row_of[r["id"]] for r in anchor_rows])
anchor_y = torch.tensor([encode(r["label"]) for r in anchor_rows])
data["reviewed"] = (rev_idx, rev_y)
data["ft"] = (torch.cat([rev_idx.repeat(FT["repeat"]), anchor_idx]),
              torch.cat([rev_y.repeat(FT["repeat"], 1), anchor_y]))

ft_model, ckpt = load_model(MODEL_PATH)   # always from the baseline
before = {s: evaluate(ft_model, s) for s in ("reviewed", "gold", "test")}

torch.manual_seed(FT["seed"])
opt = torch.optim.AdamW(ft_model.parameters(), lr=FT["lr"], weight_decay=FT["weight_decay"])
for epoch in range(1, FT["epochs"] + 1):
    ft_model.train()
    for x, y in batches("ft", FT["batch"], shuffle=True):
        logits = ft_model(augment(x))
        loss = F.cross_entropy(logits.flatten(0, 1), y.flatten(), label_smoothing=FT["smoothing"])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    r, g = evaluate(ft_model, "reviewed"), evaluate(ft_model, "gold")
    print(f"epoch {epoch}/{FT['epochs']}  reviewed exact {r['exact']:.2%}  "
          f"gold exact {g['exact']:.2%}", flush=True)

after = {s: evaluate(ft_model, s) for s in ("reviewed", "gold", "test")}
print("\n                  before  ->  after")
for s in before:
    b, a = before[s], after[s]
    print(f"{s:<9} exact {b['exact']:7.2%} -> {a['exact']:7.2%}   "
          f"char {b['char']:7.2%} -> {a['char']:7.2%}")

torch.save({**ckpt, "state_dict": ft_model.state_dict(),
            "finetune": {**FT, "reviewed_ids": ids}, "scores": after}, FT_PATH)
print(f"saved {FT_PATH}")
