# Label every captcha with the teacher model and compare with Apple Vision -> LABELS_CSV.
# Run from the notebook after its setup and gold cells:  %run -i ../scripts/relabel.py
# Needs Vision's reads of every captcha (python3 scripts/label_vision.py, from the project root).
#
#   gold captchas      left out entirely: they live only in data/gold.csv, the test set
#   your reviews       your typed answer, source "review"          -> training
#   model == Vision    that read, source "agree"                   -> training / val / test
#   model != Vision    the model's read, source "disagree"         -> not trained on; review.py shows these first
import json

reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
assert not set(GOLD) & set(reviews), "a gold captcha is in the reviews"
with open(VISION_LABELS) as f:   # re-read: label_vision.py may have finished after the notebook loaded it
    VISION = {r["id"]: r["vision"] for r in csv.DictReader(f)}
missing = [i for i in ALL_IDS if i not in VISION]
assert not missing, f"{len(missing)} captchas have no Vision read yet: run python3 scripts/label_vision.py"

teacher, _ = load_model(TEACHER)
ids = [i for i in ALL_IDS if i not in GOLD]
reads, confs = model_reads(teacher, ids)

count = Counter()
with open(LABELS_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "source", "confidence", "model", "vision"])
    for i, read, conf in zip(ids, reads, confs):
        if i in reviews:
            label, source = reviews[i]["truth"], "review"
        else:
            label, source = read, "agree" if read == VISION[i] else "disagree"
        count[source] += 1
        w.writerow([i, label, source, f"{conf:.3f}", read, VISION[i]])

print(f"wrote {LABELS_CSV}: {count['agree']} agree with Vision, {count['disagree']} disagree, "
      f"{count['review']} your reviews; gold's {len(GOLD)} left out (the notebook's splits cell picks what trains)")
print(f"  of the disagreements, Vision gave no valid read on {sum(not VISION[i] for i in ids if i not in reviews)}")
c = np.array(confs)
for t in (0.3, 0.5, 0.7):
    print(f"  teacher confidence < {t}: {(c < t).sum():>6} images ({(c < t).mean():.1%})")
