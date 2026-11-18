# README pictures: how to remake them

Everything that makes the images in `docs/images/` lives here or in `tools/make_doc_figures.py`, so a change to the extension or the README can be followed by a rebuild. Run from the repository root.

```sh
pip install playwright && python3 -m playwright install chromium    # once
python3 tools/readme_visuals/make_visuals.py                        # all browser scenes, in the right order
python3 tools/readme_visuals/make_visuals.py real_first popup       # or just some
python3 tools/readme_visuals/model_visuals.py                       # cleaning animation, confidence figure, accuracy chart
python3 tools/readme_visuals/check_docs.py                          # links, anchors, images, Mermaid, math
```

## Which scene makes which image

| Scene (`make_visuals.py`) | Images in `docs/images/` | Source |
|---|---|---|
| `real_first` | `first-run-1.png`, `first-run-2.png`, `first-run.gif` | The **real** login page, read-only (`real_scenes.py`) |
| `real_refresh` | `refresh-1..4.png`, `refresh.gif` | Real login page |
| `real_fill` | `fill-only.png` | Real login page, fake credentials in the throwaway profile, auto sign-in off |
| `popup` | `popup-1..5.png`, `popup.gif` | The extension's own popup in a throwaway profile (`scenes.py`) |
| `install` | `install-1..3.png`, `install.gif` | Real `chrome://extensions` page |
| `console` | `signin.png`, `reject.png` | Console output of a run against the local stand-in page (`mock_site.py`) |
| `rules` | `rules.png` | Same: four loads of the stand-in page, real console lines |
| `hero` | `demo.gif` | Assembled from the pictures above, so run it last |
| `model_visuals.py` | `cleaning.gif`, `reading.png`, `accuracy.png` | The model and gold captchas (needs `data/captchas.zip`) |
| `../make_doc_figures.py` | `styles.png`, `cleaning.png`, `site_mistakes.png` | The captcha zips (CHANGELOG figures) |
| hand-written | `banner.svg`, `network.svg`, `folder-picker.svg` | Edit the SVG files directly |

## Files

- `real_scenes.py`: the real login page. Only GET requests to `login.gitam.edu`, `cdn.gitam.edu` and `cdn.jsdelivr.net` are allowed; everything else, and every POST, is aborted, so nothing can be submitted.
- `mock_site.py`, `scenes.py`, `browser.py`: the local stand-in page and the scenes that need a sign-in or a rejection, which cannot be shown on the real site without a real account. The mock only answers its own hosts and no hostname resolves.
- `anno.py`: canvas, red boxes, numbered steps, callouts, console panel and GIF writer (one palette for all frames).
- `model_visuals.py`: figures made from the model itself.
- `check_docs.py`: checks the Markdown after an edit.

## Rules

- Fake credentials only (`demo1234` / `demo-password`). Never put a real User ID or password in a picture.
- Run it in a throwaway profile (the scripts do). Do not point it at your own browser profile: the extension's settings there hold your real login.
- After a rebuild, look at the pictures, then commit the changed files in `docs/images/`.
