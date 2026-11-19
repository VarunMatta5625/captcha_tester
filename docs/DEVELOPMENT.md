# Development

Notes for working on the extension or the training workspace. Usage is in the [README](../README.md), training and data in [TRAINING.md](TRAINING.md), version history in [CHANGELOG.md](CHANGELOG.md).

## Layout

- `extension/`: the Chrome/Edge/Brave extension (Manifest V3). Load unpacked from here. `content.js` reads the captcha and runs auto-login, `background.js` runs the model and saves rejected captchas, `model.js` + `model.wasm` + `model/` are the network, and `popup.html`, `options.html` and `settings-ui.js` are the settings.
- `docs/`: these docs and the pictures in `docs/images/`.
- `export_model.py`: checkpoint to `extension/model/{model.json,weights.bin}` with BatchNorm folded in. Defaults to `models/captcha_cnn_v5.pt`. Writes the checkpoint's `levels` into `model.json`.
- `build_zip.sh`: packs `extension/` into `dist/captcha-paster-<version>.zip` (git-ignored, regenerable).
- `models/`: `captcha_cnn_v5.pt` (shipped) and `captcha_cnn_v4_ft.pt` (v5's teacher).
- `notebooks/train_v5.ipynb`: round 5, shipped in 5.3. Use it as the template for later rounds.
- `scripts/`: `prep.py` (image cleaning, shared by the notebooks and scripts, plus the Apple Vision helpers), `label_vision.py`, `audit_gold.py`, `relabel.py`, `review.py`, `finetune.py`. See [TRAINING.md](TRAINING.md).
- `tools/`: `check_extension.py` and `.mjs` (the pre-ship check), `run_round.py` (runs a round notebook headless), `make_doc_figures.py` (changelog figures), `readme_visuals/` (README pictures), `ocr` and `ocr.swift` (Apple Vision OCR, macOS only).
- `data/`: gold, reviews, labels, and the git-ignored captcha zip. See [TRAINING.md](TRAINING.md#data).
- `archive/`: earlier work, kept as it was. Don't edit it, copy what you need out.

## Checks

There's no unit test suite. The check that matters is the pre-ship one. It runs the checkpoint through the extension's own `model.js` and `model.wasm` in Node and through PyTorch, on gold and on the site's rejected captchas, and fails unless every read matches:

```sh
python3 tools/check_extension.py                      # the shipped v5
python3 tools/check_extension.py models/<model>.pt    # a candidate
```

It needs `node` and `data/captchas.zip` (for gold). For v5 you should see `JS == PyTorch on 208/208`, gold 200/200 and site rejections 8/8. To syntax-check the extension scripts, run `node --check extension/content.js` and the same for the other `.js` files.

The auto-login rules have no unit test. I ran them against a local copy of the login page with the real extension (`tools/readme_visuals/`, see below), not against the live site, because signing in needs a real account.

## Shipping a model

```sh
python3 tools/check_extension.py models/<model>.pt   # stop here if any read differs
python3 export_model.py models/<model>.pt
# bump "version" in extension/manifest.json
./build_zip.sh                                       # dist/captcha-paster-<version>.zip
```

Then reload the extension in `chrome://extensions` (the circular arrow on its card; use Load unpacked again if the folder was replaced). It loads straight from the folder, so reload after every edit. On the login page the console should show `[CAPTCHA] Pasted xxxxx (confidence ...)`. Update the model table in [TRAINING.md](TRAINING.md#current-models) too.

## Rolling back

Keep the previous zips in `dist/`. At 5.5, the 5.4 zip is auto-login without the rules and 5.3 is v5 without auto-login. `dist/` is git-ignored, so the published releases are the other copy.

## Releasing

For any extension version, whether or not the model changed:

1. Add the version to `docs/CHANGELOG.md`: a row in the table and a section covering what changed, why, settings and tests. New figures go in `tools/make_doc_figures.py`.
2. Commit, then tag and publish:
   ```sh
   git tag -a v<version> -m "Extension <version>: <summary>" && git push origin main v<version>
   gh release create v<version> dist/captcha-paster-<version>.zip --title "<version>: <summary>" --notes-file <notes.md>
   ```
   The release notes are for users (what's new, safety, what was tested, known issues, install) and link to the changelog for the details.

## Rebuilding the README pictures

The pictures are illustrations made by `tools/readme_visuals/`, which drives a throwaway Chromium profile with the extension loaded:

- `real_scenes.py` opens the login page itself, only with GET requests to `login.gitam.edu`, `cdn.gitam.edu` and `cdn.jsdelivr.net`. Everything else, and every POST, is blocked, so a login can't be sent. Fake credentials are saved in the throwaway profile for the "fill" picture, with auto sign-in off.
- `mock_site.py` is a local, unbranded copy of the form with the element ids `content.js` needs. It's used for the console pictures (signing in, the rules, rejected captchas). Fake credentials only (`demo1234` / `demo-password`).
- `browser.py` starts Chromium with the extension in a throwaway profile. In the mock scenes only the mock hosts answer.
- `scenes.py` and `make_visuals.py` hold the scenes and assemble the GIFs. `model_visuals.py` makes the cleaning animation, the per-character confidences and the accuracy chart from the model itself. `anno.py` draws the boxes, numbers and panels.

```sh
pip install playwright && python3 -m playwright install chromium
python3 tools/readme_visuals/make_visuals.py     # browser scenes -> docs/images/
python3 tools/readme_visuals/model_visuals.py    # model figures  -> docs/images/
```

Which scene makes which image is in [tools/readme_visuals/README.md](../tools/readme_visuals/README.md). After editing any Markdown, run `python3 tools/readme_visuals/check_docs.py` to check links, anchors and unused images.

The scenes that open the real page need network access. The mock scenes need `data/captchas.zip`, because the mock serves gold captchas. Scene names for `make_visuals.py`: `real_first real_refresh real_fill popup install console rules hero`. `network.svg` is hand-written SVG.

## GitHub

`origin` is `github.com/VarunMatta5625/captcha_tester`. Commits use the GitHub noreply address (`git config user.email` in this repo), because the account blocks pushes that expose a private email. Git-ignored data (captcha zips, `cache/`, `dist/`) isn't on GitHub, so back it up yourself.
