# Captcha model workspace

Training workspace for the captcha-reading CNN used by the Chrome extension. Lives in
`captcha_tester/training/`; the extension, export tools and `host/captcha_cnn.pt` are one level up.
Current status and open items: `../docs/STATE.md`.

```
data/
  varun/            126,919 raw captchas, <id>.png (never modified)
  gold.csv          152 hand-checked captchas: the TEST SET. Never relabeled, reviewed or trained on.
  reviews.json      your hand-checked model reads (650+), used as true labels / for fine-tuning
scripts/            shared by every round, run from a round's notebook with  %run -i ../scripts/<name>.py
  relabel.py        label every captcha with a model -> the round's labels csv (gold left out)
  review.py         show a model's least confident reads, you confirm or correct -> data/reviews.json
  finetune.py       fine-tune the round's baseline on all reviews
  audit_gold.py     blind re-check of gold labels (no model answers shown) -> corrected data/gold.csv
v1/                 round 1 (done; train_v1.ipynb = original training notebook, outputs only): Vision OCR labels -> baseline CNN -> fine-tuned on reviews
  labels_vision.csv every image's Vision label (gold rows hold the hand label)
  models/           captcha_cnn.pt (baseline), captcha_cnn_ft_150/350/650.pt (fine-tuned)
  labeled/, rejected/, label_images.py, label_run.log, review_queue.csv, old script versions
v2/                 round 2 (current)
  train_v2.ipynb    relabel with v1's best -> new baseline -> test -> review -> fine-tune
```

## Scores on gold (152 hand-checked captchas)

| Model | Gold exact |
|---|---|
| Apple Vision + cleanup (no training) | ~76% |
| v1 baseline, trained on Vision labels | 86.84% |
| v1 fine-tuned on 650 reviews: `v1/models/captcha_cnn_ft_650.pt` | **93.42%** (best so far, in the extension) |
| v2 baseline / v2 fine-tuned | run `v2/train_v2.ipynb` |

Val and test scores only measure agreement with whatever produced the labels. Compare models on gold only.

## Putting a better model in the extension

```
cp <model>.pt ../host/captcha_cnn.pt   # from training/
cd ..
python3 export_model.py      # writes extension/model/
./build_zip.sh               # dist/captcha-paster-<version>.zip (bump version in extension/manifest.json first)
```
Then reload the extension in chrome://extensions.

## Starting another round later (v3)

Copy `v2/train_v2.ipynb` to `v3/train_v3.ipynb` and change the paths in its first cell:
`RELABEL_MODEL` = the best model so far, `LABELS_CSV = "labels_v3.csv"`, `MODEL_PATH`/`FT_PATH` = v3 names.
Gold and reviews stay in `data/` and carry over.
