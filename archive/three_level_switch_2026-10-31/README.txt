Record of the 2026-10-31 switch from two-level to three-level image cleaning (style-3 captchas).

experiment/   Input-variant experiment, run from a scratch folder (paths in common.py point at the project; raw.npz,
              a 2 GB RGB cache of all 100k captchas, is rebuilt on first run). Labels: the first v4's (two-level)
              own reads with confidence >= 0.7 (93,185 captchas), 70/20/10 split, same for every run; trained from
              scratch, 10 epochs, 2 seeds; gold = data/gold.csv as it was before the 2-label fix.
                step1_reads.py   v4 reads everything -> reads_v4.csv, label-rule comparison on gold
                step2_train.py   one run: <binary|three|raw> <seed> [init checkpoint]
                step3_report.py  report.md (tables, confusions, per-captcha misses, site rejections)
                rescore_gold.py  the saved models on the corrected gold
              Gold (old -> corrected): binary 95.0/95.0 -> 96.0/96.0, raw 95.5/96.5 -> 96.5/97.5,
              three 97.0/96.0 -> 98.0/97.0. Binary scored highest on val but lowest on gold: it copies the
              teacher's mistakes. models/three_s0.pt (98.0% corrected gold, in_ch 1, three-level input with blobs
              = 0.5) is kept as a candidate teacher for a v5 round; the other 7 models were not kept.
models/       captcha_cnn_v4_binary.pt: v4 as first trained (two-level prep.ink input, no "levels" key), gold 94.5%
              on the corrected gold, 6/8 site rejections. The live models/captcha_cnn_v4.pt is the same recipe with
              three-level input (97.0%, 8/8).
