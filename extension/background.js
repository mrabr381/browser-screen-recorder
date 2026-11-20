// Service worker: opens the recorder page in a tab (a popup cannot keep
// recording once it loses focus, so recording lives in a full tab).
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "open-recorder") {
    chrome.tabs.create({ url: chrome.runtime.getURL("recorder.html") });
  }
});
