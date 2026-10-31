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
A rejected read logs
    [CAPTCHA] Site rejected the model's read, saved captcha_mistakes/20261031-025337_model-r6EAg_conf-0.900.png

Captchas the model got wrong
----------------------------
When you press LOGIN with the model's answer and the site replies "Invalid CAPTCHA", the rejected
captcha is saved automatically to
    Downloads/captcha_mistakes/<time>_model-<model's read>_conf-<confidence>.png
(time is UTC). Only rejected reads are saved: correct reads, wrong-password failures and logins
where you retyped the code yourself save nothing. The right answer is unknown; label these later.

Update the model
----------------
From the project root: python3 export_model.py [models/<model>.pt] (default models/captcha_cnn_v4.pt)
rewrites model/model.json and model/weights.bin. Then click the reload icon on the extension in
chrome://extensions. model.js cleans the image before reading exactly like training (scripts/prep.py):
red letters 0, gray blobs 128, paper 255 (prep.clean), or letters only for models exported without
"levels": 3 (prep.ink); change both together or not at all.

Files
-----
manifest.json    extension definition
content.js       reads the captcha image on the page, fills the answer, spots rejected reads
background.js    loads the model, reads captchas, saves misread ones (downloads)
model.js         image cleaning (letters / blobs / paper) + runs the network (layer order, softmax)
model.wasm       the heavy maths, compiled to WebAssembly (archive/v1_2026-10-30/wasm/kernels.c)
model/           trained weights (model.json + weights.bin)
