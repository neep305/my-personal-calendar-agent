import json
import os
import re
from typing import Dict, List, Any, Tuple
from claude_agent_sdk import create_sdk_mcp_server

from tools import calendar_mcp_server

DEFAULT_CONFIG_PATH = "mcp.json"

def _substitute_env_vars(data: Any) -> Any:
    """
    JSON 구조 내부의 ${ENV_VAR_NAME} 문자열을 OS 환경변수 값으로 자동 치환합니다.
    환경변수가 없을 경우 원래 ${ENV_VAR_NAME} 문자열 그대로 유지됩니다.
    """
    if isinstance(data, dict):
        return {k: _substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        pattern = re.compile(r"\$\{([^}]+)\}")
        def replace_match(match):
            env_var_name = match.group(1)
            return os.environ.get(env_var_name, match.group(0))
        return pattern.sub(replace_match, data)
    return data

def load_mcp_configuration(config_path: str = DEFAULT_CONFIG_PATH) -> Tuple[Dict[str, Any], List[str]]:
    """
    mcp.json 파일에서 사용자가 정의한 MCP 서버 및 allowed_tools 설정을 동적으로 로드합니다.
    JSON 내부의 ${VAR_NAME} 형태는 OS 환경 변수로 스마트 자동 치환됩니다.
    
    :param config_path: mcp.json 파일 경로
    :return: (mcp_servers_dict, allowed_tools_list)
    """
    # 1. 기본 내장 In-Process MCP 서버 및 allowed_tools 준비
    mcp_servers: Dict[str, Any] = {
        "calendar": calendar_mcp_server
    }
    allowed_tools: List[str] = ["mcp__calendar__*"]
    
    # 2. mcp.json 존재 여부 확인
    if not os.path.exists(config_path):
        return mcp_servers, allowed_tools
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        # 스마트 환경 변수 치환 (${ENV_VAR})
        user_config = _substitute_env_vars(raw_data)
            
        # 3. 유저 정의 mcp_servers 병합
        user_servers = user_config.get("mcp_servers", {})
        if isinstance(user_servers, dict):
            for server_name, server_spec in user_servers.items():
                if server_name != "calendar":
                    mcp_servers[server_name] = server_spec
                    
        # 4. 유저 정의 allowed_tools 병합
        user_tools = user_config.get("allowed_tools", [])
        if isinstance(user_tools, list):
            for tool_pattern in user_tools:
                if isinstance(tool_pattern, str) and tool_pattern not in allowed_tools:
                    allowed_tools.append(tool_pattern)
                    
    except Exception as e:
        print(f"⚠️ [MCP Loader] '{config_path}' 읽기 중 경고 발생: {e}. 기본 내장 MCP로 구동합니다.")
        
    return mcp_servers, allowed_tools
