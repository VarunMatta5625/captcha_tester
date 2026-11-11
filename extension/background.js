// Reads captchas with the trained CNN (model.js + model.wasm + model/). Runs entirely inside the extension:
// no native host, no Python, same on macOS, Linux and Windows.
import { clean, createModel, readCaptcha } from './model.js';

let modelPromise = null;

function getModel() {
  modelPromise ??= Promise.all([
    fetch(chrome.runtime.getURL('model/model.json')).then((r) => r.json()),
    fetch(chrome.runtime.getURL('model/weights.bin')).then((r) => r.arrayBuffer()),
    fetch(chrome.runtime.getURL('model.wasm')).then((r) => r.arrayBuffer()),
  ]).then(([meta, weights, wasm]) => createModel(meta, weights, wasm));
  return modelPromise;
}

// A captcha the site rejected the model's read for -> Downloads/captcha_mistakes/
// <time>_model-<read>_conf-<confidence>.png (the right answer is unknown; label it later)
function saveMistake({ png, code, confidence }) {
  if (!png?.startsWith('data:image/png;base64,') || !/^[A-Za-z0-9]{5}$/.test(code) ||
      !(confidence >= 0 && confidence <= 1)) {
    return Promise.reject(new Error('bad captcha or code'));
  }
  const time = new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15); // 20261031-142530
  const filename = `captcha_mistakes/${time}_model-${code}_conf-${confidence.toFixed(3)}.png`;
  return chrome.downloads.download({ url: png, filename, conflictAction: 'uniquify', saveAs: false })
    .then(() => ({ filename }));
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'saveMistake') {
    saveMistake(message).then(sendResponse, (e) => sendResponse({ error: String(e) }));
    return true;
  }
  if (message.action !== 'solve') return;
  getModel()
    .then((model) => {
      const n = model.width * model.height;
      if (message.rgba.length !== 4 * n) throw new Error(`expected ${model.width}x${model.height} pixels`);
      const start = performance.now();
      const { text, confidence } = readCaptcha(model, clean(message.rgba, n, model.levels));
      sendResponse({ code: text, confidence: Math.round(confidence * 1000) / 1000,
                     ms: Math.round(performance.now() - start) });
    })
    .catch((e) => {
      modelPromise = null; // retry loading next time
      sendResponse({ error: String(e) });
    });
  return true; // keeps the channel open for async response
});
