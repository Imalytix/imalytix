chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "imalytix-analyze-image",
    title: "Imalytix AI로 분석하기",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "imalytix-analyze-image") return;
  await chrome.storage.local.set({
    lastAnalysisResult: {
      note: "Extension UI is intentionally stubbed in the MVP."
    }
  });
});

