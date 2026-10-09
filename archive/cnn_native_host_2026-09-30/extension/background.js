// Relays captcha images from the page to the local model host (../host/cnn_host.py).
const HOST = 'com.captcha_paster.cnn';

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action !== 'solve') return;
  chrome.runtime.sendNativeMessage(HOST, { image: message.image }, (reply) => {
    sendResponse(reply ?? { error: chrome.runtime.lastError?.message ?? 'no reply from host' });
  });
  return true; // keeps the channel open for async response
});
