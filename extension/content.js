// CAPTCHA reader + optional auto-login for login.gitam.edu. Misread captchas end up in
// Downloads/captcha_mistakes/ for retraining.
const img = document.getElementById('imgCaptcha');
const input = document.getElementById('txtCaptchaInput');
const userInput = document.getElementById('txtusername');
const passInput = document.getElementById('password');
const submitBtn = document.getElementById('Submit');
let latest = 0; // newest captcha wins
let modelRead = null; // { code, confidence }
let autoSubmitted = false;

const W = 150, H = 45; // the model's input size
const SUBMITTED_KEY = 'captchaPasterSubmitted'; // sessionStorage keeps it across the login POST
const ATTEMPTS_KEY = 'captchaPasterAutoAttempts';
const BLOCKED_KEY = 'captchaPasterAutoBlocked';
const MAX_ATTEMPTS = 2; // first press + one retry after an invalid captcha

const settingsPromise = chrome.storage.local.get({
  autofill: true, // fill the saved User ID and password into the login form
  autoLogin: true, // also press LOGIN; implies autofill
  username: '',
  password: '',
  signInAfterLogout: false, // sub-rule of autoLogin; reloads never sign in
  minConfidence: 0.5,
});

function imagePixels() {
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, W, H); // captchas are already 150x45, a straight copy
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
  } else {
    input.value = reply.code;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    modelRead = { code: reply.code, confidence: reply.confidence };
    console.log(`[CAPTCHA] Pasted ${reply.code} (confidence ${reply.confidence}, ` +
                `model ${reply.ms} ms, total ${Math.round(performance.now() - started)} ms)`);
    maybeAutoSubmit(await settingsPromise);
  }
}

// Keep the submitted captcha around (in the model's read, not a retyped one) for a possible rejection.
function rememberSubmitted(event) {
  sessionStorage.removeItem(SUBMITTED_KEY);
  if (event.submitter?.id !== 'Submit' || !modelRead || input.value.trim() !== modelRead.code) return;
  try {
    sessionStorage.setItem(SUBMITTED_KEY, JSON.stringify({ png: imagePng(), ...modelRead }));
  } catch (e) {
    console.warn('[CAPTCHA] Could not keep the submitted captcha:', e);
  }
}

// A reload whose message mentions the captcha means the model's read was rejected: save that image.
async function saveIfRejected(submitted) {
  const message = document.getElementById('lblmessage')?.textContent ?? '';
  if (!/captcha/i.test(message)) return;
  const reply = await chrome.runtime.sendMessage({ action: 'saveMistake', ...JSON.parse(submitted) });
  if (reply?.error) console.error('[CAPTCHA] Could not save the misread captcha:', reply.error);
  else console.log(`[CAPTCHA] Site rejected the model's read, saved ${reply.filename}`);
}

// ---- auto-login ----

function fill(el, value) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}

function visible(id) {
  const el = document.getElementById(id);
  if (!el) return false;
  return !!el.offsetParent || getComputedStyle(el).position === 'fixed';
}

const pressCount = () => parseInt(sessionStorage.getItem(ATTEMPTS_KEY), 10) || 0; // LOGIN presses in this tab

// What this page load may do, based on the message the last attempt left behind: nothing on a
// wrong password, one retry on an invalid captcha, and a reset when there is no message at all.
// The site blocks a User ID after 5 failed logins, so this stays strictly behind those guards.
function evaluateAutoLoginState(settings) {
  const message = (document.getElementById('lblmessage')?.textContent ?? '').trim();
  const attempts = pressCount();
  if (!message) {
    sessionStorage.removeItem(ATTEMPTS_KEY);
    sessionStorage.removeItem(BLOCKED_KEY);
    const kind = loadKind();
    const allowed = kind === 'open' || (kind === 'internal' && settings.signInAfterLogout);
    if (!allowed) {
      console.log(`[CAPTCHA] Page load kind "${kind}" is not an auto sign-in case: filling only, press LOGIN yourself.`);
    }
    return { allowed, fillPassword: true };
  }
  if (/invalid captcha/i.test(message)) {
    if (attempts >= MAX_ATTEMPTS) {
      console.warn(`[CAPTCHA] Auto-login paused after ${attempts} rejected attempts in this tab, ` +
                   'please check the login.');
      return { allowed: false, fillPassword: true };
    }
    console.log(`[CAPTCHA] Login rejected the captcha, retrying automatically ` +
                `(${attempts + 1} of ${MAX_ATTEMPTS}).`);
    return { allowed: true, fillPassword: true };
  }
  if (!sessionStorage.getItem(BLOCKED_KEY)) {
    sessionStorage.setItem(BLOCKED_KEY, '1');
    console.warn(`[CAPTCHA] Auto-login stopped for this tab: "${message}". ` +
                 'If the saved password changed, update it in the extension options and ' +
                 'reopen the login page (a new tab is cleanest).');
  }
  return { allowed: false, fillPassword: false };
}

// How this page load happened: 'reload' (reload, back/forward, restored tab), 'internal' (arrived from a
// gitam.edu page: logout, session timeout), or 'open' (typed URL, bookmark, link from another site).
function loadKind() {
  const navType = performance.getEntriesByType('navigation')[0]?.type ?? 'navigate';
  let referrerHost = '';
  try { referrerHost = document.referrer ? new URL(document.referrer).hostname : ''; } catch { /* keep empty */ }
  console.log(`[CAPTCHA] Page load: type ${navType}, referrer "${document.referrer}"`);
  if (navType !== 'navigate') return 'reload';
  return /(^|\.)gitam\.edu$/i.test(referrerHost) ? 'internal' : 'open';
}

let autoState = { allowed: false, fillPassword: false }; // decided once at startup

async function fillCredentials() {
  const settings = await settingsPromise;
  autoState = evaluateAutoLoginState(settings); // before any submit: maybeAutoSubmit stays closed until now
  if (!settings.autofill && !settings.autoLogin) return;
  if (!settings.password) {
    console.warn('[CAPTCHA] Credential fill is on but no credentials are saved (extension options).');
    return;
  }
  if (!userInput || !passInput) {
    console.warn('[CAPTCHA] Credential fill skipped: the login fields were not found (site changed?).');
    return;
  }
  fill(userInput, settings.username);
  if (autoState.fillPassword) fill(passInput, settings.password);
  maybeAutoSubmit(settings);
}

// The credential fill and the captcha read happen in either order; this fires only once both are done.
function maybeAutoSubmit(settings) {
  if (!settings.autoLogin || autoSubmitted || !autoState.allowed || !modelRead) return;
  if (!submitBtn || submitBtn.disabled) return;
  if (document.getElementById('lblRateLimit')) return; // rate-limit break active
  if (visible('pnlGoogleCaptcha')) { // model cannot read reCAPTCHA
    console.warn('[CAPTCHA] This login uses Google reCAPTCHA, not auto-submitting.');
    return;
  }
  if (!userInput || !passInput) return;
  if (userInput.value.trim() !== settings.username || passInput.value !== settings.password) return;
  if (input.value.trim() !== modelRead.code) return; // captcha on screen is not the model's read
  if (modelRead.confidence < settings.minConfidence) {
    console.warn(`[CAPTCHA] Confidence ${modelRead.confidence} is below ${settings.minConfidence}, ` +
                 'press LOGIN yourself or lower the minimum on the options page.');
    return;
  }
  autoSubmitted = true;
  const attempts = pressCount() + 1;
  sessionStorage.setItem(ATTEMPTS_KEY, String(attempts));
  console.log('[CAPTCHA] Auto-login: signing in.');
  submitBtn.click(); // real click: the site's validating onclick runs, submitter stays 'Submit'
}

// read before the element check, so the post-login page also clears it
const submitted = sessionStorage.getItem(SUBMITTED_KEY);
sessionStorage.removeItem(SUBMITTED_KEY);

if (!img || !input) {
  console.warn('[CAPTCHA] Captcha elements not found.');
} else {
  if (submitted) saveIfRejected(submitted);
  input.form?.addEventListener('submit', rememberSubmitted);
  img.addEventListener('load', solve); // every refresh
  if (img.complete && img.naturalWidth) solve();
  fillCredentials();
}
