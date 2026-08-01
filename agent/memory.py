from typing import List, Dict, Any

class ConversationMemory:
    """
    Claude Agent의 세션별 대화 이력(State & Context Window) 관리 모듈.
    Claude Anthropic API 메시지 규격(user, assistant, tool_result 등)을 준수합니다.
    """
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, content: str) -> None:
        self.messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(self, content: Any) -> None:
        """Assistant 메시지 (단순 텍스트 또는 Blocks 목록/tool_use 포함)"""
        self.messages.append({
            "role": "assistant",
            "content": content
        })

    def add_tool_result_message(self, tool_use_id: str, content: str) -> None:
        """도구 실행 결과를 user 역할의 tool_result 컨텐츠 블록으로 추가"""
        self.messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content
                }
            ]
        })

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def clear(self) -> None:
        self.messages.clear()
