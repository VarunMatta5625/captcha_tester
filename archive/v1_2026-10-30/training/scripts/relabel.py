# Relabel every captcha with a trained model -> LABELS_CSV, the training labels for a new baseline.
# Run from a round's notebook after its setup cells:  %run -i ../scripts/relabel.py
# Uses the notebook's RELABEL_MODEL, LABELS_CSV, REVIEWS, GOLD, ALL_IDS, VISION, load_model, model_reads.
#
#   gold captchas     left out entirely: they live only in data/gold.csv, the test set
#   your reviews      your typed answer, source "review"
#   everything else   the model's read, source "model" (incl. images Vision gave up on)
import json

reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
assert not set(GOLD) & set(reviews), "a gold captcha is in the reviews"

relabel_model, relabel_ckpt = load_model(RELABEL_MODEL)
ids = [i for i in ALL_IDS if i not in GOLD]
reads, confs = model_reads(relabel_model, ids)

count = Counter()
with open(LABELS_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "source", "confidence", "vision_label"])
    for i, read, conf in zip(ids, reads, confs):
        if i in reviews:
            label, source = reviews[i]["truth"], "review"
        else:
            label, source = read, "model"
            count["differs from Vision"] += read != VISION[i]
        count[source] += 1
        w.writerow([i, label, source, f"{conf:.3f}", VISION[i]])

gold_reads, _ = model_reads(relabel_model, list(GOLD))
gold_right = sum(r == g["label"] for r, g in zip(gold_reads, GOLD.values()))
print(f"wrote {LABELS_CSV}: {count['model']} model labels + {count['review']} your reviews "
      f"(gold's {len(GOLD)} left out)")
print(f"relabel model {os.path.basename(RELABEL_MODEL)} on gold: {gold_right}/{len(GOLD)} "
      f"= {gold_right / len(GOLD):.2%} (the teacher's score; the new baseline should beat it)")
print(f"model label differs from Vision's on {count['differs from Vision']} images")
c = np.array(confs)
for t in (0.3, 0.4, 0.5, 0.6):
    print(f"  confidence < {t}: {(c < t).sum():>6} images ({(c < t).mean():.1%})")
