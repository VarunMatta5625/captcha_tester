# Label every captcha with the teacher model and compare with Apple Vision -> LABELS_CSV.
# Run from the notebook after its setup and gold cells:  %run -i ../scripts/relabel.py
# Needs Vision's reads of every captcha (python3 scripts/label_vision.py, from the project root).
#
#   gold captchas      left out entirely: they live only in data/gold.csv, the test set
#   your reviews       your typed answer, source "review"          -> training
#   model == Vision    that read, source "agree"                   -> training / val / test
#   model != Vision    Vision's read, source "vision_fix", where every differing character is in VISION_FIXES
#                      (the teacher can't read a glyph the new font changed, Vision can)  -> training / val / test
#                      otherwise the model's read, source "disagree" -> not trained on; review.py shows these first
import json

# (teacher's char, Vision's char) pairs where Vision is trusted. 2026-10-31 font: v3 reads the new J (no top bar)
# as 3; all 23 such Vision reads in a 500-captcha sample were right. Empty it once the teacher reads J.
VISION_FIXES = {("3", "J")}

reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
assert not set(GOLD) & set(reviews), "a gold captcha is in the reviews"
with open(VISION_LABELS) as f:   # re-read: label_vision.py may have finished after the notebook loaded it
    VISION = {r["id"]: r["vision"] for r in csv.DictReader(f)}
missing = [i for i in ALL_IDS if i not in VISION]
assert not missing, f"{len(missing)} captchas have no Vision read yet: run python3 scripts/label_vision.py"

teacher, _ = load_model(TEACHER)
ids = [i for i in ALL_IDS if i not in GOLD]
reads, confs = model_reads(teacher, ids)

count, pairs = Counter(), Counter()   # pairs: (teacher, Vision) characters in disagreements
with open(LABELS_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "source", "confidence", "model", "vision"])
    for i, read, conf in zip(ids, reads, confs):
        diff = [(a, b) for a, b in zip(read, VISION[i]) if a != b]
        if i in reviews:
            label, source = reviews[i]["truth"], "review"
        elif not diff and VISION[i]:
            label, source = read, "agree"
        elif VISION[i] and all(d in VISION_FIXES for d in diff):
            label, source = VISION[i], "vision_fix"
        else:
            label, source = read, "disagree"
            pairs.update(diff)
        count[source] += 1
        w.writerow([i, label, source, f"{conf:.3f}", read, VISION[i]])

print(f"wrote {LABELS_CSV}: {count['agree']} agree with Vision, {count['vision_fix']} Vision fixes {sorted(VISION_FIXES)}, "
      f"{count['disagree']} disagree, {count['review']} your reviews; gold's {len(GOLD)} left out "
      f"(the notebook's splits cell picks what trains)")
print("  disagreeing characters (teacher -> Vision):", pairs.most_common(12))
print(f"  of the disagreements, Vision gave no valid read on {sum(not VISION[i] for i in ids if i not in reviews)}")
c = np.array(confs)
for t in (0.3, 0.5, 0.7):
    print(f"  teacher confidence < {t}: {(c < t).sum():>6} images ({(c < t).mean():.1%})")
