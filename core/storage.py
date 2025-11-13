"""
데이터베이스 관리
"""
import sqlite3
import json
from pathlib import Path
from config.settings import DB_PATH
from utils import logger
from typing import Optional, Dict, List, Any

def init_db():
    """데이터베이스 초기화"""
    logger.info("데이터베이스 초기화 시작")

    # 폴더 생성
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 테이블 생성
    cursor.executescript("""
        -- 메인 활동 테이블
        CREATE TABLE IF NOT EXISTS browsing_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- URL 정보
            url TEXT NOT NULL UNIQUE,
            domain TEXT,
                         
            -- 메타데이터 
            author TEXT,
            publish_date TEXT,
                         
            -- content
            title TEXT,
            content TEXT,  -- 전체 본문
            summary TEXT,  -- 요약본
                         
            -- 분류
            category TEXT,  -- 주제 (RAG, LangGraph, FastAPI...) 
            tags TEXT,     -- JSON 배열
            source_type TEXT,  -- 출처 유형 (blog, youtube, docs...) 
            
            -- 추가 정보
            metadata TEXT      -- JSON, 추가 정보    
        );
                         
        -- 인덱스 생성 (검색속도 향상)
        CREATE INDEX IF NOT EXISTS idx_created_at
            ON browsing_activity(created_at);
                    
        CREATE INDEX IF NOT EXISTS idx_category
            ON browsing_activity(category);
                         
        CREATE INDEX IF NOT EXISTS idx_source_type
            ON browsing_activity(source_type);

        CREATE INDEX IF NOT EXISTS idx_domain
            ON browsing_activity(domain);            
                    
        -- 브리핑 히스토리
        CREATE TABLE IF NOT EXISTS briefing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            briefing_type TEXT,     -- 'daily', 'weekly'
            period_start DATE,      -- 시작 날짜
            period_end DATE,        -- 종료 날짜
            content TEXT,           -- Markdown 형식
            activity_count INTEGER, -- 포함된 활동 수
            metadata TEXT           -- JSON, 통계 등
        );
                         
        CREATE INDEX IF NOT EXISTS idx_briefing_created 
            ON briefing_history(created_at);
            
        CREATE INDEX IF NOT EXISTS idx_briefing_type 
            ON briefing_history(briefing_type);
                    
        -- 사용자 설정 
        CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()

    logger.info(f"데이터 베이스 생성 완료: {DB_PATH}")

def save_activity(data: dict) -> int:
    """활동 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tags_json = json.dumps(data.get('tags', []), ensure_ascii=False)
    metadata_json = json.dumps(data.get('metadata', {}), ensure_ascii=False)

    try:
        cursor.execute("""
            INSERT INTO browsing_activity 
               (url, domain, title, content, summary, author, publish_date,
                category, tags, source_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['url'],
            data.get('domain'),
            data.get('title'),
            data.get('content'),
            data.get('summary'),
            data.get('author'),
            data.get('publish_date'),
            data.get('category'),
            tags_json,
            data.get('source_type'),
            metadata_json
        ))

        conn.commit()
        activity_id = cursor.lastrowid

        logger.info(f"활동 저장: {data.get('title')} (ID : {activity_id})")
        return activity_id
    
    except Exception as e:
        logger.warning(f"⚠️ 중복 URL: {data['url']}")
        return None
    
    finally:
        conn.close()

def get_activities(
        limit: int = 10,
        category: Optional[str] = None,
        source_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """활동 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 쿼리 구성  -> 좀 더 편하게 뒤를 붙이기 위해 참인 조건 1=1 넣음, 뒤에 띄어쓰기!!
    query = "SELECT * FROM browsing_activity WHERE 1=1 "
    params = []

    if category:
        query += "AND category = ?"
        params.append(category)

    if source_type:
        query += "AND source_type = ?"
        params.append(source_type)

    query += "ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()    # 결과 가져오기
    conn.close()

    # dict 변환 + json 파싱 
    activities = []
    for row in rows:
        activity = dict(row)
        activity['tags'] = json.loads(activity['tags']) if activity['tags'] else []
        activity['metadata'] = json.loads(activity['metadata']) if activity['metadata'] else {}
        activities.append(activity)

    return activities

def save_briefing(
    briefing_type: str,
    period_start: str,
    period_end: str,
    content: str,
    activity_count: int,
    metadata: dict = None
) -> int:
    """브리핑 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

    cursor.execute("""
        INSERT INTO briefing_history
        (briefing_type, period_start, period_end, content, activity_count, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (briefing_type, period_start, period_end, content, activity_count, metadata_json))
    
    conn.commit()
    briefing_id = cursor.lastrowid
    conn.close()
    
    logger.info(f"브리핑 저장: {briefing_type} (ID: {briefing_id})")
    return briefing_id

def get_briefings(limit: int = 10) -> List[Dict[str, Any]]:
    """브리핑 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM briefing_history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    briefings = []
    for row in rows:
        briefing = dict(row)
        briefing['metadata'] = json.loads(briefing['metadata']) if briefing['metadata'] else {}
        briefings.append(briefing)

    return briefings

def get_setting(key: str, default: Any = None) -> Any:
    """설정 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return default


def set_setting(key: str, value: Any):
    """설정 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO user_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (key, str(value)))
    
    conn.commit()
    conn.close()
    
    logger.debug(f"⚙️ 설정 저장: {key} = {value}")

def search_by_keyword(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """키워드로 활동 검색 (제목, 본문, 태그, 카테고리)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    search_pattern = f"%{keyword}%"

    cursor.execute("""
        SELECT * FROM browsing_activity 
        WHERE title LIKE ?
            OR content LIKE ?
            OR tags LIKE ?
            OR category LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))

    rows = cursor.fetchall()
    conn.close()

    # dict 변환
    activities = []
    for row in rows:
        activity = dict(row)
        activity['tags'] = json.loads(activity['tags']) if activity['tags'] else []
        activity['metadata'] = json.loads(activity['metadata']) if activity['metadata'] else {}
        activities.append(activity)
    
    logger.info(f"검색 완료: '{keyword}' - {len(activities)}개 결과")
    return activities

def get_activity_by_id(activity_id: int) -> Optional[Dict[str, Any]]:
    """ID로 활동 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM browsing_activity WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        activity = dict(row)
        activity['tags'] = json.loads(activity['tags']) if activity['tags'] else []
        activity['metadata'] = json.loads(activity['metadata']) if activity['metadata'] else {}
        return activity
    
    return None

def update_activity(activity_id: int, data: dict) -> bool:
    """활동 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 업데이트할 필드만 처리
    updates = []
    values = []

    if 'title' in data:
        updates.append("title = ?")
        values.append(data['title'])
    
    if 'summary' in data:
        updates.append("summary = ?")
        values.append(data['summary'])
    
    if 'category' in data:
        updates.append("category = ?")
        values.append(data['category'])
    
    if 'tags' in data:
        updates.append("tags = ?")
        values.append(json.dumps(data['tags'], ensure_ascii=False))
    
    if 'source_type' in data:
        updates.append("source_type = ?")
        values.append(data['source_type'])
    
    if not updates:
        logger.warning("업데이트할 필드 없음")
        conn.close()
        return False
    
    query = f"UPDATE browsing_activity SET {', '.join(updates)} WHERE id = ?"
    values.append(activity_id)

    try:
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"활동 업데이트: ID {activity_id}")
            conn.close()
            return True
        else:
            logger.warning(f"활동 없음: ID {activity_id}")
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"업데이트 실패: {e}")
        conn.close()
        return False
    

def delete_activity(activity_id: int) -> bool:
    """활동 삭제"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM browsing_activity WHERE id = ?", (activity_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"활동 삭제: ID {activity_id}")
            conn.close()
            return True
        else:
            logger.warning(f"활동 없음: ID {activity_id}")
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"삭제 실패: {e}")
        conn.close()
        return False
    
def get_categories() -> List[str]:
    """모든 카테고리 반환"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT category
        FROM browsing_activity
        WHERE category IS NOT NULL
        ORDER BY category
    """)

    rows = cursor.fetchall()
    conn.close()

    categories = [row[0] for row in rows]
    return categories

def get_stats() -> Dict[str, Any]:
    """통계 정보"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 총 활동수
    cursor.execute("SELECT COUNT(*) FROM browsing_activity")
    total = cursor.fetchone()[0]

    # 총 카테고리수 
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM browsing_activity
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """)
    categories = {row[0]: row[1] for row in cursor.fetchall()}

    # 소스 타입 별 수 
    cursor.execute("""
        SELECT source_type, COUNT(*) as count
        FROM browsing_activity
        WHERE source_type IS NOT NULL
        GROUP BY source_type
        ORDER BY count DESC
    """)
    source_types = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {
        'total': total,
        'categories': categories,
        'source_types': source_types
    }

if __name__ == "__main__":
    print("🧪 Storage 테스트\n")
    print("=" * 60)
    
    # 1. DB 초기화
    print("\n1️⃣ 데이터베이스 초기화...")
    init_db()
    
    # 2. 활동 저장 테스트
    print("\n2️⃣ 활동 저장 테스트...")
    test_activity = {
        'url': 'https://example.com/test-article',
        'domain': 'example.com',
        'title': '테스트 아티클',
        'content': '이것은 테스트 내용입니다. ' * 50,
        'summary': '테스트 요약문입니다.',
        'author': 'Test Author',
        'publish_date': '2025-11-13',
        'category': 'Test',
        'tags': ['test', 'example', 'demo'],
        'source_type': 'blog',
        'metadata': {'lang': 'ko', 'difficulty': 'easy'}
    }
    
    activity_id = save_activity(test_activity)
    print(f"   저장 완료: ID {activity_id}")
    
    # 3. 활동 조회 테스트
    print("\n3️⃣ 활동 조회 테스트...")
    activities = get_activities(limit=5)
    print(f"   조회된 활동: {len(activities)}개")
    for act in activities:
        print(f"   - {act['title']} ({act['category']}) - {len(act['tags'])} tags")
    
    # 4. 브리핑 저장 테스트
    print("\n4️⃣ 브리핑 저장 테스트...")
    briefing_id = save_briefing(
        briefing_type='daily',
        period_start='2025-11-13',
        period_end='2025-11-13',
        content='# 오늘의 요약\n\n- 1개 문서 저장\n- 주제: Test',
        activity_count=1,
        metadata={'total_words': 1000}
    )
    print(f"   브리핑 저장: ID {briefing_id}")
    
    # 5. 설정 테스트
    print("\n5️⃣ 설정 테스트...")
    set_setting('theme', 'dark')
    set_setting('language', 'ko')
    
    theme = get_setting('theme')
    language = get_setting('language')
    print(f"   theme: {theme}")
    print(f"   language: {language}")
    
    # 완료
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")
    print(f"📁 DB 위치: {DB_PATH}")