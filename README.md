# captcha_tester

Browser extension ("CAPTCHA Paster") that reads the 5-character login captcha on
`login.gitam.edu` with a small CNN and types it into the input box. The CNN runs inside the
extension (WebAssembly, no Python, no native host). This folder holds the extension, the
training workspace that produces the model, and legacy experiments.

Current shipped version: **4.1** (Chrome MV3). Best measured accuracy: **93.42% exact on the
152-image hand-checked gold set** (98.68% per character).

Model registry: `training/MODELS.md`. Read `docs/STATE.md` first when resuming work: it has current status, scores, known issues and next steps.

## Layout

| Path | What |
|---|---|
| `extension/` | Shipping Chrome/Edge/Brave extension (MV3, ES-module service worker). Load unpacked from here. |
| `wasm/kernels.c`, `build_wasm.sh` | WASM conv/pool/linear kernels. Rebuild only if the C changes (needs emscripten). |
| `export_model.py` | `host/captcha_cnn.pt` -> `extension/model/{model.json,weights.bin}` (BatchNorm folded). |
| `build_zip.sh` | Packages `extension/` into `dist/captcha-paster-<version>.zip`. |
| `dist/` | Build output (zip + unzipped copy of extension). Regenerable. |
| `host/` | Legacy macOS native-messaging helpers. `host/captcha_cnn.pt` is the **model checkpoint the export reads**. |
| `training/` | Model training workspace (data, labels, scripts, v1/v2 rounds, models). See `training/README.md`. |
| `safari/` | Safari port: Xcode project + classic-service-worker copy of the extension. |
| `notebooks/` | Original Apple-Vision-era notebooks, Colab trainer, test PNGs. Historical. |
| `data/` | Vision-era review data (`ocr_review.json`, `rounds/`). Historical. |
| `archive/` | Frozen 2026-09-30 snapshots (Vision extension, CNN-with-Python-host extension) and `downloads_leftovers_2026-10-09/` (junk, deletable). |
| `docs/` | Project documentation: `STATE.md` (status, next steps, gotchas). |
| `requirements.txt`, `.gitignore` | Python deps for training/export; ignore list for regenerable bulk (no git repo yet). |

## Common tasks

Install the extension: chrome://extensions, Developer mode, Load unpacked, pick `extension/`.

Ship a new model:
```
cp training/v?/models/<model>.pt host/captcha_cnn.pt
python3 export_model.py          # needs torch, numpy
# bump "version" in extension/manifest.json
./build_zip.sh
```
Then reload the extension. For Safari, also refresh the resources (see `docs/STATE.md`).

Train / improve the model: see `training/README.md` (round workflow, gold set rules).
