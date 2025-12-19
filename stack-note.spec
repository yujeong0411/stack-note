# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.hooks import get_package_paths
from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path 

# streamlit 패키지 경로 찾기
streamlit_pkg_path = Path(get_package_paths('streamlit')[1])
streamlit_static_path = str(streamlit_pkg_path / 'static')

trafilatura_pkg_path = Path(get_package_paths('trafilatura')[1])

justext_pkg_path = Path(get_package_paths('justext')[1])
justext_stoplists_path = str(justext_pkg_path / 'stoplists')

streamlit_autorefresh_pkg_path = Path(get_package_paths('streamlit_autorefresh')[1])
streamlit_autorefresh_frontend_path = str(streamlit_autorefresh_pkg_path / 'frontend/build')

dateparser_data_files = collect_data_files('dateparser')


block_cipher = None

datas=[
        # ('원본경로', '실행파일내부경로')
        ('app.py','.'),
        ('api.py', '.'),
        ('style.css', '.'),
        ('.env', '.'),

        # 폴더
        ('core', 'core'),
        ('config', 'config'),
        ('extension', 'extension'),
        ('utils', 'utils'),
        (streamlit_static_path, 'streamlit/static'),
        (trafilatura_pkg_path, 'trafilatura'),
        (justext_stoplists_path, 'justext/stoplists'),
        (streamlit_autorefresh_frontend_path, 'streamlit_autorefresh/frontend/build')
    ]

datas += dateparser_data_files

datas += copy_metadata('streamlit')

# (선택사항) Streamlit이 의존하는 패키지들도 안전하게 추가하면 좋습니다.
# 만약 실행 후 또 다른 metadata 에러가 뜨면 아래 주석을 풀고 추가하세요.
# datas += copy_metadata('tqdm')
# datas += copy_metadata('regex')
# datas += copy_metadata('requests')
# datas += copy_metadata('packaging')

a = Analysis(
    ['run_desktop.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # ===============================================
        # 1. Streamlit Core (필수)
        # ===============================================
        'streamlit.web.cli',
        'streamlit.web.server.server',
        'streamlit.runtime.scriptrunner.magic_funcs', 
        'streamlit.runtime.metrics_util',
        'streamlit.logger',
        'streamlit.error_util',
        'streamlit.web.server.websocket_handler',
        'streamlit_autorefresh',
        
        # ===============================================
        # 2. Flask / API (core, trafilatura, requests)
        # ===============================================
        'flask', 
        'jinja2',
        'werkzeug',
        'requests',
        'trafilatura', 
        'lxml',
        'sqlite3',
        'urllib.parse',
        
        # ===============================================
        # 3. Scheduling (APScheduler)
        # ===============================================
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.jobstores.memory', 
        'apscheduler.executors.pool', 
        'apscheduler.triggers.cron', 
        'apscheduler.triggers.interval', 
        'apscheduler.jobstores.sqlalchemy',
        'apscheduler.triggers.date', 
        
        # ===============================================
        # 4. LangChain / LLM / VectorDB
        # ===============================================
        'langchain',
        'langchain_core',
        'langchain_community',
        'langchain_upstage',
        'langchain_chroma',
        'langgraph',
        'langgraph.graph',
        'langgraph.prebuilt',
        'networkx',
        'chromadb',
        'pydantic',
        'pydantic.v1.typing', # Pydantic 버전 충돌 방지
        'httpx', # API 통신 라이브러리
        'chromadb.telemetry.product.posthog',
        'chromadb.telemetry.posthog',         # Telemetry 관련 모듈
        'chromadb.api',
        'chromadb.api.rust',
        'chromadb.types',
        'requests', # ChromaDB 내부에서 HTTP 통신용으로 사용
        'pandas',   # ChromaDB 내부 데이터 처리용으로 사용
        'numpy',    # Pandas/ChromaDB의 핵심 종속성
        'packaging'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Stacknote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
