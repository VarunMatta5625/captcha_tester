Round 4 (captcha style 3), archived 2026-11-01 when extension 5.3 shipped v5 (round 5).

notebooks/train_v4.ipynb   round 4: gold check, relabel with v3 + Apple Vision (Vision's J where v3 reads 3),
                           three-level training from v3's weights. Outputs are from the three-level run.
data/labels_v4.csv         its training labels (v3 + Vision agreement: under-represents lowercase y and J, and
                           labels hard 6s as 5; round 5 relabelled with v4_ft instead).
models/captcha_cnn_v4.pt   v4, shipped in extension 5.2 (dist/captcha-paster-5.2.zip, the rollback): gold 97.0%
                           (194/200), 8/8 site rejections. Misses: 6 read as 5, J as 3, y as Y.
models/captcha_cnn_v3.pt   the style-2 model (gold 86.0% on style 3), teacher of round 4.

Still live at the project root: models/captcha_cnn_v4_ft.pt (v4 fine-tuned on the 88 hard cases in
data/reviews.json, gold 100%), because it is the teacher of round 5 (notebooks/train_v5.ipynb).

To re-run train_v4.ipynb, copy it back to notebooks/ and the two models back to models/ (it reads gold, Vision labels
and the captcha zip from the live data/ folder, and writes ../data/labels_v4.csv).
