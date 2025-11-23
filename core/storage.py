"""
데이터베이스 관리
"""
import sqlite3
import json
from datetime import datetime, timedelta
from config.settings import DB_PATH
from utils import logger
from typing import Optional, Dict, List, Any
from .classifier import classify_content

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
            period_start DATE,      -- 시작 날짜
            period_end DATE,        -- 종료 날짜
            content TEXT,           -- Markdown 형식
            activity_count INTEGER, -- 포함된 활동 수
            metadata TEXT           -- JSON, 통계 등
        );
                         
        CREATE INDEX IF NOT EXISTS idx_briefing_created 
            ON briefing_history(created_at);
                    
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

def check_existing_activity(url: str) -> Optional[int]:
    """URL이 DB에 있는지 확인하고 ID 반환"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 중복 체크
    cursor.execute(
        "SELECT id FROM browsing_activity WHERE url = ?",
        (url,)
    )
    existing = cursor.fetchone()
    conn.close()
    
    # 중복 처리
    if existing:
        return existing[0] # 기존 Activity ID 반환
    
    return None

def save_activity(data: Dict[str, Any]) -> Optional[int]:
    """
    활동 저장
    
    Returns:
        int: activity_id (새로 생성 또는 기존 ID)
        None: 저장 실패
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tags_json = json.dumps(data.get('tags', []), ensure_ascii=False)
    metadata_json = json.dumps(data.get('metadata', {}), ensure_ascii=False)

    try:
        cursor.execute("""
            INSERT INTO browsing_activity 
               (url, domain, title, content, summary,
                category, tags, source_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['url'],
            data.get('domain'),
            data.get('title'),
            data.get('content'),
            data.get('summary'),
            data.get('category'),
            tags_json,
            data.get('source_type'),
            metadata_json
        ))

        conn.commit()
        activity_id = cursor.lastrowid

        logger.info(f"[OK] 저장 완료: ID {activity_id}")

        return activity_id
    
    except sqlite3.IntegrityError as e:
        logger.error(f"[FAIL] 무결성 에러: {e}")
        conn.rollback()
        return None
    
    except Exception as e:
        logger.error(f"[FAIL] 저장 실패: {e}")
        conn.rollback()
        return None
    
    finally:
        conn.close()

def get_activities(
        page: int =1,
        page_size: int = 10,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        start_date: Optional[str] = None,  
        end_date: Optional[str] = None,    
        tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    활동 조회 (필터링 지원)
    
    Args:
        page: ,
        page_size: ,
        category: 카테고리 필터
        source_type: 출처 유형 필터
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date : 종료 날짜 
        tags: 태그 필터 (리스트, OR 조건)
    
    Returns:
        {
            'total': int,
            'page': int,
            'page_size': int,
            'total_pages': int,
            'items': List[Dict]
        }
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM browsing_activity WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if source_type:
        query += " AND source_type = ?"
        params.append(source_type)
    
    if start_date and end_date:
        # 둘 다 있으면: BETWEEN
        query += " AND DATE(created_at) BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif start_date:
        # 시작일만: 그날 이후
        query += " AND DATE(created_at) >= ?"
        params.extend(start_date)
    elif end_date:
        # 종료일만: 그 날 이전
        query += " AND DATE(created_at) <= ?"
        params.append(end_date)

    if tags and len(tags) > 0:
        tag_conditions = []
        for tag in tags:
            tag_clean = tag.lstrip('#')  # # 제거
            tag_conditions.append("tags LIKE ?")
            params.append(f'%"{tag_clean}"%')

        query += " AND (" + " OR ".join(tag_conditions) + ")"

    # 전체 개수 조회
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # 페이지네이션
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.append(page_size)
    params.append((page - 1) * page_size)

    logger.debug(f"쿼리: {query}")
    logger.debug(f"파라미터: {params}")
    
    # 데이터 조회
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # dict 변환 + json 파싱 
    activities = []
    for row in rows:
        activity = dict(row)
        activity['tags'] = json.loads(activity['tags']) if activity['tags'] else []
        activity['metadata'] = json.loads(activity['metadata']) if activity['metadata'] else {}
        activity['created_at'] = activity['created_at'][:10]
        activities.append(activity)

    logger.info(
        f"활동 조회: {len(activities)}개 "
        f"(페이지: {page}/{(total + page_size - 1) // page_size}, "
        f"필터: 카테고리={category}, 날짜={start_date}~{end_date}, 태그={tags})"
    )

    return {
        "items": activities,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

def save_briefing(
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
    try:
        cursor.execute("""
            INSERT INTO briefing_history
            (period_start, period_end, content, activity_count, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (period_start, period_end, content, activity_count, metadata_json))
    except Exception as e:
        logger.error(f"브리핑 저장 실패: {e}")
    conn.commit()
    briefing_id = cursor.lastrowid
    conn.close()
    
    logger.info(f"브리핑 저장: (ID: {briefing_id})")
    return briefing_id

def get_briefings(limit: int = 10) -> List[Dict[str, Any]]:
    """브리핑 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * 
        FROM briefing_history
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

def get_activities_for_briefing(days: int=7) -> List[Dict[str, Any]]:
    """
    브리핑 생성을 위해 최근 활동 데이터 조회
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # created_at이 start_date 이후인 활동만 조회
    cursor.execute("""
        SELECT *
        FROM browsing_activity
        WHERE created_at >= ?
        ORDER BY created_at DESC
    """, (start_date,))

    rows = cursor.fetchall()
    conn.close()

    activities = []
    for row in rows:
        activity = dict(row)
        # 시간 정보를 제거하고 날짜만 남깁니다.
        activity['created_at'] = activity['created_at'].split(' ')[0] 
        activities.append(activity)

    return activities

def get_setting() -> list:
    """설정 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM user_settings WHERE key = 'user_topics'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return []


def set_setting(topics: list):
    """설정 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO user_settings (key, value, updated_at)
        VALUES ('user_topics', ?, CURRENT_TIMESTAMP)
    """, (json.dumps(topics)))
    
    conn.commit()
    conn.close()
    
    logger.debug(f"⚙️ 설정 저장: {topics}")

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
            updated = get_activity_by_id(activity_id)
            return updated
        else:
            logger.warning(f"활동 없음: ID {activity_id}")
            conn.close()
            return None
            
    except Exception as e:
        logger.error(f"업데이트 실패: {e}")
        conn.close()
        return None
    

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
    
def get_categories(date: Optional[str] = None) -> List[str]:
    """카테고리 목록 조회
    
    Args:
        date: 날짜 (None이면 전체 기간)
    
    Returns:
        List[str]: 카테고리 목록
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if date:
        # 특정 날짜의 카테고리만
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count
            FROM browsing_activity
            WHERE category IS NOT NULL
              AND DATE(created_at) = ?
            ORDER BY category
        """, (date,))

    else:
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count
            FROM browsing_activity
            WHERE category IS NOT NULL
            ORDER BY category
        """)

    rows = cursor.fetchall()
    conn.close()

    categories = [{"category": row[0], "count": row[1]} for row in rows]
    return categories

def get_tags(date: Optional[str] = None, category: Optional[str] = None, limit: int = 100) -> List[str]:
    """
    태그 목록만 조회 (최적화됨)
    - content, metadata 등 불필요한 컬럼 제외
    - tags 컬럼만 SELECT

    Args:
        date: 날짜 (None이면 전체 기간)
        category: 카테고리 필터 (None이면 전체)
        limit: 개수
    
    Returns:
        List[str]: 태그 목록
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT tags FROM browsing_activity WHERE tags IS NOT NULL"
    params = []
    
    # 날짜 필터
    if date:
        query += " AND DATE(created_at) = ?"
        params.append(date)
    
    # 카테고리 필터 추가
    if category:
        query += " AND category = ?"
        params.append(category)
    
    # query += " ORDER BY created_at DESC LIMIT ?"
    # params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    all_tags = set()
    for row in rows:
        try:
            tags_list = json.loads(row[0])
            if isinstance(tags_list, list):
                all_tags.update(tags_list)
        except (json.JSONDecodeError, TypeError):
            continue
    tags = sorted(list(all_tags))
    logger.debug(
        f"태그 조회: {len(tags[:limit])}개 "
        f"(날짜={date or '전체'}, 카테고리={category or '전체'})"
    )
    return tags[:limit]

def get_activity_metrics() -> Dict[str, Any]:
    """오늘의 활동 통계 (총 개수, 최다 카테고리, 카테고리 분포) 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().date().isoformat()
    last_seven_days = (datetime.now() - timedelta(days=7)).isoformat()

    # 오늘 총 활동수
    cursor.execute("SELECT COUNT(id) FROM browsing_activity WHERE DATE(created_at) = ?", (today,))
    total_count_today = cursor.fetchone()[0]

    # 오늘 최다 카테고리
    cursor.execute("""
        SELECT category, COUNT(category) as count
        FROM browsing_activity
        WHERE DATE(created_at) = ? AND category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """, (today,))
    top_category_row = cursor.fetchone()
    top_category = top_category_row[0] if top_category_row else "N/A"

    # 오늘 최다 태그
    cursor.execute("""
        SELECT tags 
        FROM browsing_activity 
        WHERE created_at >= ? AND tags IS NOT NULL
    """, (today,))
    tags_today = cursor.fetchall()

    all_tags = []
    for row in tags_today:
        try:
            tags_list = json.loads(row[0])
            all_tags.extend(tags_list)
        except:
            pass

    from collections import Counter
    tag_counts = Counter(all_tags)
    top_tag = f"#{tag_counts.most_common(1)[0][0]}" if tag_counts else "N/A"

    # 4. 카테고리 분포 (최근 7일 기준)
    cursor.execute("""
        SELECT category, COUNT(category) as count 
        FROM browsing_activity 
        WHERE created_at >= ? AND category IS NOT NULL
        GROUP BY category 
        ORDER BY count DESC
        LIMIT 5
    """, (last_seven_days,))
    
    category_rows = cursor.fetchall()
    total_activities_7d = sum([row[1] for row in category_rows])

    category_distribution = []
    for category, count in category_rows:
        percent = (count / total_activities_7d * 100) if total_activities_7d else 0
        category_distribution.append({
            "category": category,
            "count": count,
            "percent": round(percent)
        })

    conn.close()

    return {
        "total_count_today": total_count_today,
        "top_category": top_category,
        "top_tag": top_tag,
        "category_distribution": category_distribution
    }

def save_activity_with_ai(data: dict) -> int:
    """
    활동 저장 + AI 분류
    
    Args:
        data: {
            'url': str,
            'domain': str,
            'title': str,
            'content': str
        }
        
    Returns:
        activity_id
    """
    logger.info(f"활동 저장 (AI 분류 포함): {data.get('title')}")

    # AI 분류
    if data.get('content'):
        logger.info("   🤖 AI 분류 중...")
        ai_result = classify_content(
            data['title'],
            data['content']
        )
        
        # AI 결과 추가
        data['category'] = ai_result['category']
        data['tags'] = ai_result['tags']
        data['summary'] = ai_result['summary']
        
        logger.info(f"분류 완료: {ai_result['category']}")
    else:
        # AI 분류 실패 시 기본값
        data['category'] = 'Uncategorized'
        data['tags'] = []
        data['summary'] = data.get('title', 'No summary')
    
    logger.info(f"save_activity에 줄 data : {data}")
    
    return save_activity(data)

