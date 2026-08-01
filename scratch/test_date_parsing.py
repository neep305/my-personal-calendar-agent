from datetime import datetime
from agent.prompt import get_relative_date_info, build_system_prompt

now = datetime(2026, 7, 30, 22, 37)  # Thursday
info = get_relative_date_info(now)
print("=== 생성된 날짜 테이블 ===")
print(info)

print("\n=== System Prompt 확인 ===")
prompt_text = build_system_prompt("2026-07-30 22:37:00 (Thursday)")
assert "이번주 토요일: 2026-08-01" in prompt_text
print("✅ 날짜 검증 완료: 이번주 토요일 -> 2026-08-01 매핑 성공!")
