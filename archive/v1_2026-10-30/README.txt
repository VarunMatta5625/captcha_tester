Frozen 2026-10-30 snapshot of the whole v1 project (old-style captchas: black letters crossed by gray lines;
shipped extension v4.1), archived when the site switched to red letters on gray speckle and work moved to v2.

Everything is exactly where it was at the project root, so paths inside resolve relative to this folder:
extension/, safari/, host/, wasm/, export_model.py, build_wasm.sh, build_zip.sh, dist/, docs/STATE.md,
notebooks/ (Vision-era + Colab), data/ (Vision-era review data), training/ (data, scripts, v1, v2 rounds,
MODELS.md, README.md). training/v2/train_v2.ipynb is the original, unedited.

training/data/varun/ (126,919 old captchas) was zipped to training/data/varun.zip on 2026-10-30 and the loose
PNGs deleted after verification. Code here expects the folder: cd training/data && unzip -q varun.zip

Copied out to the live v2 workspace (originals still here):
  training/v1/models/captcha_cnn_ft_650.pt -> models/   (v2's teacher)
  host/ocr, host/ocr.swift                 -> tools/
  training/scripts/*                       -> scripts/  (since adapted for v2)
  extension/, export_model.py, build_zip.sh -> project root (since adapted for v2: red mask, v5.0)

The live extension is at the project root again; the copy here is the frozen v4.1 for old captchas.
