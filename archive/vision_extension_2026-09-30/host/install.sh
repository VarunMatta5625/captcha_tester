#!/bin/bash
# Registers host/vision_host.py with Chrome as native messaging host "com.captcha_paster.vision".
#
#   ./install.sh               extension ID computed from the extension/ folder's path
#   ./install.sh <extension-id> use the ID shown in chrome://extensions instead
#
# The host runs straight from this folder, so code edits and new reviews apply without
# re-running this. Re-run only after moving the project or switching Python.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
EXT_DIR="$(dirname "$HERE")/extension"
NAME="com.captcha_paster.vision"
TARGET="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
LOG="$HOME/Library/Logs/captcha-paster-host.log"   # host stderr; Chrome discards it otherwise

# Chrome starts hosts with a bare PATH, so pin the python that has numpy/scipy/Pillow
PYTHON="$(command -v python3)"
"$PYTHON" -c "import numpy, scipy, PIL" || { echo "python3 ($PYTHON) lacks numpy/scipy/Pillow"; exit 1; }

# unpacked extension ID = first 32 hex chars of sha256(absolute path), digits 0-f mapped to a-p
EXT_ID="${1:-$(printf '%s' "$EXT_DIR" | shasum -a 256 | head -c 32 | tr '0-9a-f' 'a-p')}"

LAUNCHER="$HERE/vision_host"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
exec "$PYTHON" -B "$HERE/vision_host.py" 2>> "$LOG"
EOF
chmod +x "$LAUNCHER"

mkdir -p "$TARGET"
cat > "$TARGET/$NAME.json" <<EOF
{
  "name": "$NAME",
  "description": "Captcha cleanup + Apple Vision OCR",
  "path": "$LAUNCHER",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXT_ID/"]
}
EOF

echo "Host registered for extension $EXT_ID (log: $LOG)"
echo "Load $EXT_DIR in chrome://extensions and check the ID matches; if not, run: $0 <real-id>"
