# Review a model's least confident reads, 1 captcha at a time.
#   Enter = model is right, type the true text if it's wrong, s = skip, q = quit.
# Run from a round's notebook after its setup cells:  %run -i ../scripts/review.py
# Answers are saved after every captcha to the notebook's REVIEWS file (data/reviews.json).
# Gold captchas are never shown, so they stay an honest test.
import json
import re
from datetime import datetime

REVIEW_MODEL = FT_PATH if os.path.exists(FT_PATH) else MODEL_PATH   # hunt the latest model's mistakes
N_REVIEW = 50
FOCUS = ""        # only reads containing one of these characters, e.g. "9gq" ("" = any)
POOL = 2000       # pick at random among this many least confident reads


def ask(n, total, i, read, conf):
    """Prompt until the answer is Enter, s, q or a valid captcha text."""
    prompt = (f"[{n}/{total}] {i}  model: {read}  (Vision: {VISION[i] or '-'}, conf {conf:.2f})  "
              f"Enter=right / type truth / s=skip / q=quit: ")
    pattern = re.compile(f"[{ALPHABET}]{{{LENGTH}}}")
    while True:
        ans = input(prompt).strip()
        if ans in ("", "s", "q") or pattern.fullmatch(ans):
            return ans
        print(f"  need {LENGTH} characters from {ALPHABET}, try again")


review_model, _ = load_model(REVIEW_MODEL)
reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
fresh = [i for i in ALL_IDS if i not in reviews and i not in GOLD]
reads, confs = model_reads(review_model, fresh)   # ~20 s for all images
candidates = sorted((t for t in zip(fresh, reads, confs) if not FOCUS or any(c in t[1] for c in FOCUS)),
                    key=lambda t: t[2])[:POOL]
batch = random.Random().sample(candidates, min(N_REVIEW, len(candidates)))   # fresh pick each run
print(f"reviewing {len(batch)} of the {len(candidates)} least confident reads of "
      f"{os.path.basename(REVIEW_MODEL)}; {len(reviews)} reviewed so far")

for n, (i, read, conf) in enumerate(batch, 1):
    plt.figure(figsize=(6, 1.8))
    plt.imshow(imgs[row_of[i]], cmap="gray", vmin=0, vmax=255)
    plt.axis("off")
    plt.show()
    ans = ask(n, len(batch), i, read, conf)
    if ans == "q":
        break
    if ans == "s":
        continue
    truth = ans or read
    reviews[i] = {"truth": truth, "model": read, "vision": VISION[i], "model_right": truth == read,
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
