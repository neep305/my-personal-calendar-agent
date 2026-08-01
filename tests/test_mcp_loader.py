import os
import json
import tempfile
import pytest

from tools.mcp_loader import load_mcp_configuration

def test_load_mcp_configuration_fallback():
    """mcp.json 파일이 존재하지 않을 때 기본 calendar MCP만 정상 구성되는지 검증"""
    mcp_servers, allowed_tools = load_mcp_configuration("non_existent_file.json")
    
    assert "calendar" in mcp_servers
    assert "mcp__calendar__*" in allowed_tools

def test_load_mcp_configuration_valid_json():
    """mcp.json에 커스텀 MCP 및 allowed_tools 추가 시 정상 병합되는지 검증"""
    test_config = {
        "mcp_servers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "./storage"]
            }
        },
        "allowed_tools": [
            "mcp__calendar__*",
            "mcp__filesystem__*"
        ]
    }
    
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(test_config, f)
        temp_path = f.name
        
    try:
        mcp_servers, allowed_tools = load_mcp_configuration(temp_path)
        
        assert "calendar" in mcp_servers
        assert "filesystem" in mcp_servers
        assert mcp_servers["filesystem"]["command"] == "npx"
        assert "mcp__calendar__*" in allowed_tools
        assert "mcp__filesystem__*" in allowed_tools
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_load_mcp_configuration_env_substitute():
    """${ENV_VAR} 표기가 OS 환경변수 값으로 자동 치환되는지 검증"""
    os.environ["TEST_SLACK_TOKEN"] = "xoxb-test-12345"
    test_config = {
        "mcp_servers": {
            "slack": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-slack"],
                "env": {
                    "SLACK_BOT_TOKEN": "${TEST_SLACK_TOKEN}"
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(test_config, f)
        temp_path = f.name
        
    try:
        mcp_servers, allowed_tools = load_mcp_configuration(temp_path)
        assert "slack" in mcp_servers
        assert mcp_servers["slack"]["env"]["SLACK_BOT_TOKEN"] == "xoxb-test-12345"
    finally:
        del os.environ["TEST_SLACK_TOKEN"]
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_load_mcp_configuration_invalid_json():
    """깨진 JSON 파일이 입력되어도 예외가 발생하지 않고 기본 MCP로 복구되는지 검증"""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write("{ invalid json content ...")
        temp_path = f.name
        
    try:
        mcp_servers, allowed_tools = load_mcp_configuration(temp_path)
        
        assert "calendar" in mcp_servers
        assert "mcp__calendar__*" in allowed_tools
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
