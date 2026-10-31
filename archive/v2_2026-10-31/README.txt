Frozen 2026-10-31 snapshot of the v2 workspace (red letters on fine gray speckle; shipped extension 5.1 with
captcha_cnn_v2_ft.pt, gold 98.5%), archived when the site switched to a bolder font on large gray blobs
(between 03:02 and 08:04 UTC on 2026-10-31).

README.md is the project README as it was. Everything else is where it was at the project root, so paths inside
resolve relative to this folder: notebooks/ (train_v2, train_v3, and train_v4: an unfinished hard-gold round that was
never run), scripts/ (incl. hardness.py and pick_gold.py from that round), data/, models/, extension/,
export_model.py, build_zip.sh, cache/.

data/captchas.zip (100,000 v2-style captchas) and cache/ are git-ignored: back the zip up, every label here refers
to its ids. Its ids (1..100000) overlap the next style's ids: never mix data/*.csv or reviews.json from here into the
live workspace.

Still live at the project root (originals; copies here): scripts/*.py (since adapted), captcha_cnn_v3.pt (teacher
of round 4), extension/ (since 5.2), export_model.py, build_zip.sh. models/captcha_cnn_v2_ft.pt (extension 5.1)
lives only here since 5.2 shipped.

data/site_mistakes/: the one style-2 captcha extension 5.1 saved as rejected (03:02 UTC, minutes before the style
change). 5.1 read Gy6nb and the site said no, so the truth is most likely GY6nb (labels.csv; not hand-checked).
