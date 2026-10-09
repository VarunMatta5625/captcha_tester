"""Chrome native messaging host: captcha PNG (data URL) in, Vision reading out.

Chrome frames every message as a 4-byte native-endian length followed by UTF-8 JSON,
on stdin (requests) and stdout (replies). stdout must carry nothing else.
"""
import base64, io, json, struct, sys, traceback

import numpy as np
from PIL import Image

from pipeline import solve


def read_message():
    header = sys.stdin.buffer.read(4)
    if len(header) < 4:
        return None   # Chrome closed the pipe
    (length,) = struct.unpack("=I", header)
    return json.loads(sys.stdin.buffer.read(length))

def send_message(msg):
    body = json.dumps(msg).encode()
    sys.stdout.buffer.write(struct.pack("=I", len(body)) + body)
    sys.stdout.buffer.flush()

def handle(msg):
    png = base64.b64decode(msg["image"].split(",", 1)[1])
    a = np.array(Image.open(io.BytesIO(png)).convert("L"))   # same load as the notebook
    code, raw = solve(a)
    return {"code": code, "raw": raw}

def main():
    while (msg := read_message()) is not None:
        try:
            send_message(handle(msg))
        except Exception as e:
            traceback.print_exc(file=sys.stderr)   # launcher sends stderr to ~/Library/Logs/captcha-paster-host.log
            send_message({"error": f"{type(e).__name__}: {e}"})

if __name__ == "__main__":
    main()
