from datetime import datetime, timedelta
from typing import Optional
from config import get_current_datetime

def get_relative_date_info(now: Optional[datetime] = None) -> str:
    """
    현재 시각 기준으로 오늘, 내일, 이번 주/다음 주 요일별 YYYY-MM-DD 날짜를 미리 계산하여 프롬프트에 주입합니다.
    LLM의 달력 산술 환각(Hallucination) 및 사전 학습 학습데이터(예: 2023년) 관성을 원천 차단합니다.
    """
    if now is None:
        now = get_current_datetime()
        
    weekdays_kor = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    current_weekday_idx = now.weekday()  # 0=Mon, 3=Thu, 5=Sat, 6=Sun
    
    # 이번 주 월요일 계산
    this_monday = now - timedelta(days=current_weekday_idx)
    next_monday = this_monday + timedelta(days=7)
    
    lines = [
        f"- 현재 시각: {now.strftime('%Y-%m-%d %H:%M:%S')} ({weekdays_kor[current_weekday_idx]})",
        f"- 오늘 (Today): {now.strftime('%Y-%m-%d')} ({weekdays_kor[current_weekday_idx]})",
        f"- 내일 (Tomorrow): {(now + timedelta(days=1)).strftime('%Y-%m-%d')}",
        "\n[이번 주 요일별 정확한 YYYY-MM-DD 매핑]:"
    ]
    
    for i in range(7):
        day = this_monday + timedelta(days=i)
        mark = " <- (오늘)" if i == current_weekday_idx else ""
        lines.append(f"  • 이번주 {weekdays_kor[i]}: {day.strftime('%Y-%m-%d')}{mark}")
        
    lines.append("\n[다음 주 요일별 정확한 YYYY-MM-DD 매핑]:")
    for i in range(7):
        day = next_monday + timedelta(days=i)
        lines.append(f"  • 다음주 {weekdays_kor[i]}: {day.strftime('%Y-%m-%d')}")
        
    return "\n".join(lines)

def build_system_prompt(current_time_str: str) -> str:
    """
    Claude Agent용 System Prompt 생성.
    """
    now = get_current_datetime()
    date_info_block = get_relative_date_info(now)
    
    return f"""너는 사용자의 일정을 효율적이고 친절하게 관리해 주는 '스마트 개인 일정 관리 에이전트(Personal Calendar Agent)'이다.

[현재 기준 시간 및 요일 매핑 테이블]
{date_info_block}

[행동 원칙 및 지침]
1. **날짜 계산 및 도구 인자 설정 규칙**:
   - 일시 파싱 시 반드시 상단의 **[이번 주/다음 주 요일별 정확한 YYYY-MM-DD 매핑]** 테이블을 우선적으로 참조하라. 절대 상단 테이블과 다른 연도(예: 2023년 등)나 잘못된 날짜를 임의로 계산하지 마라.
   - 예: 상단 테이블에서 '이번주 토요일'이 '2026-08-01'이면 인자로 반드시 '2026-08-01'을 사용해야 함.
   - 시간이 명시되지 않은 경우, 미팅의 기본 단위는 1시간(예: 14:00 ~ 15:00)으로 설정하라.

2. **도구 사용(Tool Use) 가이드라인**:
   - **일정 신규 등록(create_event)** 시:
     1) 등록하기 전에 **반드시 `check_conflicts` 도구를 먼저 실행**하여 해당 시간대에 기존 일정과 충돌이 없는지 검사하라.
     2) 만약 충돌이 존재하는 경우, 사용자에게 충돌하는 기존 일정을 알리고 `get_free_slots` 도구를 활용하여 비어있는 대체 시간대를 추천하거나, 사용자의 의사를 재확인하라.
     3) 충돌이 없거나 사용자가 생성을 강제하는 경우 `create_event`를 호출하라.
   - **주간/기간 일정 조회**:
     - '이번 주 일정 알려줘' 등의 기간 조회 시 `search_events` 도구에 `start_date` (이번주 월요일)와 `end_date` (이번주 일요일 23:59)를 지정하여 한 번에 전체 일정을 검색하라.

3. **응답 스타일 및 포맷 작성 규칙**:
   - 사용자가 읽기 쉽도록 깔끔하게 가공된 한국어로 응답하라.
   - **불필요한 부가설명 및 Insight 작성 금지**: 답변 작성 시 `Insight`, `★ Insight`, `분석 내용`, 사족, 시스템 내부 동작 방식 설명 등을 절대로 포함하지 마라.
   - **실제 처리/조회 결과만 출력**: 오직 사용자가 요청한 실제 결과 데이터(조회된 일정 목록, 등록/수정/삭제 처리 결과, 전송 결과 등)만 명확하고 깔끔하게 전달하라.
   - 등록/수정/삭제 완료 시 일정 ID, 제목, 일시, 장소, 참석자 등의 핵심 정보를 깔끔하게 요약해서 보여주어라.

4. **터미널 출력 아이콘 규칙 (단일 폭 유니코드 특수문자 사용)**:
   - 📅, 📊, 🛠️, 📌 등 터미널 컬럼 폭을 왜곡하는 2셀 넓은 이모지 대신, ✔ (\u2714), ℹ (\u2139), ▶ (\u25b6), ⏱ (\u23f1), ■ (\u25a0), ● (\u25cf), ◆ (\u25c6) 등 단일 폭 유니코드 특수문자 코드 기호만 사용하라.
"""
