// Reads captchas with the trained CNN (model.js + model.wasm + model/). Runs entirely inside the extension:
// no native host, no Python, same on macOS, Linux and Windows.
importScripts('model.js'); // createModel, readCaptcha, toGray

let modelPromise = null;

function getModel() {
  modelPromise ??= Promise.all([
    fetch(chrome.runtime.getURL('model/model.json')).then((r) => r.json()),
    fetch(chrome.runtime.getURL('model/weights.bin')).then((r) => r.arrayBuffer()),
    fetch(chrome.runtime.getURL('model.wasm')).then((r) => r.arrayBuffer()),
  ]).then(([meta, weights, wasm]) => createModel(meta, weights, wasm));
  return modelPromise;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action !== 'solve') return;
  getModel()
    .then((model) => {
      const n = model.width * model.height;
      if (message.rgba.length !== 4 * n) throw new Error(`expected ${model.width}x${model.height} pixels`);
      const start = performance.now();
      const { text, confidence } = readCaptcha(model, toGray(message.rgba, n));
      sendResponse({ code: text, raw: text, confidence: Math.round(confidence * 1000) / 1000,
                     ms: Math.round(performance.now() - start) });
    })
    .catch((e) => {
      modelPromise = null; // retry loading next time
      sendResponse({ error: String(e) });
    });
  return true; // keeps the channel open for async response
});
