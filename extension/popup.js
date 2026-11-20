// Popup: open the recorder page, or the local transcript editor app.
document.getElementById("open-recorder").addEventListener("click", () => {
  chrome.runtime.sendMessage({ type: "open-recorder" });
  window.close();
});

document.getElementById("open-app").addEventListener("click", () => {
  chrome.tabs.create({ url: "http://localhost:8501" });
  window.close();
});
