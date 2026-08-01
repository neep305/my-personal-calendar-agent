import traceback
from agent.core import ClaudeCalendarAgent

try:
    agent = ClaudeCalendarAgent()
    res = agent.run("안녕! 오늘 일정 알려줘.", verbose=True)
    print("\n✅ claude_agent_sdk 성공 응답:\n", res)
except Exception as e:
    print("디버그 실패:")
    traceback.print_exc()
