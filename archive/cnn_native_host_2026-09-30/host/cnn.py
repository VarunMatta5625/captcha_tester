"""The captcha CNN from the training notebook, for reading captchas in the native host.

CaptchaCNN must stay layer-for-layer identical to the notebook's, or the saved weights won't load.
Input is the raw captcha (no cleanup): grayscale, x = 1 - pixel/255 so ink = 1, paper = 0.
"""
import os

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "captcha_cnn.pt")   # copy of the notebook's best checkpoint


class CaptchaCNN(nn.Module):
    def __init__(self, n_classes, length, widths, dropout, image_width):
        super().__init__()
        layers, c_in = [], 1
        for c in widths:   # each block halves H and W: 45x150 -> 2x9
            layers += [
                nn.Conv2d(c_in, c, 3, padding=1, bias=False), nn.BatchNorm2d(c), nn.ReLU(inplace=True),
                nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c), nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            ]
            c_in = c
        self.features = nn.Sequential(*layers)
        n_cols = image_width // 2 ** len(widths)
        self.shared = nn.Sequential(nn.Flatten(), nn.Dropout(dropout),
                                    nn.Linear(c_in * n_cols, 512), nn.ReLU(inplace=True), nn.Dropout(dropout))
        self.heads = nn.ModuleList(nn.Linear(512, n_classes) for _ in range(length))

    def forward(self, x):
        z = self.features(x).mean(dim=2)
        z = self.shared(z)
        return torch.stack([head(z) for head in self.heads], dim=1)


def load(path=MODEL):
    """-> (model in eval mode on CPU, checkpoint dict)."""
    ckpt = torch.load(path, map_location="cpu")
    h, w = ckpt["image_size"]
    model = CaptchaCNN(len(ckpt["alphabet"]), ckpt["length"], ckpt["widths"],
                       ckpt["config"]["dropout"], w)
    model.load_state_dict(ckpt["state_dict"])
    return model.eval(), ckpt


@torch.no_grad()
def read(model, ckpt, image):
    """PIL image -> (text, confidence of the weakest character)."""
    h, w = ckpt["image_size"]
    gray = image.convert("L")
    if gray.size != (w, h):   # the site's captchas are 150x45; resize anything else to fit
        gray = gray.resize((w, h), Image.BILINEAR)
    x = 1 - torch.from_numpy(np.array(gray)).float() / 255
    probs = model(x[None, None]).softmax(-1)[0]   # (length, n_classes)
    conf, idx = probs.max(-1)
    return "".join(ckpt["alphabet"][i] for i in idx.tolist()), conf.min().item()
