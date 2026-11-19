# archive/

Older work, kept as it was. Nothing in here is needed to train or ship; the live project is the repository root (`../README.md`). Don't edit these, copy what you need out.

| Folder | What |
|---|---|
| `extension_5.4_2026-11-11/` | Extension 5.4 (v5 plus auto-login), from before 5.5 added the rules for when the page may press LOGIN. |
| `round4_2026-11-01/` | Round 4 (style 3), after v5 replaced it: `train_v4.ipynb`, `labels_v4.csv`, v4 (extension 5.2, gold 97.0%) and v3 (its teacher). See its `README.txt`. |
| `three_level_switch_2026-10-31/` | The experiment behind the switch to three-level cleaning (two-level vs three-level vs raw RGB), and v4 two-level, the model it replaced. See its `README.txt`. |
| `v2_2026-10-31/` | The v2 workspace (red letters on fine speckle): rounds v2/v3 (gold 98.5%), an unfinished hard-gold v4, extension 5.1 and its model v2_ft, its 100k captchas in `data/captchas.zip`, and the one style-2 captcha the site rejected (`data/site_mistakes/`). See its `README.txt`. |
| `v1_2026-10-30/` | The whole v1 project (old captchas, black letters crossed by gray lines): extension 4.1, the Safari port, the WASM kernels (`wasm/kernels.c`, `build_wasm.sh`), native hosts, Vision-era notebooks, and training rounds v1 and v2 with their data. See its `README.txt`. The old captchas are in `training/data/varun.zip`. |
| `cnn_native_host_2026-09-30/` | The extension that ran the CNN through a Python native-messaging host, from before the WASM version. |
| `vision_extension_2026-09-30/` | The original Apple Vision OCR extension (about 76% on the old captchas). |

Git-ignored in here: `v2_2026-10-31/data/captchas.zip`, `v2_2026-10-31/cache/`, `v2_2026-10-31/dist/` (the 5.1 zip), `v1_2026-10-30/training/data/varun.zip`, `v1_2026-10-30/training/v1/labeled|rejected/`, `v1_2026-10-30/training/v2/cache/`, `v1_2026-10-30/dist/`, and the Safari Xcode `build/`.
