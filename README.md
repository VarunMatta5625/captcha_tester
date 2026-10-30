# captcha_tester

Chrome extension ("Instant CAPTCHA Paster") that reads the 5-character login captcha on `login.gitam.edu` with a
small CNN running inside the extension (WebAssembly, no Python, no native host), plus the workspace that trains it.

Read this file first when resuming work. Older history is in `archive/` (see `archive/README.md`).

## Status (2026-10-30)

In Oct 2026 the captcha changed from black letters crossed by gray lines to **red letters on gray speckle**
(same 150x45 size, 5 characters, font, 37-character alphabet). v1 (old captchas) is frozen in `archive/v1_2026-10-30/`.

| Model (`models/`) | Trained on | Gold exact (200) |
|---|---|---|
| `captcha_cnn_ft_650.pt` | v1's best, old captchas only (teacher for v2) | 91.0% |
| `captcha_cnn_v2.pt` | `data/labels.csv` rows where v1 model and Apple Vision agree (66k), from v1 weights | 96.0% |
| `captcha_cnn_v2_ft.pt` | v2 + fine-tuned on 100 reviews | **98.5%**, **ships in extension 5.0** |
| `captcha_cnn_v3.pt` | `data/labels_v3.csv`: every v2_ft read with confidence >= 0.5 (69k) + reviews, from scratch | 98.5% |
| `captcha_cnn_v3_ft.pt` | v3 + fine-tuned on 100 reviews | 98.5% |

v2_ft and v3 tie: at 3 misses in 200, gold can no longer separate models. Remaining gold misses: A/4, a/e, g/9.

## Layout

| Path | What |
|---|---|
| `extension/` | Chrome/Edge/Brave extension v5.0 (MV3). Load unpacked from here. See `extension/README.txt`. |
| `export_model.py` | Checkpoint -> `extension/model/{model.json,weights.bin}` (BatchNorm folded). Default: `models/captcha_cnn_v2_ft.pt`. |
| `build_zip.sh` | `extension/` -> `dist/captcha-paster-<version>.zip` (git-ignored, regenerable). |
| `notebooks/train_v2.ipynb` | Round 2: gold check, relabel (v1 model + Vision agree), train from v1 weights, review, fine-tune. |
| `notebooks/train_v3.ipynb` | Round 3: relabel with v2_ft (confidence filter), train from scratch, fine-tune. Template for new rounds. |
| `scripts/prep.py` | Shared by notebooks and scripts: reads captchas from the zip, `ink()` red-letter mask, Apple Vision helpers. |
| `scripts/label_vision.py` | Terminal, from the project root: Vision reads every captcha -> `data/labels_vision.csv` (~8 min, resumable). |
| `scripts/audit_gold.py` | Builds + pre-labels the gold set (first run), then lets you check it (Enter / type correction). |
| `scripts/relabel.py` | Notebook's `TEACHER` reads every non-gold captcha -> labels csv with model read, confidence, Vision read. |
| `scripts/review.py` | Type-in review, 50 per run: model-vs-Vision disagreements first, then least confident. `FOCUS` filters by characters. |
| `scripts/finetune.py` | Fine-tunes `MODEL_PATH` on all reviews (+ 5,000 anchors) -> `FT_PATH`. Always restarts from the baseline. |
| `data/captchas.zip` | **The 100,000 captchas** (`captchas/<id>.png`, stored uncompressed). Git-ignored, not regenerable: back it up. |
| `data/gold.csv` | 200 hand-checked test captchas (`label`, pre-label `model`, `vision`, `checked` time). Never trained on. |
| `data/reviews.json` | Your typed answers: the only human labels besides gold. Shared by all rounds. |
| `data/labels_vision.csv` | Apple Vision's read of every captcha (`vision` = valid 5-char read or ""; `raw`). |
| `data/labels.csv`, `data/labels_v3.csv` | Training labels written by round 2 / round 3 relabel cells. |
| `tools/ocr` | Apple Vision OCR binary (`tools/ocr.swift`). macOS only. |
| `cache/` | Decoded-image cache (`ink_images.npz`) and logs. Git-ignored, rebuilt automatically. |

## Data: zipped, no loose PNGs

On 2026-10-30 both captcha sets were zipped and the loose PNGs deleted after every file was verified against its zip
(CRC32 + size):

- `data/captchas.zip`: 100,000 new captchas (376 MB). Code reads it directly via `prep.captcha_ids()` /
  `prep.open_captcha(id)`; nothing needs unzipping.
- `archive/v1_2026-10-30/training/data/varun.zip`: 126,919 old captchas (545 MB). Archived v1 code expects a
  `varun/` folder: `cd archive/v1_2026-10-30/training/data && unzip -q varun.zip` before running it.

Both zips are git-ignored. Keep them backed up (Drive): every label and model refers to these images by id.

## Workflow

Setup: `pip install -r requirements.txt` (torch, numpy, Pillow, jupyter, matplotlib, tqdm), then
`cd notebooks && jupyter lab`. Notebooks use paths relative to `notebooks/` and run on `mps` (Apple Silicon) or CPU.

**Review loop** (any round's notebook, after its setup cells 1–3 and splits/training cells):
section 12 review 50 -> 13 fine-tune -> 14 what changed on gold. Repeat while gold improves.
Then ship (below).

**New round** (relabel with the best model, retrain):
1. Copy the latest `notebooks/train_vN.ipynb` to `train_vN+1.ipynb`.
2. In its setup cell set `TEACHER` = best model so far, `LABELS_CSV = "../data/labels_vN+1.csv"`,
   `MODEL_PATH`/`FT_PATH` = `captcha_cnn_vN+1.pt` / `captcha_cnn_vN+1_ft.pt`. Update the intro markdown.
3. Run top to bottom, skipping the gold-check and review cells (they wait for keyboard input).
4. Compare on gold in section 10 against the teacher. Add a row to the Status table above.

**New captcha style**: put the PNGs in a zip like `data/captchas.zip`, check `prep.ink` still isolates the letters
(look at the section 7 preview), rebuild the gold set (move `data/gold.csv` aside, run section 4), run
`scripts/label_vision.py`, then a new round from the best model.

## Ship a model to the extension

```
python3 export_model.py models/<model>.pt   # default: models/captcha_cnn_v2_ft.pt
# bump "version" in extension/manifest.json
./build_zip.sh                              # optional: dist/captcha-paster-<version>.zip
```
Reload the extension in chrome://extensions. On login.gitam.edu the console (F12) logs
`[CAPTCHA] Pasted xxxxx (confidence …)`. Update the Status table: which model ships.

## Rules (break these and scores stop meaning anything)

- **Gold is never trained on, relabeled or reviewed.** Every script skips `GOLD` ids. Compare models on gold only;
  val/test only measure agreement with the teacher's labels.
- **Preprocessing must match**: `scripts/prep.py` `ink()` and `extension/model.js` `toInk()` both keep pixels with
  `r - g > 60 && r - b > 60` as letters (0), everything else 255. Change both or neither; re-export afterwards.
- **Alphabet** (`2345689ABDEFGHJLMNQRTYabdefghijmnqrty`, no 0/O/1/l/I/7) comes from the checkpoint. Gold checking
  accepts any letter/digit and warns if a new character appears; adding one means new head classes and removing the
  matching entries from `prep.LEARNED`.
- `export_model.py` only knows this architecture (4 blocks of conv-BN-ReLU x2 + maxpool, widths 32/64/128/192, mean over
  height, Linear 512, 5 heads). A different network needs export and `model.js` changes too.

## Gotchas

- Editing a `.ipynb` on disk while it is open in Jupyter: use File -> Reload Notebook from Disk (choose Revert, not
  Overwrite, if asked). The kernel keeps its state.
- `scripts/label_vision.py` uses all CPU cores via multiprocessing: run it from a terminal, not a notebook cell.
- The notebook loads `VISION` once in section 2; `relabel.py` re-reads the file itself.
- Safari port (`archive/v1_2026-10-30/safari/`) is still v4.1 for the old captchas: not updated for v2.
- `archive/v1_2026-10-30/training/v2/cache/all_images.npz` (820 MB) is a regenerable cache; delete if space matters.

## Change log

- 2026-09-30: v1 shipped (extension 4.1, old captchas, gold 93.42%).
- 2026-10-30: captcha style changed. Archived v1 to `archive/v1_2026-10-30/`. New workspace: red-letter mask,
  Vision labels for 100k new captchas, 200-captcha gold (checked: v1 model 91.0%). Round 2: v2 96.0%, v2_ft 98.5%
  (100 reviews). Round 3: v3 / v3_ft 98.5%. Extension 5.0 (red mask in `model.js`) ships v2_ft; JS output verified
  identical to PyTorch on all 200 gold. Captcha PNGs zipped, loose copies deleted.
