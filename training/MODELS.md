# Model registry

All models: same CNN architecture (see `../docs/STATE.md`), PyTorch state dicts, ~7.3 MB. Gold = `data/gold.csv`, 152 hand-checked images. Scores for v1 rows were taken before the gold audit (7 labels corrected); v2 was also scored before it. Re-score on corrected gold before comparing.

| File | Trained on | Gold exact | SHA-256 (first 16) |
|---|---|---|---|
| `v1/models/captcha_cnn.pt` | Apple Vision labels (`v1/labels_vision.csv`) | 86.84% | e271d8c097480031 |
| `v1/models/captcha_cnn_ft_150.pt` | baseline fine-tuned on 150 reviews | not recorded | f11a39011c199559 |
| `v1/models/captcha_cnn_ft_350.pt` | baseline fine-tuned on 350 reviews | not recorded | e4c88034f67a526c |
| `v1/models/captcha_cnn_ft_650.pt` | baseline fine-tuned on 650 reviews | **93.42%** (char 98.68%) | 8cbf3d721a58201f |
| `v2/models/captcha_cnn_v2.pt` | `v2/labels_v2.csv` (labels from ft_650 teacher) | 94.08% (143/152) | 44cd76758a60e8c4 |
| `v2/models/captcha_cnn_v2_ft.pt` | (planned) v2 fine-tuned on reviews | not run, file does not exist | - |
| `../host/captcha_cnn.pt` | copy of ft_650 | = ft_650 | 8cbf3d721a58201f |
| `../archive/cnn_native_host_2026-09-30/host/captcha_cnn.pt` | frozen copy of ft_650 | = ft_650 | (same size 7320253) |

## Shipped
`extension/model/{model.json,weights.bin}` was exported from `host/captcha_cnn.pt` = **ft_650**, extension v4.1.
Verify a checkout: `shasum -a 256 host/captcha_cnn.pt training/v1/models/captcha_cnn_ft_650.pt` must match.

When you add a model, add a row here (file, labels, gold score on the corrected gold, hash) and say which one ships.
