// 최근 요청을 기록할 캐시 객체
let sentTabs = {};
// 캐시 초기화 함수: 탭이 완전히 닫히면 메모리 해제
chrome.tabs.onRemoved.addListener((tabId) => {
  delete activeTabStart[tabId];
  delete sentTabs[tabId]; // 탭이 닫힐 때 기록 삭제
});

// 모든 페이지 방문을 자동 감지
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  chrome.storage.local.get("userConsent", ({ userConsent }) => {
    if (!userConsent) return; // 동의 안 하면 수집 안함

    // 페이지 로딩 완료되면
    if (changeInfo.status === 'complete' && tab.url) {
      //  이 탭 ID와 URL이 이미 전송되었는지 확인
      const tabKey = `${tabId}-${tab.url}`;

      if (sentTabs[tabKey]) {
        console.log('중복 요청 무시:', tab.url, ' (이미 전송됨)');
        return; // 이미 전송된 탭/URL 조합이므로 무시
      }

      console.log('페이지 방문 감지:', tab.url);

      // 전송 기록 추가
      sentTabs[tabKey] = true;

      // Streamlit 앱으로 자동 전송
      fetch('http://localhost:8502/api/add-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: tab.url,
          title: tab.title,
          timestamp: new Date().toISOString()
        })
      })
        .then(response => response.json())
        .then(data => {
          if (data.saved) {
            // 저장되면 알림
            chrome.notifications.create({
              type: 'basic',
              iconUrl: 'icon.png',
              title: 'Stacknote 💾',
              message: `저장됨: ${data.category}`
            });
          }
          console.log("data 저장됨")
        })
        .catch(error => {
          // Streamlit 앱이 안 켜져있으면 무시
          // 전송 실패 시, 다음 시도를 위해 기록을 다시 제거할 수 있음 (선택 사항)
          delete sentTabs[tabKey];
          console.log('Stacknote 앱이 실행 중이 아닙니다');
        });
    }
  });
});

// 체류 시간 추적 
let activeTabStart = {};

chrome.tabs.onActivated.addListener((activeInfo) => {
  activeTabStart[activeInfo.tabId] = Date.now();
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (activeTabStart[tabId]) {
    const duration = Date.now() - activeTabStart[tabId];
    // 30초 이상 머문 페이지만 진지하게 봤다고 판단
    if (duration > 30000) {
      console.log(`${tabId} 탭에서 ${duration}ms 체류`);
    }
  }
});