import os
import asyncio
from typing import Optional, Any
from claude_agent_sdk import query, ClaudeSDKClient, ClaudeAgentOptions

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
    AWS_REGION,
    BEDROCK_MODEL_ID,
    get_current_time_str
)
from agent.prompt import build_system_prompt
from agent.memory import ConversationMemory
from tools.mcp_loader import load_mcp_configuration

class ClaudeCalendarAgent:
    """
    공식 claude_agent_sdk 패키지 기반 개인 일정 관리 에이전트.
    In-process MCP Server와 mcp.json 기반 동적 MCP Server를 종합 활용합니다.
    """
    def __init__(
        self,
        model_id: Optional[str] = None,
        memory: Optional[ConversationMemory] = None,
        config_path: str = "mcp.json",
        skills: Optional[Any] = "all"
    ):
        self.model_id = model_id or BEDROCK_MODEL_ID
        self.memory = memory or ConversationMemory()
        self.config_path = config_path
        self.skills = skills
        
        # AWS Bedrock 및 SDK 라우팅 환경변수 설정
        os.environ["CLAUDE_CODE_USE_BEDROCK"] = "1"
        if AWS_REGION:
            os.environ["AWS_REGION"] = AWS_REGION
            os.environ["AWS_DEFAULT_REGION"] = AWS_REGION
        if AWS_ACCESS_KEY_ID:
            os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
        if AWS_SECRET_ACCESS_KEY:
            os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
        if AWS_SESSION_TOKEN:
            os.environ["AWS_SESSION_TOKEN"] = AWS_SESSION_TOKEN
        if self.model_id:
            os.environ["ANTHROPIC_MODEL"] = self.model_id

    def run(
        self,
        user_input: str,
        verbose: bool = True,
        debug: bool = False,
        on_event: Optional[Any] = None
    ) -> str:
        """
        비동기 claude_agent_sdk query 함수를 호출하여 에이전트를 수행합니다.
        """
        return asyncio.run(self._run_async(user_input, verbose=verbose, debug=debug, on_event=on_event))

    async def _run_async(
        self,
        user_input: str,
        verbose: bool = True,
        debug: bool = False,
        on_event: Optional[Any] = None
    ) -> str:
        current_time_str = get_current_time_str()
        system_prompt = build_system_prompt(current_time_str)
        
        # mcp.json 및 내장 MCP 서버 동적 수집
        mcp_servers, allowed_tools = load_mcp_configuration(self.config_path)
        
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools,
            skills=self.skills,
            setting_sources=["user", "project"],
            thinking={"type": "disabled"}
        )
        
        accumulated_texts = []
        final_result_text = None
        
        try:
            async for message in query(prompt=user_input, options=options):
                msg_type = message.__class__.__name__
                
                # 1. ResultMessage 처리
                if hasattr(message, "result") and isinstance(message.result, str) and message.result.strip():
                    final_result_text = message.result.strip()
                    if on_event:
                        on_event("result", final_result_text)
                
                # 2. Assistant / System 메시지 & 도구 호출 블록 파싱
                elif hasattr(message, "content"):
                    if isinstance(message.content, str) and message.content.strip():
                        text_val = message.content.strip()
                        if not accumulated_texts or accumulated_texts[-1] != text_val:
                            accumulated_texts.append(text_val)
                            if on_event:
                                on_event("thought", text_val)
                    elif isinstance(message.content, list):
                        for block in message.content:
                            block_type = block.__class__.__name__
                            
                            # Tool Use Block (도구 호출 요청)
                            if hasattr(block, "name") and hasattr(block, "input"):
                                tool_name = getattr(block, "name", "unknown")
                                tool_input = getattr(block, "input", {})
                                if on_event:
                                    on_event("tool_use", {"name": tool_name, "input": tool_input})
                            
                            # Tool Result Block (도구 실행 결과)
                            elif "ToolResult" in block_type or hasattr(block, "output"):
                                tool_out = getattr(block, "output", getattr(block, "content", str(block)))
                                if on_event:
                                    on_event("tool_result", tool_out)
                                    
                            # 일반 텍스트 추론 블록
                            elif hasattr(block, "text") and block.text.strip():
                                text_val = block.text.strip()
                                if not accumulated_texts or accumulated_texts[-1] != text_val:
                                    accumulated_texts.append(text_val)
                                    if on_event:
                                        on_event("thought", text_val)

        except Exception as e:
            if on_event:
                on_event("error", str(e))
            if not final_result_text and not accumulated_texts:
                raise e

        # ResultMessage가 있으면 이를 우선 사용하고, 없으면 수신된 텍스트 중 중복 없이 합쳐 반환
        if final_result_text:
            return final_result_text
            
        # 중복 문장 필터링
        unique_texts = []
        for t in accumulated_texts:
            if t not in unique_texts:
                unique_texts.append(t)
                
        return "\n\n".join(unique_texts) or "Schedule request has been processed."
