# safari/

Safari port of the extension (v4.1, same model as `../extension/`).

- `extension-classic-sw/`: copy of `../extension/` with a classic service worker (`importScripts`, no `"type": "module"`) because Safari lacks module workers. Differs from `extension/` ONLY in `background.js`, `manifest.json`, `model.js`. `content.js`, `model.wasm` and `model/` must stay identical.
- `xcode-project/CAPTCHA Paster/`: Xcode project (macOS + iOS app and extension targets). The extension files live in `Shared (Extension)/Resources/` and must equal `extension-classic-sw/`.
- `captcha-paster-4.1.zip`: packaged classic-sw copy.
- `xcode-project/CAPTCHA Paster/build/`: Xcode build output (215 MB, regenerable, safe to delete).

## After any change to `../extension/`
1. Port the change into `extension-classic-sw/` (keep the three differing files in classic-sw form; copy everything else verbatim, including `model/` after a new export).
2. Copy `extension-classic-sw/*` into `xcode-project/CAPTCHA Paster/Shared (Extension)/Resources/`.
3. Bump the version in both manifests and in the Xcode target if shipping.
4. Verify: `for f in content.js model.wasm model/weights.bin model/model.json; do cmp extension/$f safari/extension-classic-sw/$f; done` (no output = in sync).
5. Build and run from Xcode, enable the extension in Safari settings.
