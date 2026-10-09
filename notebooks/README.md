# notebooks/ - historical

| File | What | Re-runnable? |
|---|---|---|
| `main_vision_ocr.ipynb` | Original Apple Vision OCR pipeline development (cleanup params, review loop). | Yes (macOS; uses `../host/ocr` and `../training/data/varun`). |
| `cleanup_test.ipynb` | Cleanup/OCR experiments built on the above. | Yes, same needs. |
| `train_colab.ipynb` | Older Colab trainer. Expects `image_ftech_solver.zip` and Drive paths under `/content/`. | Only on Colab with that zip rebuilt. |
| `comparison_245.pdf` | Vision-vs-truth comparison of 245 images (2026-09-29). | n/a |
| `test/` | 283 sample PNGs. | n/a |
| `.ipynb_checkpoints/`, `.jupyter/` | Jupyter state, deletable. | n/a |

Current training notebooks are in `../training/` (`v1/train_v1.ipynb`, `v2/train_v2.ipynb`).
