# Review the model's reads, 1 captcha at a time.
#   Enter = model is right, type the true text if it's wrong, s = skip, q = quit.
# Run from the training notebook (after cells 1-6) with:  %run -i review_model.py
# Answers are saved after every captcha to model_reviews.json (read by finetune_model.py).
import json
import re
from datetime import datetime

REVIEWS = "model_reviews.json"
REVIEW_MODEL = "captcha_cnn_ft.pt"   # hunt the latest fine-tuned model's mistakes (MODEL_PATH = baseline)
N_REVIEW = 50
FOCUS = "9gq"               # only reads with one of these characters ("" = any)
SOURCE = "uncertain"        # "uncertain": the model's least confident reads, whatever Vision says
                            #   (finds the model's own mistakes, including ones Vision shares)
                            # "disagree": model and Vision disagree (mostly finds Vision's mistakes)
POOL = 2000                 # "uncertain": pick at random among this many least confident reads


def load_model(path=MODEL_PATH):
    ckpt = torch.load(path, map_location=DEVICE)
    m = CaptchaCNN(len(ckpt["alphabet"]), ckpt["length"], ckpt["widths"],
                   ckpt["config"]["dropout"]).to(DEVICE)
    m.load_state_dict(ckpt["state_dict"])
    return m.eval(), ckpt


@torch.no_grad()
def read_ids(m, ids, batch_size=2048):
    """Model reads + weakest-character confidence for a list of image ids."""
    m.eval()
    reads, confs = [], []
    for k in range(0, len(ids), batch_size):
        rows = torch.tensor([row_of[i] for i in ids[k:k + batch_size]]).to(DEVICE)
        conf, idx = m(to_input(X[rows])).softmax(-1).max(-1)
        reads += ["".join(ALPHABET[i] for i in p) for p in idx.cpu().tolist()]
        confs += conf.min(-1).values.cpu().tolist()
    return reads, confs


def ask(n, total, r, read, conf):
    """Prompt until the answer is Enter, s, q or a valid captcha text."""
    prompt = (f"[{n}/{total}] {r['id']}  model: {read}  "
              f"(Vision: {r['vision_label']}, conf {conf:.2f})  "
              f"Enter=right / type truth / s=skip / q=quit: ")
    pattern = re.compile(f"[{ALPHABET}]{{{LENGTH}}}")
    while True:
        ans = input(prompt).strip()
        if ans in ("", "s", "q") or pattern.fullmatch(ans):
            return ans
        print(f"  need {LENGTH} characters from {ALPHABET}, try again")


def focused(read, vision_label):
    return not FOCUS or any(c in read + vision_label for c in FOCUS)


review_model, _ = load_model(REVIEW_MODEL)
reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}
gold_ids = {r["id"] for r in gold}   # never reviewed here, stays the honest test
fresh = lambda i: i not in reviews and i not in gold_ids

if SOURCE == "uncertain":
    # v1 labels.csv: label is Vision's; labels_v2.csv keeps Vision's in vision_label
    rows = [{"id": r["id"], "vision_label": r.get("vision_label", r["label"])}
            for r in auto if fresh(r["id"])]
    reads, confs = read_ids(review_model, [r["id"] for r in rows])   # ~20 s for all images
    candidates = sorted((t for t in zip(rows, reads, confs) if focused(t[1], t[0]["vision_label"])),
                        key=lambda t: t[2])[:POOL]
else:
    with open("review_queue.csv") as f:
        rows = [r for r in csv.DictReader(f) if fresh(r["id"])]
    reads, confs = read_ids(review_model, [r["id"] for r in rows])
    candidates = [t for t in zip(rows, reads, confs) if focused(t[1], t[0]["vision_label"])]
batch = random.Random().sample(candidates, min(N_REVIEW, len(candidates)))   # fresh pick each run
print(f"{SOURCE}: {len(candidates)} candidates, reviewing {len(batch)}; {len(reviews)} reviewed so far")

for n, (r, read, conf) in enumerate(batch, 1):
    plt.figure(figsize=(6, 1.8))
    plt.imshow(imgs[row_of[r["id"]]], cmap="gray", vmin=0, vmax=255)
    plt.axis("off")
    plt.show()
    ans = ask(n, len(batch), r, read, conf)
    if ans == "q":
        break
    if ans == "s":
        continue
    truth = ans or read
    reviews[r["id"]] = {
        "truth": truth, "model": read, "vision": r["vision_label"],
        "model_right": truth == read, "confidence": conf, "source": SOURCE,
        "time": datetime.now().isoformat(timespec="seconds"),
    }
    if truth != read:
        diffs = [f"{t} -> {m} @{p}" for p, (t, m) in enumerate(zip(truth, read)) if t != m]
        print("  model wrong:", ", ".join(diffs))
    with open(REVIEWS, "w") as f:   # saved after every answer, so quitting loses nothing
        json.dump(reviews, f, indent=1)

wrong = [v for v in reviews.values() if not v["model_right"]]
print(f"\n{len(reviews)} reviewed in total: model right {len(reviews) - len(wrong)}, wrong {len(wrong)}")
pairs = Counter((t, m) for v in wrong for t, m in zip(v["truth"], v["model"]) if t != m)
print("model confusions (true -> model):", pairs.most_common(10))
