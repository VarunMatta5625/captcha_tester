<div align="center">

<img src="docs/images/banner.svg" alt="Instant CAPTCHA Paster: a small neural network that reads a login captcha inside your browser" width="100%">

<br>

![Extension 5.5](https://img.shields.io/badge/extension-5.5-007467?style=flat-square)
![Manifest V3](https://img.shields.io/badge/Manifest-V3-4285f4?style=flat-square&logo=googlechrome&logoColor=white)
![Chrome, Edge, Brave](https://img.shields.io/badge/browsers-Chrome%20%C2%B7%20Edge%20%C2%B7%20Brave-555?style=flat-square)
![Gold 200/200](https://img.shields.io/badge/hand--checked%20gold-200%2F200-30d158?style=flat-square)
![No runtime dependencies](https://img.shields.io/badge/runtime%20dependencies-none-ff9f0a?style=flat-square)

**A Chrome extension that reads the 5-character login captcha on `login.gitam.edu` with a small CNN running inside the browser (WebAssembly), and can fill your login and sign you in.**

[Setup](#setup) · [Overview](#overview) · [Usage](#usage) · [How it works](#how-it-works) · [Security](#security) · [Known limits](#known-limits) · [Development](#development) · [Docs](#documentation-map)

<br>

<img src="docs/images/demo.gif" alt="Animated demo: the login page opens, the captcha is read and typed, a refresh is read again, then auto sign-in logs in without any click" width="100%">

</div>

> [!NOTE]
> **The login screenshots are of the real login page**, opened read-only in a throwaway browser profile (never my own browser): the page is loaded and the extension fills it, and **nothing is ever submitted**. Any User ID or password in a picture is a fake one. The two exceptions are labelled in place: pictures of *signing in* and of *rejected captchas* show console output from a test run on a local stand-in page, because those need a real account or a real rejection on the real site. The folder picker in the install step is an illustration, because it is an operating system window.

---

## Setup

From download to a login page that fills itself: install, first run, first use. About five minutes.

### 1. Install

You need Chrome, Edge or Brave. Nothing else: no Python, no helper program.

1. Download `captcha-paster-5.5.zip` from the [latest release](https://github.com/VarunMatta5625/captcha_tester/releases/latest) (about 7 MB; while the repository is private you must be signed in with access to it). Or clone this repository and use its `extension/` folder directly.
2. Unzip it somewhere **permanent**: the browser keeps loading the extension from that folder. You get one folder, `captcha-paster`.
3. Open `chrome://extensions` (Edge: `edge://extensions`, Brave: `brave://extensions`) and turn on **Developer mode**, top right.
4. Click **Load unpacked** and choose the `captcha-paster` folder (the one that contains `manifest.json`).

<p align="center">
  <img src="docs/images/install.gif" alt="Three steps on the extensions page: turn on Developer mode, click Load unpacked, the Instant CAPTCHA Paster card appears" width="100%">
</p>

<details>
<summary><b>The three steps as still pictures, and the folder picker</b></summary>

<p align="center"><img src="docs/images/install-1.png" alt="Step 1: Developer mode switch is highlighted" width="100%"></p>
<p align="center"><img src="docs/images/install-2.png" alt="Step 2: the Load unpacked button is highlighted" width="100%"></p>
<p align="center"><img src="docs/images/install-3.png" alt="Step 3: the extension card with the reload arrow highlighted" width="100%"></p>

The folder picker is an operating system window and cannot be captured from the page, so this is an **illustration**:

<p align="center"><img src="docs/images/folder-picker.svg" alt="Illustration of the folder picker: choose the captcha-paster folder, then confirm" width="100%"></p>

In these pictures the extension was loaded with a launch flag in a throwaway browser profile instead of the picker; the card is what you will see afterwards.

</details>

> [!TIP]
> Pin the extension (puzzle-piece icon in the toolbar) to reach its settings in one click.

### 2. First run

Open `login.gitam.edu`. The captcha box fills itself, and again every time the captcha refreshes.

<p align="center">
  <img src="docs/images/first-run.gif" alt="The captcha box is empty while the image loads, then it fills with the read captcha" width="100%">
</p>

<details>
<summary><b>Still picture of the empty state</b></summary>

<p align="center"><img src="docs/images/first-run-1.png" alt="The login page while the captcha image is still loading: the captcha box is empty" width="100%"></p>

</details>

To see that it works, right-click the page, choose **Inspect**, then **Console**. Each captcha logs one line:

```text
[CAPTCHA] Pasted J2qgj (confidence 0.892, model 108 ms, total 214 ms)
```

A confidence below about 0.5 means the read is a guess: check the box before you submit.

<p align="center">
  <img src="docs/images/first-run-2.png" alt="The filled captcha box with numbered callouts and the console line" width="100%">
</p>

### 3. First use: let it sign in for you (optional)

Click the toolbar icon, type your User ID and password, choose how far it should go, and **Save**.

<p align="center">
  <img src="docs/images/popup.gif" alt="The toolbar popup: type the User ID and password, see the linked checkboxes, set the minimum confidence, press Save" width="100%">
</p>

| Box | What it does |
|---|---|
| **Auto populate credentials only** | Fills User ID, password and captcha. You press LOGIN. |
| **Auto sign-in when the site is opened** | Also presses LOGIN, once, when you open the login page by typed address, bookmark or link. Ticking it ticks the box above. |
| **Also sign in after logging out** | Sub-box of auto sign-in, off by default. Also signs in when you arrive from a `gitam.edu` page (logout, session timeout). |
| **Min CAPTCHA confidence to press LOGIN** | Default 0.5. Below it, the captcha is still filled and LOGIN is left to you. `0` means always press. |

On a fresh install the first two boxes are ticked. A save of a User ID and password is what switches things on. (Release 5.5 has one bug here: with auto sign-in on and nothing saved yet, it presses LOGIN on the empty form. This is fixed in the source but not yet released, see [Known limits](#known-limits).)

<details>
<summary><b>The popup, step by step (still pictures)</b></summary>

<p align="center"><img src="docs/images/popup-1.png" alt="Step 1: the popup opens with empty fields" width="100%"></p>
<p align="center"><img src="docs/images/popup-2.png" alt="Step 2: User ID and password typed in" width="100%"></p>
<p align="center"><img src="docs/images/popup-3.png" alt="Step 3: the three checkboxes explained" width="100%"></p>
<p align="center"><img src="docs/images/popup-4.png" alt="The checkboxes are linked: unticking credential fill unticks auto sign-in and greys out the sub-box" width="100%"></p>
<p align="center"><img src="docs/images/popup-5.png" alt="Step 4: minimum confidence, Save and the status line" width="100%"></p>

</details>

With only the first box ticked you get this, and the last click is yours:

<p align="center">
  <img src="docs/images/fill-only.png" alt="Login form with User ID, password and captcha filled, the LOGIN button highlighted as the user's click" width="100%">
</p>

With auto sign-in on, opening the page is enough: the extension reads the captcha, fills the form and presses LOGIN by itself. Signing in needs a real account, so this is shown as console output from a test run on a local stand-in page (not the real site):

<p align="center">
  <img src="docs/images/signin.png" alt="Console lines of an automatic sign-in: page load, captcha pasted, Auto-login signing in" width="100%">
</p>

> [!IMPORTANT]
> The password is stored **unencrypted** in the extension's local storage on this machine (never synced). Do not use auto sign-in on a shared computer. Details in [Security](#security).

<details>
<summary><b>Update, remove, build the zip yourself</b></summary>

- **Update:** replace the contents of the folder with the new release, then press the circular arrow on the extension's card in `chrome://extensions`.
- **Remove:** `chrome://extensions`, **Remove**. This also deletes the saved password. **Clear** in the popup removes only the credentials.
- **Build the zip yourself:** `./build_zip.sh` writes `dist/captcha-paster-<version>.zip` ([DEVELOPMENT.md](docs/DEVELOPMENT.md)).

</details>

---

## Overview

The login page shows a 150x45 captcha of five characters. The extension takes that image, cleans it, and feeds it to a 1.8-million-weight convolutional network that runs in WebAssembly **inside the extension itself**. The answer is typed into the captcha box in a fraction of a second.

- **Nothing leaves your computer.** No server, no API, no Python, no native helper. The extension makes no network requests of its own.
- **Works in any Chromium browser** (Chrome, Edge, Brave). The screenshots were made with Chromium 145; Windows and Linux are untested here (the code has nothing platform-specific).
- **Optional auto-login** with safety guards that keep it from burning login attempts ([Usage](#usage)).
- **Learns from its mistakes.** A captcha the site rejects is saved as a PNG for the next training round.
- **A reproducible training workspace** is in this repository: data tools, notebooks, the export script and a check that the browser output equals the PyTorch output ([Development](#development)).

```mermaid
flowchart LR
    A["Login page<br/>#imgCaptcha (150x45)"] -->|"canvas pixels"| B["content.js"]
    B -->|"sendMessage<br/>{action: solve}"| C["background.js<br/>(service worker)"]
    C --> D["clean()<br/>letters 0, blobs 128, paper 255"]
    D --> E["CNN in model.wasm<br/>weights from model/"]
    E -->|"text + confidence"| B
    B -->|"types the read"| F["#txtCaptchaInput"]
    B -->|"if allowed:<br/>fill login, press LOGIN"| G["#Submit"]
    B -.->|"'Invalid CAPTCHA' after LOGIN"| H["Downloads/captcha_mistakes/*.png"]
    style A fill:#fff,stroke:#007467
    style E fill:#007467,color:#fff,stroke:none
    style H fill:#fff4d6,stroke:#e0b64a
```

| Model | Style it was trained for | Hand-checked gold | Site rejections |
|---|---|---|---|
| **v5** (extensions 5.3 to 5.5) | style 3, the current captcha | **200/200** | **8/8** |

<p align="center">
  <img src="docs/images/accuracy.png" alt="Bar chart of the gold accuracy of the shipped model: 93.4 percent, 98.5, 97.0 and 100 percent" width="100%">
</p>

---

## Usage

### Every refresh is read

<p align="center">
  <img src="docs/images/refresh.gif" alt="Pressing Refresh four times: each new captcha is read and typed in" width="100%">
</p>

<details>
<summary><b>The four captchas as still pictures</b></summary>

<p align="center"><img src="docs/images/refresh-1.png" alt="First captcha read" width="100%"></p>
<p align="center"><img src="docs/images/refresh-2.png" alt="Second captcha read after Refresh" width="100%"></p>
<p align="center"><img src="docs/images/refresh-3.png" alt="Third captcha read after Refresh" width="100%"></p>
<p align="center"><img src="docs/images/refresh-4.png" alt="Fourth captcha read after Refresh" width="100%"></p>

</details>

### When does auto sign-in press LOGIN?

Pressing LOGIN is the risky part, because the extension assumes the site locks a User ID after 5 failed logins (see [Known limits](#known-limits)). So the extension decides on every page load, using what it can see:

| How the page was opened | Signs in? |
|---|---|
| Typed address, bookmark, link from another site | **Yes**, if auto sign-in is on |
| Arrived from a `gitam.edu` page (logout, session timeout) | Only with **Also sign in after logging out** |
| Reload, back/forward, restored tab | **Never** |
| Site said "Invalid CAPTCHA" after a press | One automatic retry (at most 2 presses per tab) |

In every case the credentials and captcha are still filled. These are real console lines from the shipped extension, from a test run against a local stand-in page (a real sign-in needs a real account):

<p align="center">
  <img src="docs/images/rules.png" alt="Four columns of console output for: typed address signs in, reload fills only, logout with the sub-box off fills only, logout with the sub-box on signs in" width="100%">
</p>

The full decision, taken from `content.js`:

```mermaid
flowchart TD
    L(["Login page loaded"]) --> M{"Message on the page<br/>(#lblmessage)?"}
    M -- "none" --> K{"How was it opened?"}
    K -- "typed, bookmark, link" --> OK1["Auto sign-in allowed"]
    K -- "from a gitam.edu page" --> S{"'Also sign in<br/>after logging out' on?"}
    S -- yes --> OK1
    S -- no --> FILL["Fill only: you press LOGIN"]
    K -- "reload, back/forward" --> FILL
    M -- "Invalid CAPTCHA" --> R{"Already pressed<br/>2 times in this tab?"}
    R -- no --> OK1
    R -- yes --> STOP1["Stop for this tab"]
    M -- "anything else<br/>(wrong password, locked ...)" --> STOP2["Stop for this tab,<br/>password box stays empty"]
    OK1 --> G{"Guards all pass?"}
    G -- "credentials saved, no rate-limit break,<br/>no reCAPTCHA, box still holds the model's read,<br/>confidence at or above the minimum" --> GO(["Press LOGIN (a real click)"])
    G -- "any guard fails" --> FILL
    style GO fill:#30d158,color:#0b1220,stroke:none
    style STOP1 fill:#ffe3e0,stroke:#e5251b
    style STOP2 fill:#ffe3e0,stroke:#e5251b
```

### When the site rejects a read

If you press LOGIN (or auto sign-in does) with the model's read unchanged and the reloaded page says "Invalid CAPTCHA", the captcha is saved to `Downloads/captcha_mistakes/<time>_model-<read>_conf-<confidence>.png` (time in UTC). A wrong password, a successful login or a code you retyped saves nothing. The right answer is unknown: the file name only says what the model read.

<p align="center">
  <img src="docs/images/reject.png" alt="Console lines: Invalid CAPTCHA, one automatic retry, rejected again, auto-login paused; the two saved file names and the two captchas" width="100%">
</p>

In this test run the local stand-in page rejects every read on purpose, even correct ones, to show the retry limit and the saving. The saved images are what the next training round uses ([TRAINING.md](docs/TRAINING.md#next-round-6)). A browser extension may only write under Downloads, so they land there first.

---

## How it works

### 1. Clean the image

The captcha has red letters over gray speckle and blobs. The extension turns each pixel into one of three levels, exactly as training did (`extension/model.js` `clean()` equals `scripts/prep.py` `clean()`):

```math
\text{pixel} =
\begin{cases}
0 & \text{if } r-g > 60 \text{ and } r-b > 60 \quad (\text{letter})\\
128 & \text{else if } r+g+b < 600 \quad (\text{blob})\\
255 & \text{otherwise} \quad (\text{paper})
\end{cases}
```

Keeping the blobs matters: a stroke hidden under a blob then looks different from no stroke, which is what separates the new bar-less **J** from a **3**.

<p align="center">
  <img src="docs/images/cleaning.gif" alt="Three captchas shown raw, letters only with holes where blobs were, and the three-level cleaning the model reads" width="100%">
</p>

### 2. Read five characters

```mermaid
flowchart LR
    I["1 x 45 x 150<br/>image"] --> B1["Block 1<br/>32 ch"] --> B2["Block 2<br/>64 ch"] --> B3["Block 3<br/>128 ch"] --> B4["Block 4<br/>192 ch"] --> M["mean over height<br/>1,728 values"] --> L["Linear 512"] --> H["5 heads,<br/>37 classes each"]
```

<p align="center">
  <img src="docs/images/network.svg" alt="The network: four convolution blocks, mean over height, a 512 unit layer and five heads of 37 classes" width="100%">
</p>

Each block is two 3x3 convolutions with ReLU and a 2x2 max-pool. BatchNorm is folded into the convolutions when the model is exported (`export_model.py`), so the browser needs only convolution, ReLU, max-pool and a linear layer, written as small WebAssembly SIMD kernels (`extension/model.wasm`). The alphabet has 37 case-sensitive characters, `2345689ABDEFGHJLMNQRTYabdefghijmnqrty` (the site never uses `0 O 1 l I 7`).

<p align="center">
  <img src="docs/images/reading.png" alt="For each of the five positions the three most likely characters and their probabilities, with the weakest position marked" width="100%">
</p>

The **confidence** shown in the console is the lowest of the five winning probabilities:

```math
\text{confidence} = \min_{k=1,\dots,5} \; \max_{j} \; \operatorname{softmax}(z_k)_j
```

so one doubtful character is enough to bring it down. (Training uses label smoothing 0.1, which is why a sure read tops out around 0.9 to 0.95, not 1.)

### 3. Where the model came from

The site changed its captcha twice in two days, and each change needed new data and a new model.

<p align="center">
  <img src="docs/images/styles.png" alt="Four gold captchas of each of the three styles, with the true label under each" width="100%">
</p>

```mermaid
flowchart LR
    Z[("100k captchas<br/>data/captchas.zip")] --> V["Apple Vision reads<br/>(label_vision.py)"]
    Z --> T["Teacher model reads<br/>(relabel.py)"]
    V --> C{"Teacher and Vision agree,<br/>or teacher is sure (>= 0.7)?"}
    T --> C
    C -- yes --> TR["Train from scratch<br/>96,894 labels"]
    R["88 hand-labelled hard cases<br/>(reviews.json)"] --> TR
    TR --> G{"200 hand-checked gold<br/>never trained on"}
    G --> X["export_model.py<br/>then check_extension.py:<br/>browser == PyTorch"]
    X --> S(["Ship in the extension"])
```

Gold is the only fair score: it is never trained on, relabelled or reviewed. The whole story, with training settings and test sets, is in [docs/CHANGELOG.md](docs/CHANGELOG.md); the recipe is in [docs/TRAINING.md](docs/TRAINING.md).

---

## Security

What the code does, checked against `extension/`:

| Property | How |
|---|---|
| **No network of its own** | The only `fetch` calls load the extension's own model files via `chrome.runtime.getURL`. There is no remote code, and no analytics. |
| **Narrow reach** | Permissions are `storage` and `downloads` only. The content script runs only on `*://login.gitam.edu/*`. |
| **Strict CSP** | Extension pages allow `script-src 'self' 'wasm-unsafe-eval'` (the WebAssembly kernels) and nothing else. |
| **Credentials** | Stored in `chrome.storage.local` on this machine: never synced to a browser account, never sent anywhere except by placing them in the login form, which is submitted by the page itself. **Not encrypted.** |
| **No credentials in the repository** | The settings form starts empty. |
| **Saved files are validated** | Only a PNG data URL, a 5-character alphanumeric read and a confidence between 0 and 1 are accepted, and the file always goes to `Downloads/captcha_mistakes/`. |
| **Lockout guards** | No retry after a wrong password, at most 2 presses per tab, nothing during a rate-limit break, nothing when Google reCAPTCHA is shown, nothing when the box no longer holds the model's read, nothing below the confidence minimum. |

> [!WARNING]
> The guards count per tab and start again whenever the login page is opened without a message. If the saved password is wrong, **every fresh open of the login page signs in once more** and costs one failed login. Correct the password (or untick auto sign-in) after the first failure.

> [!NOTE]
> This is a convenience tool for signing in to **your own** account. Whether using it is allowed under the site's terms is your responsibility.

---

## Known limits

- **Release 5.5 presses LOGIN on empty fields** when auto sign-in is on (the default on a fresh install) and no credentials are saved yet. The fix is in the source (`extension/content.js`, see the "Unreleased" entry in the [changelog](docs/CHANGELOG.md)) but not in a published zip. Until a new version ships, save your credentials first or untick both boxes.
- **A style change breaks it.** The model reads the current captcha style. If the site changes the captcha again, accuracy drops until a new round is trained ([TRAINING.md](docs/TRAINING.md#new-captcha-style)).
- **Confident misses exist.** v5 still rejects some captchas that it reads with confidence 0.90 to 0.93 (the project's own earlier notes), so the confidence minimum cannot catch them. Each costs one login attempt; auto sign-in retries once. The weakest known pair is **8 read as B**.
- **Hard-coded page.** It looks for the element ids `imgCaptcha`, `txtCaptchaInput`, `txtusername`, `password`, `Submit`, `lblmessage`. If the site renames them the console says `Captcha elements not found`.
- **No Google reCAPTCHA.** If the login shows reCAPTCHA instead of the image, auto sign-in does nothing.
- **The 5-attempt lockout is an assumption** taken from how the site behaved for the author; it is not in this repository and was not verified here.
- **What was and was not tested.** The model was tested against 200 hand-checked captchas and 8 real rejections, in Node against PyTorch. The extension flows (fill, auto sign-in, the rules, the rejected-captcha saving) were tested end to end in Chromium 145 against a **local stand-in page** (the real login page was only opened read-only, never signed in to). Signing in, the rules and the rejected-captcha saving were therefore not run on the live site, and Windows, Linux, Edge and Brave were not tested here.
- **Chromium only.** There is no Firefox or Safari build (a Safari port exists only for the old captchas, in `archive/`).

---

## Development

Everything is in the repository: the extension, the training notebooks, the data tools and the export script. The one check that matters runs the checkpoint through the extension's own `model.js` and `model.wasm` and through PyTorch, and fails unless all 208 reads match:

```sh
pip install -r requirements.txt        # torch, numpy, Pillow, jupyter, matplotlib, tqdm
python3 tools/check_extension.py       # JS == PyTorch on 208/208, gold 200/200, site 8/8
```

It needs `node` and the git-ignored `data/captchas.zip`. Shipping a new model, releasing, and rebuilding the pictures in this README are in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

<details>
<summary><b>Repository layout</b></summary>

| Path | What |
|---|---|
| `extension/` | The extension. Load unpacked from here. |
| `models/` | `captcha_cnn_v5.pt` (shipped) and its teacher `captcha_cnn_v4_ft.pt`. |
| `notebooks/`, `scripts/`, `tools/` | Training round, data tools, pre-ship check, README picture scripts. |
| `data/` | Gold set, reviews, labels, the 8 rejected captchas. The captcha zip is git-ignored. |
| `docs/` | Changelog, training and development guides, pictures. |
| `archive/` | Frozen earlier work (older styles, Vision and native-host versions). |

</details>

---

## Documentation map

| Document | What is in it |
|---|---|
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Every extension version: what changed, why, settings, how it was tested. |
| [docs/TRAINING.md](docs/TRAINING.md) | Data, labelling, the next training round, rules that keep scores meaningful. |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Layout, checks, shipping, releasing, rebuilding the pictures. |
| [extension/README.txt](extension/README.txt) | The text that ships inside the zip. |
| [archive/README.md](archive/README.md) | Index of the frozen snapshots. |
