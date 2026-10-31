# Gold (test) set: N_GOLD random captchas that are never trained on, relabeled or reviewed.
# Run from the notebook after its setup cells:  %run -i ../scripts/audit_gold.py
#
# First run: picks the captchas and pre-labels them -> data/gold.csv (id, label, model, vision, checked).
#   label = the teacher model's read; Vision's read is kept beside it; checked = "" until you confirm it.
# Every run: shows the unchecked rows, the ones where model and Vision disagree first.
#   Enter = label is right, type the truth if not (exact case), s = skip, q = stop.
#   Saved after every answer, so stop any time and re-run to continue.
# Until every row is checked, gold scores are provisional: pre-labels come from the teacher, so they flatter it.
import re
from datetime import datetime

N_GOLD = 200
pattern = re.compile(f"[A-Za-z0-9]{{{LENGTH}}}")   # any letter/digit, so new characters can show up


def save_gold():
    with open(GOLD_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "label", "model", "vision", "checked"])
        w.writeheader()
        w.writerows(GOLD.values())


if not GOLD:
    ids = sorted(random.Random(SEED).sample(list(ALL_IDS), N_GOLD), key=int)
    teacher, _ = load_model(TEACHER)
    reads, _ = model_reads(teacher, ids)
    missing = [i for i in ids if i not in VISION]   # label_vision.py not finished: read these now
    for i, raw in zip(missing, prep.vision_reads([imgs[row_of[i]] for i in missing])):
        VISION[i] = prep.decode(raw)
    GOLD.update((i, {"id": i, "label": r, "model": r, "vision": VISION[i], "checked": ""})
                for i, r in zip(ids, reads))
    save_gold()
    agree = sum(g["model"] == g["vision"] for g in GOLD.values())
    print(f"built {GOLD_CSV}: {N_GOLD} captchas pre-labeled by {os.path.basename(TEACHER)}; "
          f"Vision agrees on {agree}")

todo = sorted((i for i, g in GOLD.items() if not g["checked"]),
              key=lambda i: GOLD[i]["model"] == GOLD[i]["vision"])   # disagreements first
print(f"{len(GOLD) - len(todo)}/{len(GOLD)} gold checked, {len(todo)} to go")
changed = []
for n, i in enumerate(todo, 1):
    g = GOLD[i]
    show(i)
    prompt = (f"[{n}/{len(todo)}] {i}  label: {g['label']}  (Vision: {g['vision'] or '-'})  "
              f"Enter=right / type truth / s=skip / q=quit: ")
    try:
        while (ans := input(prompt).strip()) not in ("", "s", "q") and not pattern.fullmatch(ans):
            print(f"  need {LENGTH} letters/digits (exact case), try again")
    except EOFError:   # no keyboard (e.g. run as a script): just build
        break
    if ans == "q":
        break
    if ans == "s":
        continue
    if ans and ans != g["label"]:
        changed.append((i, g["label"], ans))
        g["label"] = ans
    g["checked"] = datetime.now().isoformat(timespec="seconds")
    save_gold()

if changed:
    print(f"\n{len(changed)} labels corrected:", ", ".join(f"{i}: {a} -> {b}" for i, a, b in changed))
outside = Counter(c for g in GOLD.values() for c in g["label"] if c not in ALPHABET)
if outside:
    print(f"characters outside the model's alphabet in gold: {dict(outside)} (the model can't output these; "
          f"the heads need more classes)")
print(f"{sum(bool(g['checked']) for g in GOLD.values())}/{len(GOLD)} gold checked")

# refresh the notebook's gold split so evaluate(..., 'gold') uses the corrected labels
if "data" in globals() and "split_rows" in globals():
    split_rows["gold"] = gold_rows()
    data["gold"] = (torch.tensor([row_of[r["id"]] for r in split_rows["gold"]]),
                    torch.tensor([encode(r["label"]) for r in split_rows["gold"]]))
    print("gold split refreshed: re-run the test cell to see the new scores")
