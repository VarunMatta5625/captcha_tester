# data/ - Vision-era review data (historical)

Produced during the Apple Vision OCR phase (2026-09-29). The current labelled data lives in `../training/data/`.

| File | What | Trust |
|---|---|---|
| `ocr_review.json` | 122 hand reviews from the Vision-OCR tuning notebook (`reviews`, `confusions`, `extra`, `summary`). Each has `got`, `raw`, `truth`, `correct`, plus the cleanup params used. | summary: 96 of 122 exact. `truth` typed by you: trusted |
| `rounds/r00/results.csv` | First sample round, `status=checked` (you checked these). | Trusted |
| `rounds/r01/results.csv`, `r02/results.csv` | 100 captchas each, all `status=claude_unverified`. | **UNVERIFIED: labels were assigned by Claude from looking at the images. Do not use as ground truth or in gold.** |

Image ids refer to `../training/data/varun/<id>.png`.
