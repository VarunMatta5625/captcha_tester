# Development

Everything you need to work on the extension or the training workspace. User documentation is in the [README](../README.md); training and data in [TRAINING.md](TRAINING.md); version history in [CHANGELOG.md](CHANGELOG.md).

- [Repository layout](#repository-layout)
- [Run the checks](#run-the-checks)
- [Ship a model to the extension](#ship-a-model-to-the-extension)
- [Rollback](#rollback)
- [Release](#release)
- [Rebuild the README pictures](#rebuild-the-readme-pictures)
- [GitHub notes](#github-notes)

## Repository layout

| Path | What |
|---|---|
| `extension/` | The Chrome/Edge/Brave extension (Manifest V3). Load unpacked from here. See `extension/README.txt`. `content.js` reads the captcha and runs auto-login, `background.js` runs the model and saves rejected captchas, `model.js` + `model.wasm` + `model/` are the network, `popup.html` / `options.html` / `settings-ui.js` are the settings. |
| `docs/` | `CHANGELOG.md` (every extension version), `TRAINING.md`, this file, and the pictures in `docs/images/`. |
| `export_model.py` | Checkpoint to `extension/model/{model.json,weights.bin}` (BatchNorm folded). Default: `models/captcha_cnn_v5.pt`. Writes the checkpoint's `levels` into `model.json`. |
| `build_zip.sh` | `extension/` to `dist/captcha-paster-<version>.zip` (git-ignored, regenerable). |
| `models/` | `captcha_cnn_v5.pt` (shipped) and `captcha_cnn_v4_ft.pt` (v5's teacher). |
| `notebooks/train_v5.ipynb` | Round 5 (shipped in 5.3). Template for later rounds. |
| `scripts/` | `prep.py` (image cleaning shared by notebooks and scripts, Apple Vision helpers), `label_vision.py`, `audit_gold.py`, `relabel.py`, `review.py`, `finetune.py`. Details in [TRAINING.md](TRAINING.md). |
| `tools/` | `check_extension.py` + `.mjs` (pre-ship check), `run_round.py` (runs a round notebook headless), `make_doc_figures.py` (CHANGELOG figures), `readme_visuals/` (README screenshots and GIFs), `ocr` + `ocr.swift` (Apple Vision OCR, macOS only). |
| `data/` | Gold, reviews, labels and the git-ignored captcha zip. See [TRAINING.md](TRAINING.md#data). |
| `archive/` | Frozen snapshots of earlier work. See `archive/README.md`. Do not edit; copy what you need out. |

## Run the checks

There is no unit-test suite. The check that matters is the pre-ship check, which runs the checkpoint through the extension's own `model.js` and `model.wasm` in Node and through PyTorch, on gold and on the site's rejected captchas, and fails unless every read matches:

```sh
python3 tools/check_extension.py                      # the shipped v5
python3 tools/check_extension.py models/<model>.pt    # a candidate
```

It needs `node` and `data/captchas.zip` (for gold). Expected for v5: `JS == PyTorch on 208/208`, gold 200/200, site rejections 8/8. Syntax check of the extension scripts: `node --check extension/content.js` (and the other `.js` files).

The auto-login rules have no unit test. They were run end to end against a local stand-in login page with the real extension (`tools/readme_visuals/`, see below), not against the live site, because signing in needs a real account.

## Ship a model to the extension

```sh
python3 tools/check_extension.py models/<model>.pt   # JS == PyTorch on every gold/site captcha, else stop
python3 export_model.py models/<model>.pt            # default: models/captcha_cnn_v5.pt
# bump "version" in extension/manifest.json
./build_zip.sh                                       # dist/captcha-paster-<version>.zip (the release asset)
```

Reload the extension in `chrome://extensions` (the circular arrow on its card; Load unpacked again if it was loaded from a folder that was replaced). On the login page the console (F12) logs `[CAPTCHA] Pasted xxxxx (confidence …)`. Update the model table in [TRAINING.md](TRAINING.md#current-models). Chrome loads the unpacked extension from the folder itself, so reload it after every edit.

## Rollback

`dist/captcha-paster/` can hold the unzipped current version, and the previous zips in `dist/` are the rollback (at 5.5: 5.4 = auto-login without the rules; 5.3 = v5 without auto-login). `dist/` is git-ignored, so published releases are the other copy.

## Release

Any extension version, model change or not:

1. Add the version to `docs/CHANGELOG.md` (at-a-glance row and a section: what changed, why, config, tests). New figures: extend `tools/make_doc_figures.py`.
2. Commit, then tag and publish:
   ```sh
   git tag -a v<version> -m "Extension <version>: <summary>" && git push origin main v<version>
   gh release create v<version> dist/captcha-paster-<version>.zip --title "<version>: <summary>" --notes-file <notes.md>
   ```
   Release notes are user-facing (new, safety, tested, known issues, install) and link `docs/CHANGELOG.md` for detail.

## Rebuild the README pictures

The screenshots and GIFs in the README are real runs of the shipped extension, made by `tools/readme_visuals/`:

- `real_scenes.py`: the screenshots of the **real** login page. Read-only: GET requests to `login.gitam.edu`, `cdn.gitam.edu` and `cdn.jsdelivr.net` only, everything else (and every POST) is aborted, so a login can never be sent. Fake credentials are stored in the throwaway profile for the "fill" picture, with auto sign-in off.
- `mock_site.py`: a local, unbranded stand-in (used only for the console pictures of signing in, the rules and rejected captchas) for the login page with the element ids `content.js` needs. Fake credentials only (`demo1234` / `demo-password`).
- `browser.py`: Chromium with the extension in a throwaway profile. In the mock scenes only the mock hosts answer, every other request is aborted and no hostname resolves.
- `scenes.py`, `make_visuals.py`: the scenes and the GIF assembly. `model_visuals.py`: cleaning animation, per-character confidence and the accuracy chart, made from the model itself. `anno.py`: red boxes, numbered steps and panels.

```sh
pip install playwright && python3 -m playwright install chromium
python3 tools/readme_visuals/make_visuals.py     # browser scenes -> docs/images/
python3 tools/readme_visuals/model_visuals.py    # model figures  -> docs/images/
```

Which scene makes which image, and the rules for rebuilding, are in [tools/readme_visuals/README.md](../tools/readme_visuals/README.md). After editing any Markdown, run `python3 tools/readme_visuals/check_docs.py` (links, anchors, unused images, Mermaid and math parse).

The real-page scenes need network access to the login page; the mock scenes need `data/captchas.zip` (the mock serves gold captchas). Scene names for `make_visuals.py`: `real_first real_refresh real_fill popup install console rules hero`. The diagrams `docs/images/banner.svg`, `network.svg` and `folder-picker.svg` are hand-written SVG. The folder picker is an illustration, not a screenshot, because it is an operating system window.

## GitHub notes

`origin` is `github.com/VarunMatta5625/captcha_tester`. Commits use the GitHub noreply address (`git config user.email` in this repository): the account blocks pushes that expose a private email. The repository has one collaborator with write access (personal-account repositories have no admin role). Git-ignored data (captcha zips, `cache/`, `dist/`) is not on GitHub: back it up separately.
