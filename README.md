# captcha_tester

Chrome extension ("Instant CAPTCHA Paster") that reads the 5-character login captcha on `login.gitam.edu` with a
small CNN running inside the extension (WebAssembly, no Python, no native host), plus the workspace that trains it.

Read this file first when resuming work. Older history is in `archive/` (see `archive/README.md`).

## Status (2026-10-31)

Captcha styles so far (all 150x45, 5 characters, same 37-character alphabet):

1. Black letters crossed by gray lines: v1, frozen in `archive/v1_2026-10-30/`.
2. Red letters on fine gray speckle (2026-10-30): v2/v3, frozen in `archive/v2_2026-10-31/` (best gold 98.5%).
3. **Now** (since 2026-10-31, between 03:02 and 08:04 UTC): same red letters in a **bolder font** with **large soft gray
   blobs** drawn over them. Letters-only cleaning (`prep.ink`) leaves holes where blobs cover a letter, so since
   2026-10-31 the model reads **three levels** (`prep.clean`: letters 0, blobs 128, paper 255; +1.5 points on gold in a
   controlled test). The new **J** has no top bar:
   every old model reads it as **3** (v3 outputs J for 0.1% of characters, ~2.7% expected). Other weak pairs: B/8, y/Y,
   g/9, a/e. Extension 5.1 (v2_ft) failed on it; **extension 5.2 ships v4** (three-level), which reads all 8 style-3
   captchas the site rejected from 5.1.

Round v4 (`notebooks/train_v4.ipynb`): 100k style-3 captchas, 200 gold checked (2 labels fixed after a recheck).
Gold scores below use the corrected gold. Site = the 8 style-3 captchas the site rejected from 5.1
(`data/site_mistakes/`).

| Model (`models/`) | Trained on | Gold (style 3 unless noted) |
|---|---|---|
| `captcha_cnn_v3.pt` | style 2 (see archive) | 86.0%, 1/8 site; teacher for v4 |
| `captcha_cnn_v4.pt` | v3 + Vision agree and Vision's J fixes (57k), from v3's weights, **three-level** (`prep.clean`) | **97.0%**, 8/8 site; JS == PyTorch on all 208; **ships in extension 5.2** |
| `captcha_cnn_v4_ft.pt` | not trained: v4 + reviews (optional; remaining misses are mostly 6 read as 5) | |

Archived for comparison: v2_ft (extension 5.1; style 3 gold 87.5%, 0/8 site) in `archive/v2_2026-10-31/models/`,
v4 two-level (same labels and settings as v4, letters-only input; 94.5%, 6/8 site) and the input-variant experiment
in `archive/three_level_switch_2026-10-31/`.

## Layout

| Path | What |
|---|---|
| `extension/` | Chrome/Edge/Brave extension v5.2 (MV3). Load unpacked from here. See `extension/README.txt`. Saves captchas the site rejects (below). |
| `export_model.py` | Checkpoint -> `extension/model/{model.json,weights.bin}` (BatchNorm folded). Default: `models/captcha_cnn_v4.pt`. Writes the checkpoint's `levels` into `model.json`. |
| `build_zip.sh` | `extension/` -> `dist/captcha-paster-<version>.zip` (git-ignored, regenerable). `dist/captcha-paster/` = the unzipped current version. |
| `notebooks/train_v4.ipynb` | Round 4 (style 3): gold check, relabel (v3 + Vision agree, or Vision's J where v3 says 3), train three-level from v3 weights, review, fine-tune. Template for new rounds (style-2 rounds are in the archive). |
| `scripts/prep.py` | Shared by notebooks and scripts: reads captchas from the zip (`<id>.png`, any folder inside), `clean()` three-level image the CNN reads, `ink()` letters only (Vision, two-level models), Apple Vision helpers. |
| `scripts/label_vision.py` | Terminal, from the project root: Vision reads every captcha -> `data/labels_vision.csv` (~8 min, resumable). |
| `scripts/audit_gold.py` | Builds + pre-labels the gold set (first run), then lets you check it (Enter / type correction). |
| `scripts/relabel.py` | Notebook's `TEACHER` reads every non-gold captcha -> labels csv (`agree` / `vision_fix` / `disagree` / `review`) with model read, confidence, Vision read. `VISION_FIXES` = character pairs where Vision's read wins (now 3->J). |
| `scripts/review.py` | Type-in review, 50 per run: model-vs-Vision disagreements first, then least confident. `FOCUS` filters by characters. |
| `scripts/finetune.py` | Fine-tunes `MODEL_PATH` on all reviews (+ 5,000 anchors) -> `FT_PATH`. Always restarts from the baseline. |
| `data/captchas.zip` | **The captchas of the current style** (`<id>.png`, numeric ids, stored uncompressed). Git-ignored, not regenerable: back it up. Style 3: 100,000 captchas (787 MB). |
| `data/gold.csv` | 200 hand-checked test captchas (`label`, pre-label `model`, `vision`, `checked` time). Never trained on. |
| `data/reviews.json` | Your typed answers: the only human labels besides gold. Shared by all rounds of one captcha style. None yet for style 3. |
| `data/site_mistakes/` | Style-3 captchas the live site rejected (saved by the extension), with `labels.csv` (truth read from the image, not hand-checked). Hard cases for the next round; not gold. |
| `data/labels_vision.csv` | Apple Vision's read of every captcha (`vision` = valid 5-char read or ""; `raw`). |
| `data/labels_v4.csv` | Training labels written by round 4's relabel cell. |
| `tools/ocr` | Apple Vision OCR binary (`tools/ocr.swift`). macOS only. |
| `tools/check_extension.py` | Before shipping: runs a checkpoint through the extension's own `model.js` + `model.wasm` in Node and PyTorch on gold + `data/site_mistakes/`; every read must match. |
| `cache/` | Decoded-image cache (`clean_images.npz`, keyed by the zip's size and time) and logs. Git-ignored, rebuilt automatically. |

## Data: zipped, no loose PNGs

Each captcha style's images live in one zip; code reads it directly via `prep.captcha_ids()` /
`prep.open_captcha(id)`, nothing needs unzipping. Ids are the numeric file names, so **ids repeat across styles**:
labels, gold and reviews belong to their zip and never move between workspaces.

- `data/captchas.zip`: style 3 (the current one). Make it from the downloaded folder, stored uncompressed:
  `zip -0 -q -r data/captchas.zip "<folder>"` (any folder name inside works; add more later with `zip -0 -q -r -u`).
  Verify, then delete the loose PNGs.
- `archive/v2_2026-10-31/data/captchas.zip`: style 2, 100,000 captchas (376 MB).
- `archive/v1_2026-10-30/training/data/varun.zip`: style 1, 126,919 captchas (545 MB). Archived v1 code expects a
  `varun/` folder: `cd archive/v1_2026-10-30/training/data && unzip -q varun.zip` before running it.

All zips are git-ignored. Keep them backed up (Drive): every label and model refers to these images by id.

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

**Round 4** (done, ships in 5.2): `data/captchas.zip` from the download, `scripts/label_vision.py`, then
`notebooks/train_v4.ipynb` sections 1–11 (gold check, relabel, train three-level from v3, test). Next options: the
review loop with `FOCUS = "5"` (6 read as 5 is the main miss), or a v5 round with v4 as `TEACHER`; the archived
experiment got 97–98% on gold training three-level from scratch on v4's own reads with confidence >= 0.7.

**New captcha style**: archive the workspace like `archive/v2_2026-10-31/` (data, round notebooks, cache; ids will
clash with the new set), put the PNGs in `data/captchas.zip`, check `prep.clean` still separates letters, blobs
and paper (section 7 preview), run `scripts/label_vision.py`, copy the latest round notebook with the best model as `TEACHER`
(it builds a new gold set in section 4), and check where the teacher and Vision disagree (relabel prints the
character pairs) before trusting either.

## Ship a model to the extension

```
python3 tools/check_extension.py models/<model>.pt   # JS == PyTorch on every gold/site captcha, else stop
python3 export_model.py models/<model>.pt   # default: models/captcha_cnn_v4.pt
# bump "version" in extension/manifest.json
./build_zip.sh                              # optional: dist/captcha-paster-<version>.zip
```

Reload the extension in chrome://extensions (the circular arrow on its card; Load unpacked again if it was loaded from
a folder that was replaced). On login.gitam.edu the console (F12) logs `[CAPTCHA] Pasted xxxxx (confidence …)`.
Update the Status table: which model ships.

## Captchas the extension got wrong

Since extension 5.1, pressing LOGIN with the model's read unchanged and getting "Invalid CAPTCHA" back saves that
captcha to `~/Downloads/captcha_mistakes/<time>_model-<read>_conf-<confidence>.png` (time UTC). Wrong-password
failures, successful logins and retyped codes save nothing. The site shows a new captcha straight away, so the right
answer is unknown: the file name only says what the model read (wrong) and how sure it was.

These are real-world misses, the most useful images for the next round. Nothing imports them yet: move them into
`data/site_mistakes/`, label them in its `labels.csv` (usually one character off; known confusions J/3, 6/5, B/8, y/Y,
a/e) before training on them, and keep them out of gold. Chrome extensions can only write under Downloads, so they
land there first. The Downloads folder was emptied when 5.2 shipped: anything new there is a 5.2 miss.

## Rules (break these and scores stop meaning anything)

- **Gold is never trained on, relabeled or reviewed.** Every script skips `GOLD` ids. Compare models on gold only;
  val/test only measure agreement with the teacher's labels.
- **Preprocessing must match**: `scripts/prep.py` `clean()` and `extension/model.js` `clean()` both make pixels with
  `r - g > 60 && r - b > 60` letters (0), other pixels with `r + g + b < 600` blobs (128), everything else 255. Change
  both or neither; re-export afterwards. Checkpoints say which cleaning they need (`levels`: 3, or missing = 2 =
  letters only: v1-v3 and the archived v4 two-level); the notebook's `load_model` and the exported `model.json` carry it, so old
  and new models both read correctly.
- **Alphabet** (`2345689ABDEFGHJLMNQRTYabdefghijmnqrty`, no 0/O/1/l/I/7) comes from the checkpoint. Gold checking
  accepts any letter/digit and warns if a new character appears; adding one means new head classes and removing the
  matching entries from `prep.LEARNED`.
- `export_model.py` only knows this architecture (4 blocks of conv-BN-ReLU x2 + maxpool, widths 32/64/128/192, mean over
  height, Linear 512, 5 heads). A different network needs export and `model.js` changes too.

## Gotchas

- Editing a `.ipynb` on disk while it is open in Jupyter: use File -> Reload Notebook from Disk (choose Revert, not
  Overwrite, if asked). The kernel keeps its state.
- `scripts/label_vision.py` uses all CPU cores via multiprocessing: run it from a terminal, not a notebook cell.
  It skips ids already in `data/labels_vision.csv`: a new captcha set needs a fresh file.
- The notebook loads `VISION` once in section 2; `relabel.py` re-reads the file itself.
- Safari port (`archive/v1_2026-10-30/safari/`) is still v4.1 for the old captchas: not updated for v2.
- `archive/v1_2026-10-30/training/v2/cache/all_images.npz` (820 MB) and `archive/v2_2026-10-31/cache/` (670 MB) are
  regenerable caches; delete if space matters.

## Change log

- 2026-09-30: v1 shipped (extension 4.1, old captchas, gold 93.42%).
- 2026-10-30: captcha style changed. Archived v1 to `archive/v1_2026-10-30/`. New workspace: red-letter mask,
  Vision labels for 100k new captchas, 200-captcha gold (checked: v1 model 91.0%). Round 2: v2 96.0%, v2_ft 98.5%
  (100 reviews). Round 3: v3 / v3_ft 98.5%. Extension 5.0 (red mask in `model.js`) ships v2_ft; JS output verified
  identical to PyTorch on all 200 gold. Captcha PNGs zipped, loose copies deleted.
- 2026-10-31: extension 5.1 (same model, v2_ft): captchas the site rejects as "Invalid CAPTCHA" are saved to
  `~/Downloads/captcha_mistakes/` for retraining (new `downloads` permission).
- 2026-10-31: captcha style 3 (bolder font, large gray blobs; new J reads as 3). Archived the style-2 workspace to
  `archive/v2_2026-10-31/` (rounds v2/v3, unfinished hard-gold v4, data, models). Set up round 4: `train_v4.ipynb`
  from v3's weights; `relabel.py` trusts Vision's J where v3 reads 3 (23/23 right in a 500-captcha sample);
  `prep` accepts any folder inside the zip; the image cache is keyed by the zip file.
- 2026-10-31: round 4 trained (gold 93.5%, two-level). Gold recheck fixed 19263 (hyJ42) and 79474 (j4rM8). An
  input-variant experiment (two-level / three-level / raw RGB, 2 seeds each) favoured three-level, so the project
  switched to it: `prep.clean` / `model.js clean()` (letters 0, blobs 128, paper 255). Checkpoints and `model.json`
  carry `levels`, so two-level models keep working. v4 retrained three-level: gold 94.5% -> 97.0% (corrected gold),
  8/8 site rejections. Extension 5.2 ships it (JS == PyTorch on 208/208). v2_ft and v4 two-level archived; the
  9 saved rejections moved out of Downloads into `data/site_mistakes/` (and the style-2 one into the style-2 archive).
