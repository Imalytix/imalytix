chrome.storage.local.get(["lastAnalysisResult"]).then(({ lastAnalysisResult }) => {
  document.getElementById("result").textContent = JSON.stringify(lastAnalysisResult || {}, null, 2);
});

