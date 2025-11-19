from typing import Dict, List, Optional, Any, Annotated, Sequence
from typing_extensions import TypedDict
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage, ToolCall
from langchain_upstage import ChatUpstage
from utils.logging import logger
from config.settings import UPSTAGE_MODEL, UPSTAGE_API_KEY
from core.vector_store import search_similar
from core.storage import (
    get_activities, 
    get_activities_for_briefing, 
    save_briefing, 
    get_activity_by_id, 
    get_setting
)

# 전역 리소스
_GLOBAL_RESOURCES = {
    "vectorstore": None,
    "db_connection": None
}

def set_agent_resource(vectorstore_instance):
    """app.py에서 초기화된 리소스를 agent 모듈에 설정"""
    global _GLOBAL_RESOURCES
    _GLOBAL_RESOURCES["vectorstore"] = vectorstore_instance
    logger.info("[Agent] 벡터스토어 리소스 설정 완료")

def _get_vectorstore():
    """Tool에서 사용할 벡터스토어 인스턴스를 조회"""
    if _GLOBAL_RESOURCES["vectorstore"] is None:
        raise ValueError("벡터스토어 리소스가 초기화되지 않았습니다. app.py에서 set_agent_resources를 호출해야 합니다.")
    return _GLOBAL_RESOURCES["vectorstore"]

# ============= Tools 정의 =============
@tool
def vector_search_tool(query: str) -> str:
    """사용자 질문에 관련된 저장된 지식 문서를 벡터 검색합니다. 질문의 주제나 키워드를 입력하세요."""
    vectorstore = _get_vectorstore()
    results = search_similar(vectorstore, query, k=3)

    if not results:
        return "죄송합니다. 질문과 관련된 정보를 찾지 못했습니다."
    
    # LLM이 이해하기 쉽게 결과를 포맷팅 및 요약하여 반환
    context_lines = []
    for doc in results:
        context_lines.append(f"제목: {doc['metadata']['title']}, 내용: {doc['content'][:400]}...")

    context = "\n---\n".join(context_lines)

    return f"검색된 참고 자료: \n{context}"

@tool
def generate_briefing_tool(days: int=7) -> str:
    """
    최근 며칠간의 저장된 활동을 분석하여 주요 동향, 키워드, 상세 요약을 포함하는 브리핑을 생성합니다. 
    분석할 기간(days)을 숫자로 입력하세요 (예: 1, 7).
    """
    # 데이터 조회
    activities = get_activities_for_briefing(days=days)

    period_end = datetime.now().date().isoformat()
    period_start = (datetime.now() - timedelta(days=days)).date().isoformat()

    if not activities:
        return f"{period_start}부터 {period_end}까지의 활동 기록이 없어 브리핑을 생성할 수 없습니다."

    # LLM 입력 데이터 포매팅
    activity_summaries = "\n".join([
        f"-[{a['created_at']}] {a['title']} (카테고리-{a['category']}) :{a['summary']}"
        for a in activities
    ])

    # 프롬프트 구성
    prompt = f"""
        당신은 사용자의 지식 저장소 'Stacknote'의 전문 분석가입니다.
        다음 활동 데이터를 분석하여 아래 지침에 따라 상세한 브리핑을 생성해주세요.
        
        <metadata>
        오늘 날짜: {period_end}
        분석 기간: 최근 {days}일 ({period_start} ~ {period_end})
        총 활동 수: {len(activities)}개
        </metadata>
        
        <raw_data>
        {activity_summaries}
        </raw_data>
        
        <analysis_guidelines>
        다음 구조로 브리핑을 작성하세요:

        # Stacknote 활동 브리핑 ({period_start} ~ {period_end})
        ## 1. 주요 동향 요약
        ### 📅 주간 흐름
        - 초반/중반/후반으로 나눠 시간에 따른 관심사 변화 분석

        ### 📌 핵심 테마
        - 가장 두드러진 주제 2-3개를 강조
        - 각 테마별 구체적인 활동 예시 포함

        ## 2. 카테고리 분포
        - 카테고리별 비율을 이모지로 시각화
        - 예: 📊 AI (60%) > Programming (30%) > 기타 (10%)

        ## 3. 핵심 키워드
        - 가장 중요한 키워드 3-5개
        - 각 키워드가 어떤 맥락에서 나왔는지 한 줄 설명

        ## 4. 인사이트
        - 다음 주 학습/작업 방향 제안 (2-3개)
        - 현재 학습 흐름의 연속선상에서 제안
        - 구체적인 기술/프로젝트명 언급

        ## 5. 주목할 자료 
        - 특히 중요하거나 나중에 다시 볼 만한 자료 2-3개
        - 제목과 간단한 설명
        </analysis_guidelines>

        <tone>
        - 긍정적이고 격려하는 톤
        - "비기술적", "일부만" 같은 부정적 표현 지양
        - 균형잡힌 활동을 칭찬
        - 구체적이고 실행 가능한 조언
        </tone>

        브리핑은 한국어로 작성하며, Markdown 형식을 사용하여 가독성 높게 작성하세요.
    """
    llm = ChatUpstage(api_key='up_t4l7XWbZMQVd38iZV9Sp6jgbIQh0a', model='solar-pro2', temperature=0.1)

    # LLM 호출
    briefing_response = llm.invoke(prompt)
    briefing_text = briefing_response.content

    # DB에 저장
    save_briefing(
        period_start=period_start, 
        period_end=period_end, 
        content=briefing_text, 
        activity_count=len(activities), 
        metadata={"days": days}
    )

    # Agent에게 최종 텍스트 반환
    return briefing_text

@tool
def db_query_tool(category: str=None, limit: int=10, date: str=None):
    """
    활동 목록 조회
    
    Args:
        category: 조회할 카테고리 (None이면 전체)
        limit: 최대 조회 개수 (기본값: 10)
        date: 날짜 필터 (YYYY-MM-DD 형식, 예: "2025-01-15", None이면 전체 기간)
            - "오늘"은 현재 날짜로 변환
            - "어제"는 어제 날짜로 변환
    
    Returns:
        str: 활동 목록 또는 오류 메시지
    """
    # 날짜 변환
    if date and date.lower() in ['오늘', 'today']:
        date = datetime.now().date().isoformat()
    elif date and date.lower() in ['어제', 'yesterday']:
        date = (datetime.now() - timedelta(days=1)).date().isoformat()

    activities = get_activities(limit=limit, category=category, date=date)

    if not activities:
        date_msg = f"'{date}'" if date else "전체 기간"
        category_msg = f"'{category}' 카테고리" if category else "모든 카테고리"
        return f"{date_msg}의 {category_msg}에서 조회된 활동 기록이 없습니다."

    # agent가 읽기 쉽도록 포맷팅
    result_str = []
    for idx, a in enumerate(activities, 1):
        result_str.append(
            f"{idx}. **{a['title']}**\n"
            f"   - URL: {a['url']}\n"
            f"   - 카테고리: {a['category']}\n"
            f"   - 날짜: {a['created_at'][:10]}\n"
            f"   - 요약: {a['summary'][:100]}..."
        )
    
    result = "\n\n".join(result_str)
    date_info = f" ({date})" if date else ""
    return f"조회된 활동{date_info}: 총 {len(activities)}개\n\n{result}"

@tool
def get_activity_details_tool(activity_id: int) -> str:
    """
    활동 ID를 입력받아 해당 활동의 상세 내용(제목, 전체 본문, 카테고리 등)을 조회합니다. 
    사용자가 특정 자료의 원본 내용을 확인하고 싶을 때 사용합니다.
    """
    activity = get_activity_by_id(activity_id)

    if not activity:
        return f"활동 ID {activity_id}에 대한 자료를 찾을 수 없습니다."
    
    # LLM에게 보내는 내용 포맷팅
    details = f"""
        --- 상세 활동 정보 (ID: {activity_id}) ---
        제목: {activity.get('title', 'N/A')}
        URL: {activity.get('url', 'N/A')}
        요약: {activity.get('summary', 'N/A')}
        카테고리: {activity.get('category', 'N/A')}
        저장일: {activity.get('created_at', 'N/A')[:10]}
        
        **원본 본문(Content):**
        {activity.get('content', '원본 내용 없음')[:2500]}... (1000자 제한)
    """

    return details

@tool
def get_user_topics_tool() -> str:
    """
    사용자가 설정한 핵심 관심 주제 목록(user_topics)을 조회합니다. 
    검색이나 브리핑 결과에 이 정보를 참고하여 답변을 맞춤화해야 할 때 사용하세요.
    """
    topics = get_setting() # core/storage.py에 구현되어 있어야 함

    if not topics:
        return "사용자가 설정한 관심 주제가 없습니다. 일반적인 답변을 제공합니다."
        
    return f"사용자의 현재 관심 주제 목록: {', '.join(topics)}"

# ============= Agent State 정의 =============
class AgentState(TypedDict):
    """
    Agent의 대화 상태
    
    Attributes:
        messages: 대화 기록 (자동으로 누적됨)
            - add_messages 리듀서: 새 메시지 추가, 중복 ID 자동 업데이트
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ============= Agent 노드 정의 =============
def llm_call(state: AgentState) -> Dict:
    """
    LLM 호출 노드
    
    사용자 메시지를 분석하여 도구 사용이 필요한지 판단합니다.
    첫 호출 시 시스템 프롬프트를 자동으로 추가합니다.
    
    Args:
        state: 현재 Agent 상태 (messages 포함)
    
    Returns:
        Dict: {"messages": [AIMessage]} - LLM 응답 메시지
    """
    llm = ChatUpstage(api_key=UPSTAGE_API_KEY, model=UPSTAGE_MODEL)

    # tool binding
    tools = [
    vector_search_tool,
    generate_briefing_tool,
    db_query_tool, 
    get_activity_details_tool, 
    get_user_topics_tool
    ]
    llm_with_tools = llm.bind_tools(tools)

    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        system_prompt = """
<role>
너는 'Stacknote' Agent입니다. 사용자가 방문한 웹사이트는 자동으로 저장되며, 
카테고리는 Programming, AI, Music, News 등 실제 내용 기반으로 자동 분류됩니다.
</role>

<system_capabilities>
Stacknote가 할 수 있는 것:
- 사용자가 방문한 웹페이지 자동 수집 및 저장
- 각 페이지의 제목, URL, 본문, 요약, 카테고리, 태그 저장
- 저장된 데이터를 날짜, 카테고리, 태그로 검색
- 벡터 검색으로 유사한 내용 찾기
- 기간별 브리핑 자동 생성

Stacknote가 할 수 없는 것:
- 실시간 인터넷 검색
- 현재 저장되지 않은 웹사이트 정보 조회
- 파일 다운로드나 업로드
</system_capabilities>

<goals>
1. 사용자 질문의 의도를 정확하게 파악하고, 최적의 도구를 선택하여 문제를 해결합니다.
2. 모든 최종 답변은 반드시 **한국어**로 요약하여, 명료하고 친절한 문체로 사용자에게 전달합니다.
3. 도구를 사용해야만 해결할 수 있는 질문인지 먼저 판단하고, 도구가 필요 없다면 직접 답변합니다.
</goals>

<thinking_process>
질문을 받으면 다음 단계를 따라서 진행해:

Step 1: 질문 분석
  - 사용자가 무엇을 원하는가?
  - 어떤 정보가 필요한가?

Step 2: 도구 선택
  - 단일 Tool로 충분한가? 여러 개 필요한가?
  - 실행 순서는?

Step 3: 실행 및 평가
  - Tool 결과가 충분한가?
  - 추가 Tool 호출이 필요한가?

Step 4: 응답 생성
  - 명확하고 친절하게
  - 필요하면 후속 질문 제안
</thinking_process>

<instructions>
# Tool 사용 지침
다음은 사용자의 요청 유형에 따른 Tool 사용 지침입니다. 요청을 Tool 사용에 필요한 **인수(Arguments)**로 정확히 변환하여 호출해야 합니다.
당신은 대화 히스토리를 유지하며, 이전 질문과 답변을 기억합니다.
사용자가 "그거", "그 중에", "앞에서" 같은 표현을 사용하면 이전 컨텍스트를 참조하세요.

1. **지식 검색 (RAG):**
   - **요청 유형:** 특정 개념, 정의, 원리 설명 (예: 'RAG가 뭐야?', 'FastAPI 비동기 설명해 줘')
   - **사용 Tool:** `vector_search_tool`
   - **인수:** 질문의 핵심 내용(query)을 Tool에 전달합니다.

2. **활동 목록 조회:**
   - **요청 유형:** 
     * "오늘 방문한 사이트 알려줘"
     * "이번 주 RAG 관련 자료 보여줘"
     * "최근 읽은 LangGraph 자료"
   - **사용 Tool:** `db_query_tool`
   - **인수 변환 규칙:**
     * "오늘" → date="오늘" (Tool이 자동 변환)
     * "어제" → date="어제" (Tool이 자동 변환)
     * "이번 주" → date=None, limit=20 (많이 조회)
     * "최근 N일" → date=None, limit=적절한 수
     * 카테고리 언급 시 → category="카테고리명"

3. **종합 분석 및 브리핑:**
   - **요청 유형:** 기간별 요약, 동향 분석, 패턴 분석 요청 (예: '이번 주 요약해 줘', '학습 패턴 분석 결과 보여줘')
   - **사용 Tool:** `generate_briefing_tool`
   - **인수:** 분석 기간(days)

4. **상세 내용 조회:**
   - **요청 유형:** 목록 조회 후 특정 자료의 원본 내용 요청 (예: '저 15번 자료 전체 내용 요약해 줘', 'ID 10의 본문 보여줘')
   - **사용 Tool:** `get_activity_details_tool`
   - **인수:** 활동 ID(activity_id)

5. **사용자 맞춤 정보 활용:**
   - **요청 유형:** 검색이나 브리핑 전에 사용자의 관심 주제를 확인해야 할 때. (Agent가 자율적으로 판단하여 사용)
   - **사용 Tool:** `get_user_topics_tool`
   - **인수:** 인자 없이 호출합니다. 이 정보는 Agent의 추론 과정에만 사용됩니다.
</instructions>
"""
        messages = [SystemMessage(content=system_prompt)] + list(messages)

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    """
    다음 노드 결정 (조건부 라우팅)
    
    마지막 메시지에 tool_calls가 있으면 'tools' 노드로,
    없으면 종료(END)합니다.
    
    Args:
        state: 현재 Agent 상태
    
    Returns:
        str: "tools" 또는 END
    """
    messages = state["messages"]
    last_message = messages[-1]

    # Tool call이 있으면 tools 노드로, 없으면 종료
    if last_message.tool_calls:
        return "tools"
    
    return END


# ============= Agent Graph 생성 =============
def create_agent_graph():
    """
    Agent Graph 생성 및 컴파일
    
    Returns:
        CompiledGraph: 실행 가능한 Agent Graph
    """
    tools = [
    vector_search_tool,
    generate_briefing_tool,
    db_query_tool, 
    get_activity_details_tool, 
    get_user_topics_tool
    ]

    # tool 노드 생성
    tool_node = ToolNode(tools)

    # graph 생성
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("agent", llm_call)
    workflow.add_node("tools", tool_node)

    # entry point 설정
    workflow.set_entry_point("agent")

    # egde 추가
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

    # tools 실행 후 다시 agent로
    workflow.add_edge("tools", "agent")

    # compile
    agent_graph = workflow.compile()

    logger.info("StateGraph Agent 생성 완료 (경고 없음)")
    return agent_graph

def run_agent(user_message: str, agent_graph, conversation_state: Optional[Dict] = None) -> Dict:
    """
    Agent 실행 (대화 상태 유지)
    
    Args:
        user_message: 사용자 입력
        agent_graph: Agent graph
        conversation_state: 이전 대화 상태
    
    Returns:
        {
            'response': str,
            'state': dict
        }
    """

    try:
        # 이전상태 가져오기
        if conversation_state is None:
            conversation_state = {"messages": []}

        # 새 메세지 추가
        messages = conversation_state.get("messages", [])
        messages.append(HumanMessage(content=user_message))

        # agent 실행
        result = agent_graph.invoke({"messages": messages})

        # 응답 추출
        response_message = result["messages"][-1]
        response_text = response_message.content

        logger.info(f"Agent 응답 생성 완료: {response_text[:100]}...")
        
        return {
            'response': response_text,
            'state': result
        }

    except Exception as e:
        logger.error(f"Agent 실행 중 오류: {e}")
        return {
            'response': f"죄송합니다. 요청을 처리하는 중 오류가 발생했습니다: {str(e)}",
            'state': conversation_state
        }