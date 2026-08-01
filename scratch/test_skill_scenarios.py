import traceback
from agent.core import ClaudeCalendarAgent

def run_test():
    print("==================================================")
    print("[TEST] Personal Calendar Agent - Skill Integration Test")
    print("==================================================\n")
    
    agent = ClaudeCalendarAgent(skills=["calendar-smart-scheduler"])

    def print_event(event_type, data):
        if event_type == "tool_use":
            print(f"  [TOOL CALL] {data['name']}: {data['input']}")
        elif event_type == "thought":
            print(f"  [THOUGHT] {data[:80]}...")

    # 시나리오 1: 사전 충돌 검사 및 정상 등록
    print("--- [SCENARIO 1] 신규 일정 등록 및 사전 충돌 검사 ---")
    prompt1 = "다음주 화요일 오후 2시에 '팀 프로젝트 주간회의' 일정 등록해줘. 장소는 회의실A, 참석자는 철수와 영희야."
    print(f"사용자 요청: {prompt1}\n")
    res1 = agent.run(prompt1, on_event=print_event)
    print(f"\n[AGENT RESPONSE]:\n{res1}\n")

    # 시나리오 2: 일정 충돌 감지 및 대체 시간 제안
    print("--- [SCENARIO 2] 일정 충돌 감지 및 대체 시간 추천 ---")
    prompt2 = "다음주 화요일 오후 2시에 '고객사 디딤돌 미팅' 일정 잡아줘."
    print(f"사용자 요청: {prompt2}\n")
    res2 = agent.run(prompt2, on_event=print_event)
    print(f"\n[AGENT RESPONSE]:\n{res2}\n")

    # 시나리오 3: 주간 일정 검색 및 표준 카드 출력
    print("--- [SCENARIO 3] 이번주 일정 검색 및 정리 ---")
    prompt3 = "이번주 전체 일정 알려줘."
    print(f"사용자 요청: {prompt3}\n")
    res3 = agent.run(prompt3, on_event=print_event)
    print(f"\n[AGENT RESPONSE]:\n{res3}\n")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print("[ERROR] 테스트 중 예외 발생:")
        traceback.print_exc()
