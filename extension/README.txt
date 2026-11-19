Instant CAPTCHA Paster
======================

Fills in the captcha on login.gitam.edu using a small neural network that runs inside the
extension. There's nothing else to install: no Python, no helper program. It works in Chrome and
other Chromium browsers (Edge, Brave). It can also fill in your User ID and password and press
LOGIN for you, if you ask it to.

Install
-------
1. Unzip this folder somewhere it can stay. The browser keeps loading the extension from there.
2. Open chrome://extensions (Edge: edge://extensions, Brave: brave://extensions).
3. Turn on "Developer mode", top right.
4. Click "Load unpacked" and pick the unzipped folder, the one with manifest.json in it.
5. Open login.gitam.edu. The captcha box fills itself, and again each time the captcha refreshes.

Checking that it works
----------------------
Right-click the login page, Inspect, Console. Every captcha logs a line like
    [CAPTCHA] Pasted mMy2g (confidence 0.922, model 30 ms, total 60 ms)
A confidence below about 0.5 means it's guessing, so check the box before you submit.
If the site turns down a read, you'll see
    [CAPTCHA] Site rejected the model's read, saved captcha_mistakes/20261031-025337_model-r6EAg_conf-0.900.png

Auto-login
----------
Click the toolbar icon (or Details, then Extension options), enter your User ID and password, tick
what you want and hit Save. On a fresh install the first two boxes are ticked, but nothing gets
filled in or pressed until you've saved a User ID and password.

- "Auto populate credentials only": fills User ID, password and the captcha. You press LOGIN.
- "Auto sign-in when the site is opened": also presses LOGIN. Ticking it ticks the first box too,
  and unticking the first box unticks it.
- "Also sign in after logging out": a sub-box of auto sign-in, off by default.

When it signs in: with auto sign-in on, LOGIN gets pressed when you open the login page by typed
address, bookmark or a link, and never on a reload or back/forward. With the sub-box ticked it also
signs in when you arrive from another gitam.edu page (after a logout or a session timeout). In every
other case everything is still filled in and you press LOGIN yourself. The retry after "Invalid
CAPTCHA" works the same way either way. The console logs `Page load: type ..., referrer ...` so you
can see what it decided.

A word on safety. The extension assumes the site pauses a User ID after 5 failed logins, so:
- After a wrong password it stops for that tab and leaves the password box empty. After an invalid
  captcha it retries once at most. It does nothing while the rate-limit break is showing.
- Those counters are per tab and start over whenever the login page opens without a message on it.
  So if the saved password is wrong, every fresh open costs one failed login. Fix it after the
  first failure.
- A read below the minimum confidence (0.5 by default) still fills the captcha, but you press LOGIN,
  so a guess never costs an attempt.

The password is kept in the extension's own storage (chrome.storage.local), on this machine only,
and never synced. It isn't encrypted, so skip auto sign-in on a shared computer. "Clear" removes it.

Captchas the model got wrong
----------------------------
If you press LOGIN with the model's answer and the site says "Invalid CAPTCHA", the rejected captcha
is saved to
    Downloads/captcha_mistakes/<time>_model-<model's read>_conf-<confidence>.png
(the time is UTC). Only rejected reads are saved. Correct reads, wrong-password failures and logins
where you typed the code yourself save nothing. The right answer isn't known, so label these later.

Updating the model
------------------
From the project root, run python3 export_model.py [models/<model>.pt] (default
models/captcha_cnn_v5.pt). That rewrites model/model.json and model/weights.bin. Then click the
reload icon on the extension in chrome://extensions. model.js cleans the image the same way training
did (scripts/prep.py): red letters 0, gray blobs 128, paper 255 (prep.clean), or letters only for
models exported without "levels": 3 (prep.ink). Change both together or not at all.

Files
-----
manifest.json    the extension definition
content.js       reads the captcha image on the page, fills in the answer, spots rejected reads,
                 fills credentials and presses LOGIN (with the guards described above)
background.js    loads the model, reads captchas, saves misread ones (downloads)
model.js         image cleaning (letters / blobs / paper) and the network (layer order, softmax)
model.wasm       the heavy math, compiled to WebAssembly (archive/v1_2026-10-30/wasm/kernels.c)
model/           the trained weights (model.json + weights.bin)
popup.html       toolbar popup: credentials and the three auto-login boxes
options.html     the full options page (same form, plus security notes)
settings-ui.js   form logic shared by both (storage, validation, linked checkboxes)
popup.js         the popup's link to the options page
icons/, logo.png toolbar icons and the popup's logo
