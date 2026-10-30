Instant CAPTCHA Paster
=====================

Fills the captcha on login.gitam.edu with a small neural network that runs inside the extension.
Nothing else to install: no Python, no helper program. Works in Chrome (and Chromium-based
browsers such as Edge and Brave) on macOS, Linux and Windows.

Install
-------
1. Unzip this folder somewhere permanent (the browser keeps loading it from there).
2. Open chrome://extensions (Edge: edge://extensions, Brave: brave://extensions).
3. Turn on "Developer mode" (top right).
4. Click "Load unpacked" and choose the unzipped folder (the one containing manifest.json).
5. Open login.gitam.edu. The captcha box fills itself almost instantly, and again
   every time the captcha refreshes.

Check it is working
-------------------
Right-click the login page -> Inspect -> Console. Each captcha logs a line like
    [CAPTCHA] Pasted mMy2g (confidence 0.922, model 30 ms, total 60 ms)
Low confidence (below about 0.5) means the read is a guess: check the box before submitting.

Update the model
----------------
From the project root: python3 export_model.py [models/<model>.pt] (default models/captcha_cnn_v2_ft.pt)
rewrites model/model.json and model/weights.bin. Then click the reload icon on the extension in
chrome://extensions. model.js keeps only the red pixels (the letters) before reading, the same
prep.ink step training uses (scripts/prep.py); change both together or not at all.

Files
-----
manifest.json    extension definition
content.js       reads the captcha image on the page and fills the answer
background.js    loads the model and reads captchas
model.js         red-letter mask + runs the network (layer order, softmax)
model.wasm       the heavy maths, compiled to WebAssembly (archive/v1_2026-10-30/wasm/kernels.c)
model/           trained weights (model.json + weights.bin)
