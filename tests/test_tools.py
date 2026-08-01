import pytest
import os
import json
from storage.db import init_db
from storage.calendar_repository import CalendarRepository
from tools.calendar_tools import create_event, check_conflicts
from tools.analytics_tools import get_free_slots

TEST_DB = "test_tools_calendar.db"

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_tool_create_and_conflict():
    repo = CalendarRepository(TEST_DB)
    
    # Repository 직접 또는 툴 함수 연동 검증
    created = repo.add_event(
        title="전략 회의",
        start_time="2026-07-31 10:00",
        end_time="2026-07-31 12:00"
    )
    assert created["title"] == "전략 회의"
    
    conflicts = repo.check_conflicts(
        start_time="2026-07-31 11:00",
        end_time="2026-07-31 13:00"
    )
    assert len(conflicts) == 1

def test_tool_get_free_slots():
    repo = CalendarRepository(TEST_DB)
    repo.add_event(
        title="전략 회의",
        start_time="2026-07-31 10:00",
        end_time="2026-07-31 12:00"
    )
    
    events = repo.search_events(start_date="2026-07-31 00:00", end_date="2026-07-31 23:59")
    assert len(events) == 1
