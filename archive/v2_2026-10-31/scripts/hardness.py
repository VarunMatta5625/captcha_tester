# Every CNN in READERS reads every captcha (gold included: this is only for choosing what to look at, never a label)
# -> HARDNESS_CSV: one column per reader, plus each reader's weakest-character confidence and Vision's read.
# Run from the notebook after its setup cells:  %run -i ../scripts/hardness.py   (~20 s per model)
# pick_gold.py and review.py rank captchas by how much these readers disagree.

cols, out = [], {}
for name, path in READERS.items():
    m, _ = load_model(path)
    reads, confs = model_reads(m, list(ALL_IDS), desc=name)
    out[name], out[f"{name}_conf"] = reads, confs
    cols += [name, f"{name}_conf"]

with open(HARDNESS_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id"] + cols + ["vision"])
    for k, i in enumerate(ALL_IDS):
        w.writerow([i] + [out[c][k] if not c.endswith("_conf") else f"{out[c][k]:.3f}" for c in cols]
                   + [VISION.get(i, "")])

reads = np.array([out[n] for n in READERS])            # (readers, images)
split = (reads != reads[0]).any(0)
vision = np.array([VISION.get(i, "") for i in ALL_IDS])
print(f"wrote {HARDNESS_CSV}: {len(ALL_IDS)} captchas x {len(READERS)} readers")
print(f"  CNNs disagree: {split.sum():>6} ({split.mean():.2%})")
print(f"  CNNs agree, Vision differs: {(~split & (vision != reads[0])).sum():>6} "
      f"(Vision no read: {(~split & (vision == '')).sum()})")
print(f"  everyone agrees: {(~split & (vision == reads[0])).sum():>6}")
