#!/bin/bash
# Packs extension/ into dist/captcha-paster-<version>.zip, ready to unzip and "Load unpacked"
# in Chrome on any OS. Run after export_model.py whenever the model changes.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VERSION="$(python3 -c "import json; print(json.load(open('$HERE/extension/manifest.json'))['version'])")"
OUT="$HERE/dist/captcha-paster-$VERSION.zip"

mkdir -p "$HERE/dist"
rm -f "$OUT"
# files sit under a captcha-paster/ folder inside the zip, so unzipping gives one clean folder
STAGE="$(mktemp -d)"
cp -R "$HERE/extension" "$STAGE/captcha-paster"
find "$STAGE" -name .DS_Store -delete
(cd "$STAGE" && zip -qr -X "$OUT" captcha-paster)
rm -rf "$STAGE"
echo "built $OUT ($(du -h "$OUT" | cut -f1))"
