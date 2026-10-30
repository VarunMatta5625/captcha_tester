"""Chrome native messaging host: captcha PNG (data URL) in, Vision reading out."""
import base64, io

import numpy as np
from PIL import Image

from native_messaging import serve
from pipeline import solve


def handle(msg):
    png = base64.b64decode(msg["image"].split(",", 1)[1])
    a = np.array(Image.open(io.BytesIO(png)).convert("L"))   # same load as the notebook
    code, raw = solve(a)
    return {"code": code, "raw": raw}


if __name__ == "__main__":
    serve(handle)
