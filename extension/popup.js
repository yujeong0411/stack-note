document.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('consentButton');
  const statusDiv = document.getElementById('status');

  // 버튼 클릭 시 동의 저장
  button.addEventListener('click', () => {
    chrome.storage.local.set({ userConsent: true }, () => {
      statusDiv.textContent = '저장소에 동의(true)가 저장되었습니다.';
      statusDiv.style.color = 'green';
      button.disabled = true;

      console.log('동의함.');
    });
  });

  // 현재 상태 확인 
  chrome.storage.local.get("userConsent", ({ userConsent }) => {
    if (userConsent) {
      statusDiv.textContent = '현재 동의 상태입니다.';
      button.textContent = '이미 동의됨';
      button.disabled = true;
    }
  });
});