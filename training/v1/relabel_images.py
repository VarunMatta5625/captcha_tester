# Relabel every captcha with the fine-tuned model -> labels_v2.csv, for training a new baseline.
# Run from the training notebook (after cells 1-6):  %run -i relabel_images.py
#
#   gold (hand-checked)  copied unchanged, never relabeled, stays the test set
#   your reviews         your typed answers, source "review"
#   everything else      the model's read, source "model" (incl. images Vision had rejected)
import json

RELABEL_MODEL = "captcha_cnn_ft.pt"
REVIEWS = "model_reviews.json"
OUT = "labels_v2.csv"


def load_model(path=MODEL_PATH):
    ckpt = torch.load(path, map_location=DEVICE)
    m = CaptchaCNN(len(ckpt["alphabet"]), ckpt["length"], ckpt["widths"],
                   ckpt["config"]["dropout"]).to(DEVICE)
    m.load_state_dict(ckpt["state_dict"])
    return m.eval(), ckpt


@torch.no_grad()
def read_array(m, a, batch_size=2048):
    """uint8 images (N, H, W) -> model reads + weakest-character confidence."""
    m.eval()
    reads, confs = [], []
    for k in range(0, len(a), batch_size):
        x = to_input(torch.from_numpy(a[k:k + batch_size]).to(DEVICE))
        conf, idx = m(x).softmax(-1).max(-1)
        reads += ["".join(ALPHABET[i] for i in p) for p in idx.cpu().tolist()]
        confs += conf.min(-1).values.cpu().tolist()
    return reads, confs


with open("labels.csv") as f:          # all images, including Vision's rejected ones
    all_rows = list(csv.DictReader(f))
gold_ids = {r["id"] for r in all_rows if r["source"] == "human"}
reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
assert not gold_ids & set(reviews), "a gold captcha is in the reviews"

todo = [r for r in all_rows if r["source"] != "human"]
# images already in memory come from X's cache; Vision's rejected ones are read from disk
arr = np.stack([imgs[row_of[r["id"]]] if r["id"] in row_of else read_gray(r["id"]) for r in todo])
relabel_model, _ = load_model(RELABEL_MODEL)
reads, confs = read_array(relabel_model, arr)

out, count = [], Counter()
for r in all_rows:
    if r["source"] == "human":
        out.append({"id": r["id"], "label": r["label"], "source": "human", "confidence": "",
                    "vision_label": r["label"], "raw": r["raw"]})
for r, read, conf in zip(todo, reads, confs):
    if r["id"] in reviews:
        label, source = reviews[r["id"]]["truth"], "review"
    else:
        label, source = read, "model"
    count[source] += 1
    count["changed from Vision"] += source == "model" and r["source"] == "vision" and read != r["label"]
    out.append({"id": r["id"], "label": label, "source": source, "confidence": f"{conf:.3f}",
                "vision_label": r["label"], "raw": r["raw"]})
out.sort(key=lambda r: int(r["id"]))

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "label", "source", "confidence", "vision_label", "raw"])
    w.writeheader()
    w.writerows(out)

print(f"wrote {OUT}: {len(out)} rows  human {len(gold_ids)}  review {count['review']}  model {count['model']}")
print(f"model disagrees with Vision's label on {count['changed from Vision']} images")
c = np.array([float(x) for x in confs])
for t in (0.3, 0.4, 0.5, 0.6):
    print(f"  model confidence < {t}: {(c < t).sum():>6} images ({(c < t).mean():.1%})")
