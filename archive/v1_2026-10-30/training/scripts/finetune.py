# Fine-tune the round's baseline (MODEL_PATH) on all your reviews -> FT_PATH.
# Run from a round's notebook after its setup and training cells:  %run -i ../scripts/finetune.py
# Starts from the baseline every time, so re-running after more reviews never stacks fine-tunes.
# Gold is never trained on.
import json

FT = dict(
    epochs=2, lr=2e-4, weight_decay=1e-4, batch=256, smoothing=0.1,
    repeat=None,   # times each review is shown per epoch; None = set from the review count below
    anchors=5000,  # plus this many ordinary training captchas, so it doesn't forget the rest
    seed=SEED,
)

reviews = json.load(open(REVIEWS))
ids = [i for i in reviews if i not in GOLD]
truth = {i: reviews[i]["truth"] for i in ids}
print(f"{len(ids)} reviews, the reviewing model was wrong on {sum(not reviews[i]['model_right'] for i in ids)}")
# keep reviews from outweighing the ordinary captchas as they pile up
FT["repeat"] = FT["repeat"] or (20 if len(ids) <= 250 else 10 if len(ids) <= 500 else 5)
print(f"each review repeated {FT['repeat']}x per epoch")

anchor_pool = random.Random(FT["seed"]).sample(split_rows["train"], FT["anchors"])
anchor_rows = [r for r in anchor_pool if r["id"] not in truth]
rev_idx = torch.tensor([row_of[i] for i in ids])
rev_y = torch.tensor([encode(truth[i]) for i in ids])
data["reviewed"] = (rev_idx, rev_y)
data["ft"] = (torch.cat([rev_idx.repeat(FT["repeat"]), torch.tensor([row_of[r["id"]] for r in anchor_rows])]),
              torch.cat([rev_y.repeat(FT["repeat"], 1), torch.tensor([encode(r["label"]) for r in anchor_rows])]))

ft_model, ckpt = load_model(MODEL_PATH)   # always from the baseline
before = {s: evaluate(ft_model, s) for s in ("reviewed", "gold", "test")}

torch.manual_seed(FT["seed"])
opt = torch.optim.AdamW(ft_model.parameters(), lr=FT["lr"], weight_decay=FT["weight_decay"])
for epoch in range(1, FT["epochs"] + 1):
    ft_model.train()
    for x, y in batches("ft", FT["batch"], shuffle=True):
        loss = F.cross_entropy(ft_model(augment(x)).flatten(0, 1), y.flatten(), label_smoothing=FT["smoothing"])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    r, g = evaluate(ft_model, "reviewed"), evaluate(ft_model, "gold")
    print(f"epoch {epoch}/{FT['epochs']}  reviewed exact {r['exact']:.2%}  gold exact {g['exact']:.2%}", flush=True)

after = {s: evaluate(ft_model, s) for s in ("reviewed", "gold", "test")}
print("\n                  before  ->  after")
for s in before:
    b, a = before[s], after[s]
    print(f"{s:<9} exact {b['exact']:7.2%} -> {a['exact']:7.2%}   char {b['char']:7.2%} -> {a['char']:7.2%}")

torch.save({**ckpt, "state_dict": ft_model.state_dict(),
            "finetune": {**FT, "reviewed_ids": ids}, "scores": after}, FT_PATH)
print(f"saved {FT_PATH}")
