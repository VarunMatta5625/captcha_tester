// Shared form for the toolbar popup and the options page. Everything stays in
// chrome.storage.local on this machine; the password is only ever placed into the login form.
const DEFAULTS = { username: '', password: '', autofill: true, autoLogin: true, signInAfterLogout: false, minConfidence: 0.5 };
const $ = (id) => document.getElementById(id);

function setStatus(text, error = false) {
  const el = $('status');
  el.textContent = text;
  el.className = error ? 'error' : 'ok';
}

// Match the login page's own validation (1-16 letters/digits, password 1-20 chars).
function validate() {
  const username = $('username').value.trim();
  const password = $('password').value; // never trimmed: spaces may be part of the password
  if (!/^[A-Za-z0-9]{1,16}$/.test(username)) {
    return { error: 'The User ID is 1-16 letters or digits (what the login page accepts).' };
  }
  if (password.length < 1 || password.length > 20) {
    return { error: 'Enter the password (1-20 characters).' };
  }
  const minConfidence = Math.min(1, Math.max(0, Number($('minConfidence').value) || 0));
  $('minConfidence').value = String(minConfidence);
  return { username, password, minConfidence };
}

// Signing in needs the credentials filled, so autoLogin forces autofill on (and off takes it along).
// "Sign in after logout" is a sub-rule of auto sign-in: only available (and kept) while that is on.
function syncRules() {
  if (!$('autoLogin').checked) $('signInAfterLogout').checked = false;
  $('signInAfterLogout').disabled = !$('autoLogin').checked;
}
$('autoLogin').addEventListener('change', () => {
  if ($('autoLogin').checked) $('autofill').checked = true;
  syncRules();
});
$('autofill').addEventListener('change', () => {
  if (!$('autofill').checked) $('autoLogin').checked = false;
  syncRules();
});

function statusText(autofill, autoLogin) {
  if (autoLogin) return $('signInAfterLogout').checked ? 'Auto sign-in is on (site opens and after logout).' : 'Auto sign-in is on (site opens, not after logout).';
  if (autofill) return 'Credentials are filled in, you press LOGIN.';
  return 'Credential fill is off, only the captcha is filled.';
}

$('save').addEventListener('click', () => {
  const v = validate();
  if (v.error) return setStatus(v.error, true);
  chrome.storage.local.set({
    username: v.username,
    password: v.password,
    autofill: $('autofill').checked || $('autoLogin').checked,
    autoLogin: $('autoLogin').checked,
    signInAfterLogout: $('autoLogin').checked && $('signInAfterLogout').checked,
    minConfidence: v.minConfidence,
  }).then(() => {
    setStatus(`Saved. ${statusText($('autofill').checked, $('autoLogin').checked)}`);
  });
});

$('clear').addEventListener('click', () => {
  chrome.storage.local.remove(Object.keys(DEFAULTS)).then(() => {
    $('username').value = '';
    $('password').value = '';
    $('autofill').checked = true;
    $('autoLogin').checked = true;
    $('signInAfterLogout').checked = false;
    $('minConfidence').value = '0.5';
    syncRules();
    setStatus('Cleared. The captcha keeps being filled, nothing is signed in.', false);
  });
});

chrome.storage.local.get(DEFAULTS).then((s) => {
  $('username').value = s.username;
  $('password').value = s.password;
  $('autofill').checked = s.autofill || s.autoLogin;
  $('autoLogin').checked = s.autoLogin;
  $('signInAfterLogout').checked = s.autoLogin && s.signInAfterLogout;
  $('minConfidence').value = String(s.minConfidence);
  syncRules();
  if (s.username && s.password) {
    setStatus(`Saved. ${statusText(s.autofill || s.autoLogin, s.autoLogin)}`);
  } else {
    setStatus('No credentials saved yet.');
  }
});
