# host/ - LEGACY native-messaging helpers

The shipping extension does NOT use anything here except one file:

- `captcha_cnn.pt`: the model checkpoint `../export_model.py` reads. Currently identical to `../training/v1/models/captcha_cnn_ft_650.pt`. Replace it to ship a new model.

Everything else (`cnn_host*`, `vision_host*`, `native_messaging.py`, `pipeline.py`, `cnn.py`, `ocr`/`ocr.swift`, `install.sh`) belongs to the two archived extension variants in `../archive/`. `install.sh` derives the extension ID from the folder path and the `cnn_host`/`vision_host` launchers contain absolute paths, so they break if the project moves. `pipeline.py` is a script copy of the cleanup + Vision OCR pipeline developed in `../notebooks/main_vision_ocr.ipynb` (the notebook does not import it).
