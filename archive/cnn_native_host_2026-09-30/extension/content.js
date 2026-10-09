// Reads the captcha, has the local model host solve it, fills the answer. Re-runs on every new captcha.
const img = document.getElementById('imgCaptcha');
const input = document.getElementById('txtCaptchaInput');
let latest = 0; // only the newest captcha's answer gets pasted

function imageDataUrl() {
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  canvas.getContext('2d').drawImage(img, 0, 0);
  return canvas.toDataURL('image/png');
}

async function solve() {
  const id = ++latest;
  const reply = await chrome.runtime.sendMessage({ action: 'solve', image: imageDataUrl() });
  if (id !== latest) return;
  if (reply.error) {
    console.error('[CAPTCHA] Host error:', reply.error);
  } else if (reply.code) {
    input.value = reply.code;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    console.log(`[CAPTCHA] Pasted ${reply.code}` +
      (reply.confidence !== undefined ? ` (confidence ${reply.confidence})` : ''));
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
