"""Read every captcha in data/captchas.zip with Apple Vision -> data/labels_vision.csv.

    python3 scripts/label_vision.py              read everything not read yet (safe to stop and re-run)
    python3 scripts/label_vision.py --limit 500  just the next 500 (quick trial)

Columns: id, vision (the read if it is exactly 5 alphabet characters, else ""), raw (what Vision said).
Run from a terminal, not the notebook: it uses one process per CPU core.
"""
import csv, os, sys, time
from collections import Counter
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prep import ROOT, captcha_ids, decode, ink, open_captcha, vision_reads

CSV = os.path.join(ROOT, "data", "labels_vision.csv")
CHUNK = 50   # images per Vision call


def read_chunk(ids):
    return list(zip(ids, vision_reads([ink(open_captcha(i)) for i in ids])))


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    done = set()
    if os.path.exists(CSV):
        with open(CSV) as fh:
            done = {r["id"] for r in csv.DictReader(fh)}
    todo = [i for i in captcha_ids() if i not in done][:limit]
    print(f"{len(done)} already read, {len(todo)} to go", flush=True)

    new_file = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as fh, Pool() as pool:
        out = csv.writer(fh)
        if new_file:
            out.writerow(["id", "vision", "raw"])
        chunks = [todo[k:k + CHUNK] for k in range(0, len(todo), CHUNK)]
        count, start = Counter(), time.time()
        for n_chunk, rows in enumerate(pool.imap_unordered(read_chunk, chunks), 1):
            for i, raw in rows:
                label = decode(raw)
                out.writerow([i, label, raw])
                count["valid" if label else "invalid"] += 1
            fh.flush()
            if n_chunk % 20 == 0 or n_chunk == len(chunks):
                n = sum(count.values())
                rate = n / (time.time() - start)
                print(f"{n}/{len(todo)}  {dict(count)}  {rate:.0f} img/s  ~{(len(todo) - n) / rate / 60:.0f} min left",
                      flush=True)


if __name__ == "__main__":
    main()
