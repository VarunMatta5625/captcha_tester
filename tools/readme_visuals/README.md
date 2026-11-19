# README pictures

Everything that makes the images in `docs/images/` lives here or in `tools/make_doc_figures.py`, so a change to the extension or the README can be followed by a rebuild. Run from the repository root.

```sh
pip install playwright && python3 -m playwright install chromium    # once
python3 tools/readme_visuals/make_visuals.py                        # all browser scenes, in the right order
python3 tools/readme_visuals/make_visuals.py real_first popup       # or just some
python3 tools/readme_visuals/model_visuals.py                       # cleaning animation, confidence figure, accuracy chart
python3 tools/readme_visuals/check_docs.py                          # links, anchors, images, Mermaid, math
```

The pictures are illustrations: some come from the login page itself, others from a local copy of the form, and the model figures are drawn from the model.

## Which scene makes which image

| Scene (`make_visuals.py`) | Images in `docs/images/` | Source |
|---|---|---|
| `real_first` | `first-run-1.png`, `first-run-2.png`, `first-run.gif` | The login page itself, never submitted (`real_scenes.py`) |
| `real_refresh` | `refresh-1..4.png`, `refresh.gif` | Same |
| `real_fill` | `fill-only.png` | Same, with fake credentials in the throwaway profile and auto sign-in off |
| `popup` | `popup-1..5.png`, `popup.gif` | The extension's popup in a throwaway profile (`scenes.py`) |
| `install` | `install-1..3.png`, `install.gif` | The `chrome://extensions` page |
| `console` | `signin.png`, `reject.png` | Console output from a run against the local copy of the form (`mock_site.py`) |
| `rules` | `rules.png` | Same: four loads of the local copy |
| `hero` | `demo.gif` | Put together from the pictures above, so run it last |
| `model_visuals.py` | `cleaning.gif`, `reading.png`, `accuracy.png` | The model and gold captchas (needs `data/captchas.zip`) |
| `../make_doc_figures.py` | `styles.png`, `cleaning.png`, `site_mistakes.png` | The captcha zips (changelog figures) |
| by hand | `network.svg` | Edit the SVG |

The numbered stills (`install-1..3.png`, `popup-1..5.png`, `refresh-1..4.png`, `first-run-1/2.png`) are intermediate frames. They're git-ignored, and `hero` needs them, so run the whole `make_visuals.py` rather than `hero` alone.

## Files

- `real_scenes.py`: opens the login page itself. Only GET requests to `login.gitam.edu`, `cdn.gitam.edu` and `cdn.jsdelivr.net` go through, everything else and every POST is blocked, so nothing can be submitted.
- `mock_site.py`, `scenes.py`, `browser.py`: the local copy of the form and the scenes that need a sign-in or a rejection, which can't be shown on the live site without a real account. The mock only answers its own hosts.
- `anno.py`: canvas, boxes, numbered steps, callouts, console panel and the GIF writer (one palette for all frames).
- `model_visuals.py`: figures made from the model itself.
- `check_docs.py`: checks the Markdown after an edit.

## Rules

- Fake credentials only (`demo1234` / `demo-password`). Never put a real User ID or password in a picture.
- Use a throwaway profile, which the scripts do. Don't point them at your own browser profile, because the extension's settings there hold your real login.
- After a rebuild, look at the pictures before committing the changed files in `docs/images/`.
