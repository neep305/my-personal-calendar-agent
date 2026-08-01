import json
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from claude_agent_sdk import tool
from storage.calendar_repository import CalendarRepository

repo = CalendarRepository()

class FreeSlotsInput(BaseModel):
    date: str = Field(..., description="조회할 날짜 (YYYY-MM-DD)")
    duration_minutes: int = Field(60, description="필요한 최소 시간(분 단위)")
    work_start_hour: int = Field(9, description="업무 시작 시간(기본 9)")
    work_end_hour: int = Field(18, description="업무 종료 시간(기본 18)")

class DailyBriefingInput(BaseModel):
    date: str = Field(..., description="브리핑을 조회할 날짜 (YYYY-MM-DD)")

@tool("get_free_slots", "특정 날짜의 업무 시간 내 빈 시간 슬롯을 계산합니다.", FreeSlotsInput)
async def get_free_slots(args: dict) -> dict:
    date_str = args["date"]
    duration = args.get("duration_minutes", 60)
    work_start_h = args.get("work_start_hour", 9)
    work_end_h = args.get("work_end_hour", 18)
    
    day_start = f"{date_str} 00:00"
    day_end = f"{date_str} 23:59"
    events = repo.search_events(start_date=day_start, end_date=day_end, status="scheduled")
    
    work_start_dt = datetime.strptime(f"{date_str} {work_start_h:02d}:00", "%Y-%m-%d %H:%M")
    work_end_dt = datetime.strptime(f"{date_str} {work_end_h:02d}:00", "%Y-%m-%d %H:%M")
    
    current_time = work_start_dt
    free_slots = []
    
    parsed_events = []
    for ev in events:
        try:
            s_dt = datetime.strptime(ev["start_time"], "%Y-%m-%d %H:%M")
            e_dt = datetime.strptime(ev["end_time"], "%Y-%m-%d %H:%M")
            parsed_events.append((max(s_dt, work_start_dt), min(e_dt, work_end_dt)))
        except ValueError:
            continue
            
    parsed_events.sort(key=lambda x: x[0])
    
    for s_dt, e_dt in parsed_events:
        if s_dt > current_time:
            gap = int((s_dt - current_time).total_seconds() / 60)
            if gap >= duration:
                free_slots.append({
                    "start_time": current_time.strftime("%Y-%m-%d %H:%M"),
                    "end_time": s_dt.strftime("%Y-%m-%d %H:%M"),
                    "duration_minutes": gap
                })
        if e_dt > current_time:
            current_time = e_dt
            
    if work_end_dt > current_time:
        gap = int((work_end_dt - current_time).total_seconds() / 60)
        if gap >= duration:
            free_slots.append({
                "start_time": current_time.strftime("%Y-%m-%d %H:%M"),
                "end_time": work_end_dt.strftime("%Y-%m-%d %H:%M"),
                "duration_minutes": gap
            })
            
    res = {
        "date": date_str,
        "required_duration_minutes": duration,
        "free_slots_count": len(free_slots),
        "free_slots": free_slots
    }
    return {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}

@tool("get_daily_briefing", "특정 날짜의 전체 일정을 시간순으로 요약 브리핑 데이터를 반환합니다.", DailyBriefingInput)
async def get_daily_briefing(args: dict) -> dict:
    date_str = args["date"]
    day_start = f"{date_str} 00:00"
    day_end = f"{date_str} 23:59"
    events = repo.search_events(start_date=day_start, end_date=day_end, status="scheduled")
    
    res = {
        "date": date_str,
        "total_events": len(events),
        "events": events
    }
    return {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}
