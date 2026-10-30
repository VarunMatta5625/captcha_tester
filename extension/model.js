// The trained captcha CNN. Layer order comes from model/model.json, weights from model/weights.bin
// (both from export_model.py, BatchNorm folded in); the number crunching runs in model.wasm
// (wasm/kernels.c, WebAssembly + SIMD). No libraries, works in any Chrome.

// canvas RGBA pixels -> letters only, exactly like training's prep.ink (scripts/prep.py): the captcha's letters
// are red and its speckle noise gray, so a pixel is letter (0) when red beats green and blue by more than 60,
// else paper (255)
const RED_MIN = 60;
export function toInk(rgba, n) {
  const gray = new Uint8Array(n);
  for (let p = 0; p < n; p++) {
    const r = rgba[4 * p], g = rgba[4 * p + 1], b = rgba[4 * p + 2];
    gray[p] = r - g > RED_MIN && r - b > RED_MIN ? 0 : 255;
  }
  return gray;
}

export async function createModel(meta, weights, wasmBytes) {
  const { instance } = await WebAssembly.instantiate(wasmBytes, {});
  const k = instance.exports;
  k._initialize();
  const wPtr = k.alloc(weights.byteLength);
  new Uint8Array(k.memory.buffer, wPtr, weights.byteLength).set(new Uint8Array(weights));
  const at = (t) => wPtr + 4 * t.offset;   // byte address of a weight tensor

  // two activation buffers, each big enough for the largest layer output
  let c = 1, h = meta.height, w = meta.width, biggest = h * w;
  for (const l of meta.layers) {
    if (l.type === 'conv3x3_relu') c = l.weight.shape[0];
    else if (l.type === 'maxpool2') { h >>= 1; w >>= 1; }
    biggest = Math.max(biggest, c * h * w);
  }
  const bufA = k.alloc(4 * biggest), bufB = k.alloc(4 * biggest);
  return { ...meta, k, at, bufA, bufB };
}

// gray: Uint8Array of model.height * model.width pixels -> { text, confidence of weakest character }
export function readCaptcha(model, gray) {
  const { k, at } = model;
  const mem = new Float32Array(k.memory.buffer);
  let src = model.bufA, dst = model.bufB;
  const swap = () => { [src, dst] = [dst, src]; };
  for (let p = 0; p < gray.length; p++) mem[src / 4 + p] = 1 - gray[p] / 255;   // ink = 1, paper = 0

  let c = 1, h = model.height, w = model.width, len = 0;
  for (const l of model.layers) {
    if (l.type === 'conv3x3_relu') {
      const outC = l.weight.shape[0];
      k.conv3x3_relu(src, c, h, w, at(l.weight), at(l.bias), outC, dst);
      c = outC;
    } else if (l.type === 'maxpool2') {
      k.maxpool2(src, c, h, w, dst);
      h >>= 1; w >>= 1;
    } else if (l.type === 'mean_height') {
      k.mean_height(src, c, h, w, dst);
      len = c * w;
    } else if (l.type === 'linear_relu') {
      const n = l.bias.shape[0];
      k.linear(src, len, at(l.weight), at(l.bias), n, 1, dst);
      len = n;
    }
    swap();
  }

  let text = '', confidence = 1;
  for (const head of model.heads) {
    const n = head.bias.shape[0];
    k.linear(src, len, at(head.weight), at(head.bias), n, 0, dst);
    const logits = mem.subarray(dst / 4, dst / 4 + n);
    let best = 0;
    for (let j = 1; j < n; j++) if (logits[j] > logits[best]) best = j;
    let sum = 0;
    for (let j = 0; j < n; j++) sum += Math.exp(logits[j] - logits[best]);
    text += model.alphabet[best];
    confidence = Math.min(confidence, 1 / sum);   // softmax probability of the chosen character
  }
  return { text, confidence };
}
