// node tools/check_extension.mjs <folder>: the extension's own model.js + model.wasm on <folder>/images.rgba with
// <folder>/model.json + weights.bin; prints {reads, max_conf_diff (vs torch.json), ms} as JSON. Run by check_extension.py.
import { readFileSync } from 'node:fs';
import { clean, createModel, readCaptcha } from '../extension/model.js';

const dir = process.argv[2];
const meta = JSON.parse(readFileSync(`${dir}/model.json`));
const w = readFileSync(`${dir}/weights.bin`);
const wasm = readFileSync(new URL('../extension/model.wasm', import.meta.url));
const torch = JSON.parse(readFileSync(`${dir}/torch.json`));
const all = readFileSync(`${dir}/images.rgba`);

const model = await createModel(meta, w.buffer.slice(w.byteOffset, w.byteOffset + w.length), wasm);
const n = model.width * model.height;
const reads = [];
let maxConfDiff = 0, ms = 0;
for (let k = 0; k < all.length / (4 * n); k++) {
  const t = performance.now();
  const { text, confidence } = readCaptcha(model, clean(all.subarray(4 * n * k, 4 * n * (k + 1)), n, model.levels));
  ms += performance.now() - t;
  reads.push(text);
  maxConfDiff = Math.max(maxConfDiff, Math.abs(confidence - torch.conf[k]));
}
console.log(JSON.stringify({ reads, max_conf_diff: maxConfDiff, ms: ms / reads.length }));
