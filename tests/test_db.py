import pytest
import os
from storage.db import init_db
from storage.calendar_repository import CalendarRepository

TEST_DB = "test_calendar.db"

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_and_get_event():
    repo = CalendarRepository(TEST_DB)
    event = repo.add_event(
        title="팀 주간 회의",
        start_time="2026-07-31 10:00",
        end_time="2026-07-31 11:00",
        description="프로젝트 진행상황 점검",
        location="회의실 A",
        attendees="홍길동, 김철수"
    )
    
    assert event is not None
    assert event["title"] == "팀 주간 회의"
    assert event["status"] == "scheduled"

def test_check_conflicts():
    repo = CalendarRepository(TEST_DB)
    repo.add_event(
        title="기존 회의",
        start_time="2026-07-31 14:00",
        end_time="2026-07-31 15:00"
    )
    
    # 겹치는 일정 검사
    conflicts = repo.check_conflicts("2026-07-31 14:30", "2026-07-31 16:00")
    assert len(conflicts) == 1
    assert conflicts[0]["title"] == "기존 회의"
    
    # 안 겹치는 일정 검사
    no_conflicts = repo.check_conflicts("2026-07-31 15:00", "2026-07-31 16:00")
    assert len(no_conflicts) == 0

def test_search_and_update():
    repo = CalendarRepository(TEST_DB)
    created = repo.add_event(
        title="디자인 리뷰",
        start_time="2026-08-01 13:00",
        end_time="2026-08-01 14:00"
    )
    
    search_res = repo.search_events(query="디자인")
    assert len(search_res) == 1
    
    updated = repo.update_event(created["id"], title="UI/UX 디자인 최종 리뷰")
    assert updated["title"] == "UI/UX 디자인 최종 리뷰"
    
    repo.delete_event(created["id"])
    active_res = repo.search_events(query="디자인", status="scheduled")
    assert len(active_res) == 0
