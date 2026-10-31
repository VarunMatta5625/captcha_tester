// Reads the captcha, has the model (in background.js) solve it, fills the answer. Re-runs on every new captcha.
// When the site rejects a code the model read, saves that captcha (Downloads/captcha_mistakes/) for retraining.
const img = document.getElementById('imgCaptcha');
const input = document.getElementById('txtCaptchaInput');
let latest = 0; // only the newest captcha's answer gets pasted
let modelRead = null; // { code, confidence } the model pasted for the captcha on screen, null while reading or unsure

const W = 150, H = 45; // the model's input size (model/model.json)
const SUBMITTED_KEY = 'captchaPasterSubmitted'; // sessionStorage: the submitted captcha, kept across the login POST

function imagePixels() {
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, W, H); // the site's captchas are already 150x45, so this is a straight copy
  return Array.from(ctx.getImageData(0, 0, W, H).data);
}

function imagePng() {
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  canvas.getContext('2d').drawImage(img, 0, 0);
  return canvas.toDataURL('image/png');
}

async function solve() {
  const id = ++latest;
  modelRead = null;
  const started = performance.now();
  const reply = await chrome.runtime.sendMessage({ action: 'solve', rgba: imagePixels() });
  if (id !== latest) return;
  if (reply.error) {
    console.error('[CAPTCHA] Model error:', reply.error);
  } else if (reply.code) {
    input.value = reply.code;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    modelRead = { code: reply.code, confidence: reply.confidence };
    console.log(`[CAPTCHA] Pasted ${reply.code} (confidence ${reply.confidence}, ` +
      `model ${reply.ms} ms, total ${Math.round(performance.now() - started)} ms)`);
  } else {
    console.warn(`[CAPTCHA] Unsure (read "${reply.raw}"), left empty.`);
  }
}

// LOGIN pressed with the model's read unchanged: remember the captcha, in case the server rejects it.
// (If the code was retyped, a rejection says nothing about the model.)
function rememberSubmitted(event) {
  sessionStorage.removeItem(SUBMITTED_KEY);
  if (event.submitter?.id !== 'Submit' || !modelRead || input.value.trim() !== modelRead.code) return;
  try {
    sessionStorage.setItem(SUBMITTED_KEY, JSON.stringify({ png: imagePng(), ...modelRead }));
  } catch (e) {
    console.warn('[CAPTCHA] Could not keep the submitted captcha:', e);
  }
}

// After the login POST the site reloads the login page (new captcha, password cleared) with
// "Invalid CAPTCHA. Please try again (the code is case-sensitive)." when the code was wrong: save the misread
// captcha. Any other message (wrong password etc.) means the model's read was fine.
async function saveIfRejected(submitted) {
  const message = document.getElementById('lblmessage')?.textContent ?? '';
  if (!/captcha/i.test(message)) return;
  const reply = await chrome.runtime.sendMessage({ action: 'saveMistake', ...JSON.parse(submitted) });
  if (reply?.error) console.error('[CAPTCHA] Could not save the misread captcha:', reply.error);
  else console.log(`[CAPTCHA] Site rejected the model's read, saved ${reply.filename}`);
}

// read before the element check, so a successful login's page also clears it
const submitted = sessionStorage.getItem(SUBMITTED_KEY);
sessionStorage.removeItem(SUBMITTED_KEY);

if (!img || !input) {
  console.warn('[CAPTCHA] Captcha elements not found.');
} else {
  if (submitted) saveIfRejected(submitted);
  input.form?.addEventListener('submit', rememberSubmitted);
  img.addEventListener('load', solve); // fires for every refresh, however it is triggered
  if (img.complete && img.naturalWidth) solve();
}
