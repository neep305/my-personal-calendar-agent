import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from claude_agent_sdk import tool
from storage.calendar_repository import CalendarRepository

repo = CalendarRepository()

# ---------------------------------------------------------------------------
# Pydantic Schemas for Input Validation
# ---------------------------------------------------------------------------

class SearchEventsInput(BaseModel):
    query: Optional[str] = Field(None, description="검색 키워드")
    start_date: Optional[str] = Field(None, description="시작일시 (YYYY-MM-DD HH:MM 또는 YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료일시 (YYYY-MM-DD HH:MM 또는 YYYY-MM-DD)")
    status: str = Field("scheduled", description="상태 ('scheduled' 또는 'cancelled')")

class CheckConflictsInput(BaseModel):
    start_time: str = Field(..., description="시작 시각 (YYYY-MM-DD HH:MM)")
    end_time: str = Field(..., description="종료 시각 (YYYY-MM-DD HH:MM)")
    exclude_event_id: Optional[int] = Field(None, description="제외할 일정 ID")

class CreateEventInput(BaseModel):
    title: str = Field(..., description="일정 제목")
    start_time: str = Field(..., description="시작 일시 (YYYY-MM-DD HH:MM)")
    end_time: str = Field(..., description="종료 일시 (YYYY-MM-DD HH:MM)")
    description: Optional[str] = Field("", description="상세 설명")
    location: Optional[str] = Field("", description="장소 또는 미팅 링크")
    attendees: Optional[str] = Field("", description="참석자 목록")

class UpdateEventInput(BaseModel):
    event_id: int = Field(..., description="수정할 일정 ID")
    title: Optional[str] = Field(None, description="변경할 제목")
    start_time: Optional[str] = Field(None, description="변경할 시작 일시")
    end_time: Optional[str] = Field(None, description="변경할 종료 일시")
    description: Optional[str] = Field(None, description="변경할 설명")
    location: Optional[str] = Field(None, description="변경할 장소")
    attendees: Optional[str] = Field(None, description="변경할 참석자")

class DeleteEventInput(BaseModel):
    event_id: int = Field(..., description="취소/삭제할 일정 ID")
    hard_delete: bool = Field(False, description="True인 경우 완전 삭제")


# ---------------------------------------------------------------------------
# SDK Tools Registration
# ---------------------------------------------------------------------------

@tool("search_events", "조건(키워드, 날짜 범위, 상태 등)에 맞는 일정을 검색합니다.", SearchEventsInput)
async def search_events(args: dict) -> dict:
    events = repo.search_events(
        query=args.get("query"),
        start_date=args.get("start_date"),
        end_date=args.get("end_date"),
        status=args.get("status", "scheduled")
    )
    return {"content": [{"type": "text", "text": json.dumps({"count": len(events), "events": events}, ensure_ascii=False)}]}

@tool("check_conflicts", "특정 시간대(start_time ~ end_time)에 이미 다른 일정이 존재하는지 충돌 여부를 검사합니다.", CheckConflictsInput)
async def check_conflicts(args: dict) -> dict:
    conflicts = repo.check_conflicts(
        start_time=args["start_time"],
        end_time=args["end_time"],
        exclude_event_id=args.get("exclude_event_id")
    )
    has_conflict = len(conflicts) > 0
    return {"content": [{"type": "text", "text": json.dumps({"has_conflict": has_conflict, "conflict_count": len(conflicts), "conflicts": conflicts}, ensure_ascii=False)}]}

@tool("create_event", "신규 일정을 수립하여 등록합니다. 등록 전 check_conflicts 툴로 시간 충돌을 먼저 확인하세요.", CreateEventInput)
async def create_event(args: dict) -> dict:
    event = repo.add_event(
        title=args["title"],
        start_time=args["start_time"],
        end_time=args["end_time"],
        description=args.get("description", ""),
        location=args.get("location", ""),
        attendees=args.get("attendees", "")
    )
    return {"content": [{"type": "text", "text": json.dumps({"success": True, "message": "Event successfully created.", "event": event}, ensure_ascii=False)}]}

@tool("update_event", "기존 일정의 ID를 참조하여 일정을 수정합니다.", UpdateEventInput)
async def update_event(args: dict) -> dict:
    updated = repo.update_event(
        event_id=args["event_id"],
        title=args.get("title"),
        start_time=args.get("start_time"),
        end_time=args.get("end_time"),
        description=args.get("description"),
        location=args.get("location"),
        attendees=args.get("attendees")
    )
    if not updated:
        return {"content": [{"type": "text", "text": json.dumps({"success": False, "message": f"Event ID {args['event_id']} not found."}, ensure_ascii=False)}]}
    return {"content": [{"type": "text", "text": json.dumps({"success": True, "message": "Event successfully updated.", "event": updated}, ensure_ascii=False)}]}

@tool("delete_event", "일정을 취소하거나 완전히 삭제합니다.", DeleteEventInput)
async def delete_event(args: dict) -> dict:
    success = repo.delete_event(event_id=args["event_id"], hard_delete=args.get("hard_delete", False))
    if not success:
        return {"content": [{"type": "text", "text": json.dumps({"success": False, "message": f"Event ID {args['event_id']} not found."}, ensure_ascii=False)}]}
    return {"content": [{"type": "text", "text": json.dumps({"success": True, "message": "Event successfully cancelled/deleted."}, ensure_ascii=False)}]}
