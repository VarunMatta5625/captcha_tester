# Project state (as of 2026-10-09)

## What works
- Extension v4.1 on `login.gitam.edu`: reads `#imgCaptcha`, fills `#txtCaptchaInput`, fires an `input` event, logs `[CAPTCHA] Pasted xxxxx (confidence …)`.
- Captcha: 150x45 px, 5 chars, case-sensitive, 37-char alphabet `2345689ABDEFGHJLMNQRTYabdefghijmnqrty` (no 0/O/1/l/I/7).
- Inference: content.js sends canvas RGBA to the service worker (background.js, ES module) -> model.js does grayscale (matches Pillow `convert("L")`), ink = `1 - gray/255`, runs layers from `model/model.json` via WASM SIMD kernels (`model.wasm`). Confidence = min softmax prob over the 5 positions; below ~0.5 is a guess. Manifest CSP needs `'wasm-unsafe-eval'`.
- CNN: 4 blocks of (conv3x3-BN-ReLU x2, maxpool2), widths 32/64/128/192; input 1x45x150 -> 2x9 map -> mean over height -> 1728 -> Linear 512 -> 5 heads of Linear 37. 1,819,929 weights (7.28 MB). Dropout 0.3 in training.

## Model history and scores
Score on **gold only** (152 hand-checked images, never trained or reviewed). Val/test only measure agreement with whichever labels trained the model.

| Model | Gold exact | Notes |
|---|---|---|
| Apple Vision + cleanup | ~76% | Original pipeline, `archive/vision_extension_2026-09-30` |
| v1 baseline (Vision labels) | 86.84% | `training/v1/models/captcha_cnn.pt` |
| v1 fine-tuned on 650 reviews | **93.42%** (char 98.68%) | `training/v1/models/captcha_cnn_ft_650.pt`; **this is what ships** (`host/captcha_cnn.pt`) |
| v2 baseline (labels from ft_650 teacher) | 94.08% (143/152) | `training/v2/models/captcha_cnn_v2.pt`; scored BEFORE gold audit |
| v2 fine-tuned | not run | `training/v2/models/captcha_cnn_v2_ft.pt` does not exist |

## Unfinished / open items (resume here)
1. **v2 not finished.** Gold audit corrected 7 gold labels (mostly 9/g, y/Y), so earlier gold numbers are not strictly comparable to post-audit ones. Re-run the test cell in `training/v2/train_v2.ipynb` to rescore ft_650 and v2 on corrected gold, then review low-confidence reads and fine-tune. Only then decide whether to ship v2.
2. Persistent confusions: 9/g, q/9, q/a, y/Y, j/i.
3. v2 beats ft_650 on gold by 1 image (143 vs 142) — within noise on 152 samples. Do not ship on that alone; a larger gold set would help.
4. **Safari port is behind.** `safari/extension-classic-sw/` is v4.1 with classic service worker (`importScripts`, no `type: module`) because Safari lacks module workers. Differs from `extension/` only in background.js, manifest.json, model.js. Any change to `extension/` must be mirrored there by hand and copied into the Xcode project's `Shared (Extension)/Resources`.
5. No git repo yet (`.gitignore` is ready; `git init` is safe). Deps in `requirements.txt` (torch, numpy, Pillow; emscripten only for WASM rebuild).
6. Verified 2026-10-09: `extension/`, `dist/captcha-paster/` and `safari/xcode-project/.../Shared (Extension)/Resources` all carry the same v4.1 model/weights; Safari resources equal `safari/extension-classic-sw/`.

## Gotchas
- `host/install.sh` derives the unpacked extension ID from the folder path; moving the project changes the ID. Generated launchers `host/cnn_host`, `host/vision_host` contain absolute paths (`/Users/varunmatta/miniconda3/bin/python3`, project path). Only the legacy/archived variants use them; the shipping extension does not.
- Notebooks `main_vision_ocr.ipynb` and `cleanup_test.ipynb` read images from `training/data/varun` (updated 2026-10-09 when the data moved here) and call `host/ocr`.
- `notebooks/train_colab.ipynb` expects `image_ftech_solver.zip` and Drive paths on Colab (`/content/...`); it is the older Colab trainer. The v1/v2 notebooks in `training/` ran locally (mps).
- `training/v2/train_v2.ipynb` uses relative paths (`../data`, `../scripts`, `../v1`); keep `data`, `scripts`, `v1`, `v2` as siblings.
- `training/v1/train_v1.ipynb` (was `model.ipynb`) cannot re-run as is: its relative inputs (`varun`, `labels.csv`, `raw_cache.npz`) are no longer beside it. Kept for its recorded outputs.
- `ocr_review.json` and `data/rounds/r01`, `r02` labels were assigned by Claude and are unverified.

## Size / regenerable
Project is about 2.7 GB larger after the 2026-10-09 merge. Regenerable, safe to delete if space or Drive sync matters:
- `training/v2/cache/all_images.npz` (820 MB, decoded image cache)
- `training/v1/labeled/` (791 MB, copies of `data/varun` renamed by label; rebuild from `labels_vision.csv`) and `rejected/` (31 MB)
- `safari/xcode-project/CAPTCHA Paster/build/` (215 MB Xcode build output)
- `dist/captcha-paster/` and the zip (rebuild with `build_zip.sh`)
Not regenerable: `training/data/varun` (126,919 raw captchas), `gold.csv`, `reviews.json`, `*.pt` models, label CSVs.

## Quick start for the next session
1. `training/v2/train_v2.ipynb`: run the test cell to rescore ft_650 vs v2 on the corrected gold (`training/data/gold.csv`).
2. If v2 wins by a clear margin: review low-confidence reads, fine-tune (`scripts/finetune.py`), then ship (steps in README) and mirror to Safari.
3. Otherwise grow the gold set before comparing models further.

## Change log
- 2026-09-30: archived Vision and Python-host variants; shipped v4.1 standalone WASM extension.
- 2026-10-09: merged leftovers from `~/Downloads/image_ftech_solver` into `training/` and `safari/`; reorganised; added this documentation.
- 2026-10-09 (later): moved remaining Jupyter junk from Downloads into `archive/downloads_leftovers_2026-10-09/`, removed the empty Downloads folder, added `requirements.txt` and `.gitignore`, verified extension/Safari/dist are in sync.
- 2026-10-09 (later): added READMEs for `data/`, `host/`, `notebooks/`, `safari/`, added `training/MODELS.md`; renamed notebooks to `main_vision_ocr.ipynb` and `cleanup_test.ipynb` (references in STATE.md and host/pipeline.py updated).
- 2026-10-09 (later): `git init`. Raw captchas (`training/data/varun/`, 822 MB, 126,919 files) are git-ignored along with other regenerable bulk; they are NOT versioned, so keep them backed up (Drive). Models (`*.pt`), labels, gold and reviews ARE committed.
