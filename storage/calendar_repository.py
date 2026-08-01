from typing import List, Dict, Any, Optional
from datetime import datetime
from storage.db import get_connection

class CalendarRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def add_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = "",
        location: Optional[str] = "",
        attendees: Optional[str] = ""
    ) -> Dict[str, Any]:
        """새로운 일정을 저장소에 추가합니다."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO events (title, description, start_time, end_time, location, attendees, status)
            VALUES (?, ?, ?, ?, ?, ?, 'scheduled')
            """,
            (title, description or "", start_time, end_time, location or "", attendees or "")
        )
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        
        return self.get_event_by_id(event_id)

    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """ID로 일정을 조회합니다."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def search_events(
        self,
        query: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: str = "scheduled"
    ) -> List[Dict[str, Any]]:
        """조건에 맞춰 일정을 검색합니다."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        sql = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if status:
            sql += " AND status = ?"
            params.append(status)
            
        if query:
            sql += " AND (title LIKE ? OR description LIKE ? OR attendees LIKE ? OR location LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q, q])
            
        if start_date:
            sql += " AND end_time >= ?"
            params.append(start_date)
            
        if end_date:
            sql += " AND start_time <= ?"
            params.append(end_date)
            
        sql += " ORDER BY start_time ASC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]

    def check_conflicts(
        self,
        start_time: str,
        end_time: str,
        exclude_event_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        주어진 시간 범위(start_time ~ end_time)와 겹치는 기존 일정을 확인합니다.
        시간 겹침 조건: (ExistingStart < NewEnd) AND (ExistingEnd > NewStart)
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        sql = """
            SELECT * FROM events 
            WHERE status = 'scheduled'
            AND start_time < ? 
            AND end_time > ?
        """
        params = [end_time, start_time]
        
        if exclude_event_id:
            sql += " AND id != ?"
            params.append(exclude_event_id)
            
        sql += " ORDER BY start_time ASC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]

    def update_event(
        self,
        event_id: int,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """일정을 업데이트합니다."""
        existing = self.get_event_by_id(event_id)
        if not existing:
            return None
            
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        fields = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "location": location,
            "attendees": attendees,
            "status": status
        }
        
        for k, v in fields.items():
            if v is not None:
                updates.append(f"{k} = ?")
                params.append(v)
                
        if not updates:
            return existing
            
        params.append(event_id)
        sql = f"UPDATE events SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        
        return self.get_event_by_id(event_id)

    def delete_event(self, event_id: int, hard_delete: bool = False) -> bool:
        """일정을 취소/삭제합니다."""
        existing = self.get_event_by_id(event_id)
        if not existing:
            return False
            
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        if hard_delete:
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        else:
            cursor.execute("UPDATE events SET status = 'cancelled' WHERE id = ?", (event_id,))
            
        conn.commit()
        conn.close()
        return True
