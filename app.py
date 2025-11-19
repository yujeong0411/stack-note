# uv run streamlit run app.py로 로컬 실행 
import streamlit as st
from datetime import datetime
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from streamlit_autorefresh import st_autorefresh
from api import start_api, url_queue
from utils.logging import logger
from utils.ui import load_css, render_card, render_briefing_block
from core.url_collector import should_save_url, process_url_auto
from core.vector_store import init_vectorstore 
from core.storage import init_db, get_activity_metrics, get_activities, get_categories, get_briefings, get_tags
from core.agent import create_agent_graph, run_agent, set_agent_resource

EXTERNAL_LOGO_URL = "https://res.cloudinary.com/dofrfwdqh/image/upload/v1763444959/stacknote_logo.png"

header_html = f"""
<div style='display: flex; justify-content: center; align-items: center;'>
    <img src="{EXTERNAL_LOGO_URL}" alt="Stacknote Logo" style='height: 50px; margin-right: 15px;'>
    <h1 style='margin: 0;'>Stacknote</h1>
</div>
"""

st.set_page_config(page_title="Stacknote", page_icon=EXTERNAL_LOGO_URL)

# ============================================================================
# 3. CACHED RESOURCES & INITIALIZATION

@st.cache_resource
def initialize_resources():
    """
    앱 시작 시 필요한 모든 리소스와 Agent를 한 번만 초기화

    Returns:
        tuple: (vectorstore, agent_graph)
    """
    logger.info("DB 및 Agent 리소스 초기화 시작")

    # DB 초기화
    init_db()

    # Vectorstore 초기화
    vectorstore = init_vectorstore()
    
    # Agent 초기화
    agent_graph = create_agent_graph()

    # agent에게 전달 
    set_agent_resource(vectorstore) 

    logger.info("리소스 초기화 완료")
    return vectorstore, agent_graph

# 각 데이터 독릭접 캐싱
@st.cache_data(ttl=300)
def get_categories_cached(date_str):
    """UI용 카테고리 목록
    
    Args:
        date_str: None 또는 YYYY-MM-DD 형식의 문자열
    """
    return get_categories(date=date_str)

@st.cache_data(ttl=300)  
def get_tags_cached(date_str: str, category: str = None):
    """UI용 태그 목록 (긴 캐싱)
    
    Args:
        date_str: None 또는 YYYY-MM-DD 형식의 문자열
        category: None 또는 카테고리 문자열
    """
    return get_tags(
        date=date_str if date_str else None,
        category=category,  
        limit=100
    )

# stramlit은 캐시 후 함수 호출시 마다 make_key()
# 캐시 키를 만들 때 해시를 사용 , steamlit  내부적으로 cache_key - hash((name, age))
# f리스트는 변할 수 있다. 리스트는 같은 메모리 주소를 같지만, 리스트에 추가를 해도 항상 같은 메모리 주소??
# tuple은 수정불가이기에 
@st.cache_data(ttl=60) 
def get_activities_cached(date_str: str, category: str, tags_tuple: list, limit: int):
    """활동 목록 (짧은 캐싱)
    
    Args:
        date_str: None 또는 YYYY-MM-DD 형식의 문자열
        category: 카테고리 문자열
        tags_tuple: 태그들을 포함하는 tuple (해시 가능)
        limit: 최대 개수
    """
    # tuple을 list로 변환
    tags_list = list(tags_tuple) if tags_tuple else None

    return get_activities(
        limit=limit,
        category=None if category == "전체" else category,
        date=date_str,
        tags=tags_list if tags_list else None
    )

@st.cache_data(ttl=60)  # 1분
def get_metrics_cached():
    """활동 메트릭 (짧은 캐싱)"""
    return get_activity_metrics()

@st.cache_data(ttl=300)  # 5분
def get_briefings_cached(limit: int = 5):
    """브리핑 목록 (긴 캐싱)"""
    return get_briefings(limit=limit)

# ============================================================================
# 4. UI COMPONENTS

def render_header():
    """앱 헤더 렌더링"""
    st.markdown(header_html, unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:gray;'>Your AI-powered personal knowledge base</p>", unsafe_allow_html=True)

def render_feed_tab():
    """Feed 탭 랜더링"""

    # 10초마다 페이지 자동 갱신
    st_autorefresh(interval=5*60*1000, key="feed_refresh")

    st.markdown("### 🏷️ 주제별 분포")
    metrics = get_metrics_cached()
    
    if metrics['category_distribution']:
        for item in metrics['category_distribution']:
            st.progress(
                item['percent'] / 100, 
                text=f"{item['name']} {item['percent']}%"
            )
    else:
        st.progress(0, text="활동 데이터 부족")

    st.markdown("### 📅 오늘 활동 요약")

    colA, colB, colC = st.columns(3)
    colA.metric("방문한 사이트", f"{metrics['total_count_today']}개")
    colB.metric("최다 카테고리", metrics['top_category'])
    colC.metric("최다 태그", metrics['top_tag'])


    st.divider()

    # 활동 목록 헤더
    col_title, col_reset, col_refresh = st.columns([4, 3, 3])
    
    with col_title:
        st.markdown("### 📝 활동 목록")
    
    with col_reset:
        # 필터 초기화 버튼
        if st.button("초기화", key="reset_filters", help="모든 필터 초기화"):
            # Session state 초기화
            st.cache_data.clear()  
            st.session_state.date_filter = None
            st.session_state.category_filter = "전체"
            st.session_state.tag_filter = []
            st.session_state.limit_filter
            st.rerun()

    with col_refresh:
        # 새로고침 버튼 
        if st.button("refresh"):
            st.cache_data.clear()
            st.rerun()

    col1, col2 = st.columns(2)

    # 날짜 선택
    with col1:
        selected_date = st.date_input(
            "날짜",
            value=None,
            max_value=datetime.now().date(),
            key="date_filter"
        )

    # 날짜 기준 카테고리, 태그 로드
    date_str = selected_date.isoformat() if selected_date else None
    categories = get_categories_cached(date_str) 

    # 카테고리 선택
    with col2:
        category_options = ["전체"] + categories
        category_filter = st.selectbox(
            "카테고리",
            category_options,
            key="category_filter"
        )

    col3, col4 = st.columns(2)

    # 태그 선택 (날짜 + 카테고리 필터링)
    with col3:
        all_tags = get_tags_cached(
            date_str,
            None if category_filter == "전체" else category_filter 
        )
        
        tag_filter = st.multiselect(
            "태그",
            options=all_tags,
            key="tag_filter"
        )
    
    with col4:
        limit = st.number_input(
            "개수",
            min_value=5,
            max_value=50,
            value=10,
            step=5,
            key="limit_filter"
        )

    # 데이터 로드
    tags_tuple = tuple(tag_filter) if tag_filter else () 
    activities = get_activities_cached(
        date_str, 
        category_filter, 
        tags_tuple, 
        limit
    )
    
    # 간단한 필터 요약
    filter_summary_col1, filter_summary_col2 = st.columns([8, 2])
    
    with filter_summary_col1:
        if selected_date or category_filter != "전체" or tag_filter:
            filter_info = []
            if selected_date:
                filter_info.append(f"📅 {selected_date.isoformat()}")
            if category_filter != "전체":
                filter_info.append(f"📂 {category_filter}")
            if tag_filter:
                filter_info.append(f"🏷️ {', '.join(tag_filter)}")
            
            st.caption(f"**적용 중:** {' · '.join(filter_info)}")
        else:
            st.caption("**전체 활동** (최신순)")
    
    with filter_summary_col2:
        st.caption(f"**{len(activities)}개**")

    st.markdown("---")
    
    # 활동 표시
    if activities:
        for item in activities:
            render_card(
                title=item['title'],
                url=item['url'],
                summary=item['summary'],
                tags=item['tags']
            )
    else:
        st.info("💡 조건에 맞는 활동이 없습니다.")

def render_briefing_tab(agent_graph):
    """Briefing 탭 렌더링"""
    # 브리핑 로드
    briefings = get_briefings_cached(limit=5)

    if briefings:
        for briefing in briefings:
                created_at = briefing.get('created_at', '')
                content = briefing.get('content', '')
                activity_count = briefing.get('activity_count', 0)
                metadata = briefing.get('metadata', {})
                period_start = briefing.get('period_start', '')
                period_end = briefing.get('period_end', '')

                with st.expander(
                    f"{period_start} ~ {period_end} 브리핑", 
                    expanded=False
                ):
                    render_briefing_block(
                        content=content
                    )
                    st.caption(f"📊 {activity_count}개 활동 분석 | 🕐 {created_at[:16]}")
    else:
        st.info("생성된 브리핑이 없습니다.")

    st.divider()

    # 맞춤 브리핑
    st.markdown("### 새 브리핑 생성")
    
    col1, col2 = st.columns([7, 3])
    
    with col1:
        briefing_days = st.slider("분석 기간 (일)", 1, 30, 3, key="briefing_days_slide")
    
    with col2:
        st.write("")  # 정렬
        generate_button = st.button("생성", use_container_width=True, type="primary")
    
    if generate_button:
        with st.spinner(f"최근 {briefing_days}일 분석 중..."):
            try:
                run_agent(
                    f"최근 {briefing_days}일간의 활동을 분석하여 브리핑을 생성해줘.",
                    agent_graph
                )
                
                get_briefings_cached.clear()
                st.rerun()

            except Exception as e:
                st.error(f"브리핑 생성 실패: {str(e)}")
                logger.error(f"브리핑 생성 오류: {e}", exc_info=True)

def render_chat_tab(agent_graph, user_query):
    """
    Agent 채팅 인터페이스 렌더링
    
    Args:
        agent_graph
    """
    st.caption("저장된 활동에 대해 무엇이든 물어보세요!")

    # 대화 상태 초기화
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # 이전 대화
    for msg in st.session_state.chat_history:
        st.chat_message(msg['role']).write(msg['content'])

    if user_query:
        # 사용자 메시지 표시 및 저장
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_query
        })

        # Agent 호출
        with st.chat_message("assistant"):
            with st.spinner("요청하신 내용을 분석 중입니다..."):
                try:
                    result = run_agent(
                        user_query, 
                        agent_graph,
                        st.session_state.conversation_state
                    )

                    response = result["response"]
                    st.session_state.conversation_state = result['state']

                    # 응답 표시 및 저장
                    st.write(response)
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })

                    # 브리핑 생성 시 캐시 무효화
                    if any(kw in user_query for kw in ['브리핑', '요약', '분석']):
                        st.cache_data.clear()

                except Exception as e:
                    error_msg = f"오류가 발생했습니다.: {str(e)}"
                    st.error(error_msg)
                    logger.error(f"Agent 실행 오류: {e}")

    

# ============================================================================
# 5. BACKGROUND TASKS

def process_url_queue(vectorstore_instance):
    """
    큐에 쌓인 URL들을 처리
    
    Args:
        vectorstore: 초기화된 vectorstore 인스턴스
        
    Returns:
        list: 처리된 URL 정보 리스트
    """
    new_items= []

    if url_queue.empty():
        return new_items # 큐가 비어있으면 즉시 리턴

    logger.info("큐에 데이터 있음! 소비 시작.")

    while not url_queue.empty():
        url_data = url_queue.get()
        logger.info(f"처리 중: {url_data['url']}")

        try:
            # 1. 저장 여부 판단 (LLM)
            decision = should_save_url(url_data['url'], url_data['title'])

            if decision['should_save']:
                # 2. 콘텐츠 추출 및 저장
                result = process_url_auto(url_data['url'], vectorstore_instance)
                if result:
                    new_items.append(result)
                    logger.info(f"저장 완료: {result['title']}")
            else:
                logger.info(f"저장 건너뜀: {decision['reason']}")

        except Exception as e:
            logger.error(f"URL 처리 중 오류: {e}", exc_info=True)
        finally:
            url_queue.task_done() # 큐 항목 처리 완료를 알림

    return new_items

def start_queue_consumer(vectorstore_instance):
    """
    백그라운드 스레드에서 큐를 주기적으로 확인
    
    Args:
        vectorstore: 초기화된 vectorstore 인스턴스
    """
    from time import sleep
    logger.info("=== 큐 소비자 스레드 시작 ===")
    
    while True:
        try:
            # 큐에서 새로운 항목을 처리
            new_items = process_url_queue(vectorstore_instance)
            
            if new_items:
                logger.info(f"성공: {len(new_items)}개의 URL이 큐에서 처리됨.")
                # 참고: Streamlit UI는 직접 업데이트 불가, DB를 확인해야 함

        except Exception as e:
            logger.error(f"큐 소비자 오류: {e}", exc_info=True)
            
        sleep(10) # 5초마다 큐 확인

def generate_briefing_job(agent_graph):
    """
    일일 브리핑 자동 생성 (APScheduler Job)
    
    Args:
        agent_graph
    """
    try:
        logger.info(f"자동 브리핑 생성: {datetime.now()}")

        result = run_agent(
            "어제까지의 활동을 분석하여 일일 브리핑을 생성해줘.",
            agent_graph
        )

        logger.info(f"브리핑 완료: {result['response'][:100]}...")

    except Exception as e:
        logger.error(f"브리핑 생성 오류: {e}", exc_info=True)

def initialize_scheduler(agent_graph):
    """
    APScheduler 초기화 및 Job 등록
    
    Args:
        agent_graph
    """

    if 'scheduler_started' in st.session_state:
        return  st.session_state.scheduler  # 기존 scheduler 반환
    
    scheduler = BackgroundScheduler()
        
    scheduler.add_job(
        generate_briefing_job,
        'cron',
        hour=10,
        minute=0,
        args=[agent_graph],
        id='daily_briefing'
    )

    scheduler.start()
    st.session_state['scheduler_started'] = True
    st.session_state['scheduler'] = scheduler

    logger.info("[App] APScheduler 시작 완료.")
    return scheduler


# ============================================================================
# 6. MAIN APPLICATION

def main():
    """메인 애플리케이션 진입점"""
    
    # CSS 로드
    load_css()

    # 리소스 초기화 (캐시됨)
    vectorstore, agent_graph = initialize_resources()
    
    # 헤더 렌더링
    render_header()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📰 Feed", "🧠 Briefing", "💬 Chat"])
    user_query = st.chat_input("Agent에게 질문하기...")

    if user_query:
        st.session_state.active_tab = "chat"  # 채팅 입력 시 Chat 탭으로
    
    with tab1:
        render_feed_tab()
    
    with tab2:
        render_briefing_tab(agent_graph)

    with tab3:
        render_chat_tab(agent_graph, user_query)
        

    # 백그라운드 작업 시작 (한 번만)
    if 'background_started' not in st.session_state:
        # API 서버
        start_api()
        
        # URL 큐 소비자 스레드
        Thread(
            target=start_queue_consumer,
            args=(vectorstore,),
            daemon=True
        ).start()
        
        # 브리핑 스케줄러
        initialize_scheduler(agent_graph)
        
        st.session_state['background_started'] = True
        logger.info("=== 백그라운드 작업 시작 완료 ===")

if __name__ == "__main__":
    main()