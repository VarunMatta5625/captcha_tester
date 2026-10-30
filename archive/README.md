# archive/

Frozen snapshots. Nothing here is needed to train or ship; the live project is the repository root (`../README.md`).
Do not edit snapshots: copy what you need out instead.

| Folder | What |
|---|---|
| `v1_2026-10-30/` | The whole v1 project (old captchas: black letters crossed by gray lines): extension 4.1, Safari port, WASM kernels (`wasm/kernels.c`, `build_wasm.sh`), native hosts, Vision-era notebooks, training rounds v1 and v2 with their data. See its `README.txt`. Old captchas are in `training/data/varun.zip`. |
| `cnn_native_host_2026-09-30/` | Extension that ran the CNN through a Python native-messaging host (before WASM). |
| `vision_extension_2026-09-30/` | The original Apple Vision OCR extension (~76% on old captchas). |
| `downloads_leftovers_2026-10-09/` | Jupyter leftovers moved from ~/Downloads. Junk, deletable. |

Git-ignored inside: `v1_2026-10-30/training/data/varun.zip`, `v1_2026-10-30/training/v1/labeled|rejected/`,
`v1_2026-10-30/training/v2/cache/`, `v1_2026-10-30/dist/`, the Safari Xcode `build/`.
