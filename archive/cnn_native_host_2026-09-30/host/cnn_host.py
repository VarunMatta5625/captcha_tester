"""Chrome native messaging host: captcha PNG (data URL) in, trained CNN's reading out."""
import base64, io

from PIL import Image

import cnn
from native_messaging import serve

model, ckpt = cnn.load()


def handle(msg):
    png = base64.b64decode(msg["image"].split(",", 1)[1])
    text, confidence = cnn.read(model, ckpt, Image.open(io.BytesIO(png)))
    return {"code": text, "raw": text, "confidence": round(confidence, 3)}


if __name__ == "__main__":
    serve(handle)
