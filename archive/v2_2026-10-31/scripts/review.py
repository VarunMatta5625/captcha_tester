# Review the captchas a model most likely gets wrong, 1 at a time: first where it disagrees with Vision,
# then its least confident reads.
#   Enter = model is right, type the true text if it's wrong, s = skip, q = quit.
# Run from the notebook after its setup cells:  %run -i ../scripts/review.py
# Answers are saved after every captcha to the notebook's REVIEWS file (data/reviews.json).
# Gold captchas are never shown, so they stay an honest test.
import json
import re
from datetime import datetime

# hunt the latest model's mistakes (the teacher until a baseline exists)
REVIEW_MODEL = next(p for p in (FT_PATH, MODEL_PATH, TEACHER) if os.path.exists(p))
N_REVIEW = 50
FOCUS = "ij9gyY56ae"   # only reads containing one of these characters ("" = any): v2 gold confusions
POOL = 2000       # pick at random among this many most doubtful reads (disagreements first, then confidence)


def ask(n, total, i, read, conf):
    """Prompt until the answer is Enter, s, q or a valid captcha text."""
    prompt = (f"[{n}/{total}] {i}  model: {read}  (Vision: {VISION.get(i) or '-'}, conf {conf:.2f})  "
              f"Enter=right / type truth / s=skip / q=quit: ")
    pattern = re.compile(f"[{ALPHABET}]{{{LENGTH}}}")
    while True:
        ans = input(prompt).strip()
        if ans in ("", "s", "q") or pattern.fullmatch(ans):
            return ans
        print(f"  need {LENGTH} characters from {ALPHABET} (skip with s if it has others), try again")


review_model, _ = load_model(REVIEW_MODEL)
reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
fresh = [i for i in ALL_IDS if i not in reviews and i not in GOLD]
reads, confs = model_reads(review_model, fresh)   # ~20 s for all images
candidates = sorted((t for t in zip(fresh, reads, confs) if not FOCUS or any(c in t[1] for c in FOCUS)),
                    key=lambda t: (t[1] == VISION.get(t[0]), t[2]))[:POOL]
batch = random.Random().sample(candidates, min(N_REVIEW, len(candidates)))   # fresh pick each run
n_dis = sum(r != VISION.get(i) for i, r, _ in candidates)
print(f"reviewing {len(batch)} of the {len(candidates)} most doubtful reads of {os.path.basename(REVIEW_MODEL)} "
      f"({n_dis} of them disagree with Vision); {len(reviews)} reviewed so far")

for n, (i, read, conf) in enumerate(batch, 1):
    show(i)
    ans = ask(n, len(batch), i, read, conf)
    if ans == "q":
        break
    if ans == "s":
        continue
    truth = ans or read
    reviews[i] = {"truth": truth, "model": read, "vision": VISION.get(i, ""), "model_right": truth == read,
                  "confidence": conf, "reviewed_with": os.path.basename(REVIEW_MODEL),
                  "time": datetime.now().isoformat(timespec="seconds")}
    if truth != read:
        diffs = [f"{t} -> {m} @{p}" for p, (t, m) in enumerate(zip(truth, read)) if t != m]
        print("  model wrong:", ", ".join(diffs))
    with open(REVIEWS, "w") as f:   # saved after every answer, so quitting loses nothing
        json.dump(reviews, f, indent=1)

this_round = [reviews[i] for i, _, _ in batch if i in reviews]
wrong = [v for v in this_round if not v["model_right"]]
print(f"\nthis run: {len(this_round)} reviewed, model wrong on {len(wrong)}; {len(reviews)} reviews in total")
pairs = Counter((t, m) for v in wrong for t, m in zip(v["truth"], v["model"]) if t != m)
print("this run's confusions (true -> model):", pairs.most_common(10))
