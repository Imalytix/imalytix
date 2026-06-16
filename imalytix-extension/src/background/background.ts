import { analyzeImageFile } from "../shared/api/imalytixApi";
import type { AnalysisResult } from "../shared/types/analysis";

const MENU_ID = "imalytix-analyze";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "Imalytix로 분석",
    contexts: ["image"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID || !info.srcUrl) return;

  const windowId = tab?.windowId;
  if (windowId) {
    chrome.sidePanel.open({ windowId });
  }

  // 로딩 상태 저장
  await chrome.storage.local.set({
    imalytix_loading: true,
    imalytix_result: null,
    imalytix_error: null,
    imalytix_preview: info.srcUrl,
    imalytix_source: "context_menu",
    imalytix_timestamp: Date.now(),
  });

  try {
    const resp = await fetch(info.srcUrl);
    if (!resp.ok) throw new Error(`이미지 로드 실패 (HTTP ${resp.status})`);

    const blob = await resp.blob();
    const mime = blob.type || "image/jpeg";
    const ext = mime.split("/")[1]?.split("+")[0] ?? "jpg";
    const file = new File([blob], `image.${ext}`, { type: mime });

    const result: AnalysisResult = await analyzeImageFile(file);

    await chrome.storage.local.set({
      imalytix_loading: false,
      imalytix_result: result,
      imalytix_error: null,
      imalytix_timestamp: Date.now(),
    });
  } catch (e) {
    await chrome.storage.local.set({
      imalytix_loading: false,
      imalytix_result: null,
      imalytix_error: String(e),
      imalytix_timestamp: Date.now(),
    });
  }
});
