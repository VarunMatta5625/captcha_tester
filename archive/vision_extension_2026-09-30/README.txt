Snapshot of the working Vision-based extension (image cleanup + Apple Vision OCR), taken 2026-09-30
before the extension was switched to the trained CNN.

To use it again instead of the CNN version:
  1. chrome://extensions -> Load unpacked -> this folder's extension/
  2. Terminal: <this folder>/host/install.sh
     (registers the "com.captcha_paster.vision" host for this copy's extension ID)
  3. Remove or disable the CNN version of the extension so both don't fill the box.
