// Relays captcha images from the page to the local Vision host (../host/vision_host.py).
const HOST = 'com.captcha_paster.vision';

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action !== 'solve') return;
  chrome.runtime.sendNativeMessage(HOST, { image: message.image }, (reply) => {
    sendResponse(reply ?? { error: chrome.runtime.lastError?.message ?? 'no reply from host' });
  });
  return true; // keeps the channel open for async response
});
