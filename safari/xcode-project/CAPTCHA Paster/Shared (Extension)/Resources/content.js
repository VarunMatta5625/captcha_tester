// Reads the captcha, has the model (in background.js) solve it, fills the answer. Re-runs on every new captcha.
const img = document.getElementById('imgCaptcha');
const input = document.getElementById('txtCaptchaInput');
let latest = 0; // only the newest captcha's answer gets pasted

const W = 150, H = 45; // the model's input size (model/model.json)

function imagePixels() {
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, W, H); // the site's captchas are already 150x45, so this is a straight copy
  return Array.from(ctx.getImageData(0, 0, W, H).data);
}

async function solve() {
  const id = ++latest;
  const started = performance.now();
  const reply = await chrome.runtime.sendMessage({ action: 'solve', rgba: imagePixels() });
  if (id !== latest) return;
  if (reply.error) {
    console.error('[CAPTCHA] Model error:', reply.error);
  } else if (reply.code) {
    input.value = reply.code;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    console.log(`[CAPTCHA] Pasted ${reply.code} (confidence ${reply.confidence}, ` +
      `model ${reply.ms} ms, total ${Math.round(performance.now() - started)} ms)`);
  } else {
    console.warn(`[CAPTCHA] Unsure (read "${reply.raw}"), left empty.`);
  }
}

if (!img || !input) {
  console.warn('[CAPTCHA] Captcha elements not found.');
} else {
  img.addEventListener('load', solve); // fires for every refresh, however it is triggered
  if (img.complete && img.naturalWidth) solve();
}
