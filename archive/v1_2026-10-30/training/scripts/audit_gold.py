# Blind re-check of the gold (test) labels.
# Run from a round's notebook after its setup cells:  %run -i ../scripts/audit_gold.py
#
# Step 1 (blind): each gold captcha is shown with NO label and NO model answer; type what you see
#                 (exact case). s = skip, q = stop (progress is saved, re-run to continue).
# Step 2 (resolve): only where your fresh answer differs from gold.csv, the image is shown again with
#                 both answers: 1 = keep the gold label, 2 = take your new answer, or type a third answer.
# Then data/gold.csv is rewritten with the decisions (the original is kept as gold_before_audit.csv).
# Model predictions are never shown, so the corrected gold stays an honest test.
import json
import re
import shutil
from datetime import datetime

AUDIT = os.path.join(os.path.dirname(GOLD_CSV), "gold_audit.json")
BACKUP = os.path.join(os.path.dirname(GOLD_CSV), "gold_before_audit.csv")
pattern = re.compile(f"[{ALPHABET}]{{{LENGTH}}}")


def show(i, big=False):
    plt.figure(figsize=(9, 2.7) if big else (7, 2.1))
    plt.imshow(imgs[row_of[i]], cmap="gray", vmin=0, vmax=255)
    plt.axis("off")
    plt.show()


def ask(prompt, allowed=()):
    while True:
        ans = input(prompt).strip()
        if ans in allowed or pattern.fullmatch(ans):
            return ans
        print(f"  need {LENGTH} characters from {ALPHABET} (exact case), try again")


audit = json.load(open(AUDIT)) if os.path.exists(AUDIT) else {}
save = lambda: json.dump(audit, open(AUDIT, "w"), indent=1)

# step 1: blind typing
todo = [i for i in GOLD if "typed" not in audit.get(i, {})]
random.Random().shuffle(todo)
print(f"step 1 (blind): {len(todo)} of {len(GOLD)} gold captchas left to type")
stopped = False
for n, i in enumerate(todo, 1):
    show(i)
    ans = ask(f"[{n}/{len(todo)}] {i}  type what you see (s=skip, q=quit): ", ("s", "q"))
    if ans == "q":
        stopped = True
        break
    if ans == "s":
        continue
    audit[i] = {"typed": ans, "time": datetime.now().isoformat(timespec="seconds")}
    save()

typed = [i for i in GOLD if "typed" in audit.get(i, {})]
if stopped or len(typed) < len(GOLD):
    print(f"\n{len(typed)}/{len(GOLD)} typed so far. Re-run this cell to continue; step 2 starts when all are typed.")
else:
    # step 2: resolve disagreements between your fresh answer and the gold label
    differ = [i for i in GOLD if audit[i]["typed"] != GOLD[i]["label"] and "final" not in audit[i]]
    agree = sum(audit[i]["typed"] == GOLD[i]["label"] for i in GOLD)
    print(f"\nstep 2: your blind answers match gold on {agree}/{len(GOLD)}; {len(differ)} to resolve")
    for n, i in enumerate(differ, 1):
        old, new = GOLD[i]["label"], audit[i]["typed"]
        show(i, big=True)
        diff = " ".join(f"@{p}: {a} vs {b}" for p, (a, b) in enumerate(zip(old, new)) if a != b)
        ans = ask(f"[{n}/{len(differ)}] {i}  1 = gold {old}   2 = new {new}   ({diff})   or type the answer: ",
                  ("1", "2"))
        audit[i]["final"] = old if ans == "1" else new if ans == "2" else ans
        save()

    # write the corrected gold.csv
    changes = [(i, GOLD[i]["label"], audit[i].get("final", GOLD[i]["label"])) for i in GOLD]
    changes = [c for c in changes if c[1] != c[2]]
    if changes:
        if not os.path.exists(BACKUP):
            shutil.copy(GOLD_CSV, BACKUP)
        for i, _, final in changes:
            GOLD[i]["label"] = final
        with open(GOLD_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(next(iter(GOLD.values())).keys()))
            w.writeheader()
            w.writerows(GOLD.values())
        print(f"\n{len(changes)} gold labels corrected (original kept as {BACKUP}):")
        for i, old, new in changes:
            print(f"  {i}: {old} -> {new}")
    else:
        print("\nno gold labels changed")

    # refresh the notebook's gold split so evaluate(..., 'gold') uses the corrected labels
    if "data" in globals() and "split_rows" in globals():
        split_rows["gold"] = [{"id": i, "label": g["label"]} for i, g in GOLD.items()]
        data["gold"] = (torch.tensor([row_of[r["id"]] for r in split_rows["gold"]]),
                        torch.tensor([encode(r["label"]) for r in split_rows["gold"]]))
        print("gold split refreshed: re-run the test cell (9) to see the corrected scores")
