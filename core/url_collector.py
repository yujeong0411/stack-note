from langchain_upstage import ChatUpstage
from utils.logging import logger
from config.settings import UPSTAGE_API_KEY
from .extractor import extract_content  
from .classifier import classify_content  
from .storage import save_activity, check_existing_activity
from .vector_store import add_activity_to_vector 
import json

llm = ChatUpstage(
    api_key=UPSTAGE_API_KEY,
    model="solar-mini"   # 빠른 모델 사용
)

def should_save_url(url:str, title:str) -> dict:
    """agent가 저장 여부 판단"""
    # 1차 빠른 필터 (조건문)
    exclude = ['bank', 'facebook', 'instagram', 'login', 'auth']
    if any(kw in url.lower() for kw in exclude):
        logger.info("url 걸러짐")
        return {"should_save": False, "reason": "개인정보/보안"}

    # LLM 판단
    prompt = f"""
    URL: {url}
    제목: {title}

    <role>
    너는 당신은 사용자의 지식 저장소(Stacknote)에 보관할 가치가 있는 URL을 선별하는 전문 큐레이터 Agent야.
    </role>

    <instruction>
    주어진 URL과 제목을 분석하여 다음 기준에 따라 저장 여부를 결정해줘. 은행, 로그인, 결제 등과 같이 개인정보 및 보안과 관련된 것은 저장하면 안돼.
    - 저장 (true): 기술 블로그, 프로그래밍 튜토리얼, 공식 문서, 유용한 지식/경험 공유 글, 인터넷 강의 등
    - 무시 (false): 쇼핑몰, 은행/금융 서비스, 로그인/인증 페이지, 개인 정보가 포함된 페이지, 광고 페이지, 검색 페이지 등
    판단 후, 반드시 아래의 output formatT을 따르는 JSON 객체 하나만을 반환해야해. 추가적인 해설, 설명, 주석 등은 필요없어. 
    </instruction>

    <output format>
    {{"should_save": true/false, "reason": "결정을 내린 구체적인 이유를 한 문장으로 설명해."}}
    </output format>
    """
    
    response = llm.invoke(prompt)
    response_text = response.content.strip()
    # json 파싱
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    result = json.loads(response_text)
    return result

def process_url_auto(url:str, vectorstore):
    """자동 수집 URL 처리"""
    
    # db 중복 체크
    existing_id = check_existing_activity(url)
    if existing_id is not None:
        logger.warning(f"[SKIP] DB에 이미 존재 : {url}. 추출 건너뜀")
        return None

    logger.info(f"{url} 추출 시작")

    # 본문 추출
    extracted = extract_content(url)
    if not extracted or extracted['title'] == None:
        logger.info(f"추출 내용 없음: {url}")
        return None
    
    # 기존 classifier 사용!
    classified = classify_content(
        extracted['title'],
        extracted['content']
    )
    
    activity_data = {
        'url': url,
        'title': extracted['title'],
        'content': extracted['content'],
        'summary': classified['summary'],
        'category': classified['category'],
        'tags': classified['tags'],
        'source_type': extracted.get('source_type', 'article')
    }

    # DB 저장
    activity_id = save_activity(data=activity_data)
    
    # vectorestore 저장
    add_activity_to_vector(
        vectorstore,
        activity_id,
        extracted['content'],
        {
            'title': extracted['title'],
            'category': classified['category'],
            'url': url
        }
    )
    
    return {
        'id': activity_id,
        'category': classified['category'],
        'title': extracted['title']
    }