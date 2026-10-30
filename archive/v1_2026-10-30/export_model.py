"""Export a trained captcha CNN checkpoint for the extension's JavaScript runtime.

    python3 export_model.py [checkpoint.pt]      (default: host/captcha_cnn.pt)

Writes extension/model/model.json (layer list, alphabet) and extension/model/weights.bin
(float32, little-endian). BatchNorm layers are folded into the conv before them, so the
JavaScript only needs conv + ReLU + max-pool + linear. Re-run after training a better model,
then reload the extension (or rebuild the zip with build_zip.sh).
"""
import json, os, sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "extension", "model")
BN_EPS = 1e-5   # PyTorch BatchNorm2d default, used in training


def main(path):
    ckpt = torch.load(path, map_location="cpu")
    sd = {k: v.double().numpy() for k, v in ckpt["state_dict"].items() if not k.endswith("num_batches_tracked")}
    layers, blobs, offset = [], [], 0

    def add(name, arr):
        nonlocal offset
        arr = np.ascontiguousarray(arr, dtype="<f4")
        blobs.append(arr.tobytes())
        entry = {"name": name, "shape": list(arr.shape), "offset": offset}
        offset += arr.size
        return entry

    # features: per block [conv, bn, relu, conv, bn, relu, maxpool] -> Sequential indices 7b .. 7b+6
    for b in range(len(ckpt["widths"])):
        for conv, bn in ((7 * b, 7 * b + 1), (7 * b + 3, 7 * b + 4)):
            w = sd[f"features.{conv}.weight"]
            scale = sd[f"features.{bn}.weight"] / np.sqrt(sd[f"features.{bn}.running_var"] + BN_EPS)
            bias = sd[f"features.{bn}.bias"] - sd[f"features.{bn}.running_mean"] * scale
            layers.append({"type": "conv3x3_relu",
                           "weight": add(f"conv{conv}.w", w * scale[:, None, None, None]),
                           "bias": add(f"conv{conv}.b", bias)})
        layers.append({"type": "maxpool2"})
    layers.append({"type": "mean_height"})
    layers.append({"type": "linear_relu", "weight": add("shared.w", sd["shared.2.weight"]),
                   "bias": add("shared.b", sd["shared.2.bias"])})
    heads = [{"weight": add(f"head{k}.w", sd[f"heads.{k}.weight"]), "bias": add(f"head{k}.b", sd[f"heads.{k}.bias"])}
             for k in range(ckpt["length"])]

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "weights.bin"), "wb") as f:
        f.write(b"".join(blobs))
    h, w = ckpt["image_size"]
    meta = {"alphabet": ckpt["alphabet"], "length": ckpt["length"], "height": h, "width": w,
            "layers": layers, "heads": heads, "floats": offset,
            "source": os.path.basename(path), "scores": ckpt.get("scores", {})}
    with open(os.path.join(OUT, "model.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"exported {os.path.basename(path)}: {offset} weights ({offset * 4 / 1e6:.1f} MB) -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "host", "captcha_cnn.pt"))
