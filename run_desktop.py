import webview
import signal
import time
import threading
from streamlit.web import cli as stcli
import sys
import os

# 챗봇 스타일에 맞는 창 크기 설정
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 750

def get_resource_path(relative_path):
    """
    PyInstaller로 패키징된 경우 임시 폴더(_MEIPASS)에서 경로를 찾고,
    그렇지 않은 경우 현재 작업 디렉토리에서 경로를 찾습니다.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def start_streamlit():
    """Streamlit 서버를 내부 함수로 실행"""
    # 1. 실제 app.py의 절대 경로를 확보합니다.
    app_path = get_resource_path("app.py")

    if not os.path.exists(app_path):
        print(f"Error: app.py file not found at {app_path}")
        return
    
    # 2. [중요] api, core, utils 등을 찾을 수 있도록 _MEIPASS를 sys.path에 추가
    if hasattr(sys, '_MEIPASS'):
        sys.path.append(sys._MEIPASS)

    # 3. sys.argv를 조작하여 CLI 명령어를 흉내 냅니다.
    # 이는 "streamlit run app.py --server.port 8501"과 동일한 효과를 냅니다.
    sys.argv = [
        "streamlit",
        "run",
        app_path,  # 절대 경로 사용
        "--global.developmentMode=false",
        "--server.port=8501",
        "--server.headless=true",
        "--server.runOnSave=false"
    ]

    print(f"Starting Streamlit from: {app_path}") # 디버깅용 로그

    # ==================================================================
    # [수정된 부분] 신호 처리 우회 (Monkey Patching)
    # Streamlit이 서브 스레드에서 signal.signal을 호출하면 에러가 나므로,
    # 아무 기능 없는 함수로 덮어씌웁니다.
    # ==================================================================
    def signal_handler(sig, frame):
        pass
    
    # 기존 signal.signal 함수를 백업할 필요 없이, 
    # 그냥 호출되었을 때 아무것도 안 하도록 만듭니다.
    signal.signal = signal_handler
    # ==================================================================

    # 3. Streamlit 내부 실행 함수 호출
    # (말씀하신 cli._main_run_clExplicit 대신 더 안정적인 stcli.main 사용 권장)
    sys.exit(stcli.main())

if __name__ == '__main__':
    # Streamlit 서버를 시작하는 스레드를 분리
    threading.Thread(target=start_streamlit, daemon=True).start()

    # 서버가 로딩될 때까지 잠시 대기 (환경에 따라 3~5초)
    time.sleep(4)

    # PyWebView로 창 생성 및 Streamlit URL 로드
    webview.create_window(
        'Stacknote',
        'http://localhost:8501',
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=False,  
    )
    # 데스크톱 창 시작
    webview.start()
