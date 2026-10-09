"""Label every captcha image with the extension's cleanup + Apple Vision pipeline.

    python3 label_images.py              label everything not labeled yet (safe to stop and re-run)
    python3 label_images.py --limit 200  label just the next 200 (quick trial)

Originals in varun/ are never touched; the review log and notebooks refer to
them by number. Each image is copied here instead:

    labeled/<label>_<id>.png    label read by Vision, or your hand label where one exists
    rejected/<id>.png           Vision read wasn't 5 alphabet characters
    labels_vision.csv           id, label, raw Vision text, source (human / vision / rejected)

The id stays in the name because labels repeat and macOS filenames ignore case (aB3de == AB3DE).
"""
import csv, glob, json, os, shutil, sys, time
from collections import Counter
from multiprocessing import Pool

import numpy as np
from PIL import Image

PROJECT = "/Users/varunmatta/Drive/Varun/Projects/captcha_tester"
sys.path.insert(0, os.path.join(PROJECT, "host"))
from pipeline import clean, decode, ocr_many, LOG, ROUNDS   # same code the extension runs

IMAGES = "/Users/varunmatta/Drive/Varun/Projects/captcha_tester/training/data/varun"
HERE = os.path.dirname(os.path.abspath(__file__))
LABELED = os.path.join(HERE, "labeled")
REJECTED = os.path.join(HERE, "rejected")
CSV = os.path.join(HERE, "labels_vision.csv")
CHUNK = 50   # images per Vision call


def human_labels():
    """id -> label you checked by hand (review log + 'checked' rows of the old rounds)."""
    labels = {}
    for f in glob.glob(os.path.join(ROUNDS, "r*", "results.csv")):
        with open(f) as fh:
            labels.update((r["image"], r["label"]) for r in csv.DictReader(fh) if r["status"] == "checked" and r["label"])
    with open(LOG) as fh:
        labels.update((k, r["truth"]) for k, r in json.load(fh)["reviews"].items())
    return labels

def read_chunk(ids):
    """Worker: ids -> [(id, raw Vision text)]. Unreadable images get raw None."""
    ok, cleaned, rows = [], [], []
    for i in ids:
        try:
            cleaned.append(clean(np.array(Image.open(os.path.join(IMAGES, f"{i}.png")).convert("L"))))
            ok.append(i)
        except Exception as e:
            print(f"skip {i}: {e}", file=sys.stderr)
            rows.append((i, None))
    return rows + list(zip(ok, ocr_many(cleaned) if cleaned else []))

def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    os.makedirs(LABELED, exist_ok=True)
    os.makedirs(REJECTED, exist_ok=True)

    done = set()
    if os.path.exists(CSV):
        with open(CSV) as fh:
            done = {r["id"] for r in csv.DictReader(fh)}
    todo = sorted((os.path.splitext(f)[0] for f in os.listdir(IMAGES) if f.endswith(".png")), key=int)
    todo = [i for i in todo if i not in done][:limit]
    human = human_labels()
    print(f"{len(done)} already labeled, {len(todo)} to go")

    new_file = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as fh, Pool() as pool:
        out = csv.writer(fh)
        if new_file:
            out.writerow(["id", "label", "raw", "source"])
        chunks = [todo[k:k + CHUNK] for k in range(0, len(todo), CHUNK)]
        count, start = Counter(), time.time()
        for rows in pool.imap_unordered(read_chunk, chunks):
            for i, raw in rows:
                if raw is None:
                    continue   # unreadable: left out of the CSV so a re-run retries it
                label = human.get(i) or decode(raw)
                source = "human" if i in human else "vision" if label else "rejected"
                name = os.path.join(LABELED, f"{label}_{i}.png") if label else os.path.join(REJECTED, f"{i}.png")
                shutil.copy2(os.path.join(IMAGES, f"{i}.png"), name)
                out.writerow([i, label, raw, source])
                count[source] += 1
            fh.flush()   # rows only after their copies exist, so a stop mid-run loses nothing
            n = sum(count.values())
            rate = n / (time.time() - start)
            print(f"{n}/{len(todo)}  {dict(count)}  {rate:.1f} img/s  ~{(len(todo) - n) / rate / 60:.0f} min left", flush=True)

if __name__ == "__main__":
    main()
