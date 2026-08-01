import os
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def clean_env_var(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    cleaned = val.split('#')[0].strip()
    return cleaned if cleaned else None

AWS_ACCESS_KEY_ID = clean_env_var(os.getenv("AWS_ACCESS_KEY_ID")) or ""
AWS_SECRET_ACCESS_KEY = clean_env_var(os.getenv("AWS_SECRET_ACCESS_KEY")) or ""
AWS_SESSION_TOKEN = clean_env_var(os.getenv("AWS_SESSION_TOKEN"))
AWS_REGION = clean_env_var(os.getenv("AWS_REGION")) or "us-west-2"
BEDROCK_MODEL_ID = clean_env_var(os.getenv("BEDROCK_MODEL_ID")) or "us.anthropic.claude-sonnet-4-20250514-v1:0"

DB_PATH = clean_env_var(os.getenv("DB_PATH")) or "calendar.db"

def get_current_datetime() -> datetime:
    """현재 날짜 및 시간 반환 (시연 시 시스템 시간 사용)"""
    return datetime.now()

def get_current_time_str() -> str:
    """ISO 8601 포맷 또는 사람이 읽기 편한 현재 시각 문자열"""
    now = get_current_datetime()
    return now.strftime("%Y-%m-%d %H:%M:%S (%A)")
