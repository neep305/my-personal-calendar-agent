from claude_agent_sdk import create_sdk_mcp_server

from tools.calendar_tools import (
    search_events,
    check_conflicts,
    create_event,
    update_event,
    delete_event
)
from tools.analytics_tools import (
    get_free_slots,
    get_daily_briefing
)

ALL_SDK_TOOLS = [
    search_events,
    check_conflicts,
    create_event,
    update_event,
    delete_event,
    get_free_slots,
    get_daily_briefing
]

# in-process SDK MCP Server 생성
calendar_mcp_server = create_sdk_mcp_server(
    name="calendar",
    tools=ALL_SDK_TOOLS
)
