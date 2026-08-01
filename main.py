import sys
import os
import argparse
import traceback
import re
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt

from storage.db import init_db
from storage.calendar_repository import CalendarRepository
from agent.core import ClaudeCalendarAgent
from agent.memory import ConversationMemory
from config import get_current_time_str, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BEDROCK_MODEL_ID, AWS_REGION

console = Console()

def print_banner(debug_mode: bool):
    """
    CLI 아웃트로/배너 출력 (Big ASCII Art Header & English UI)
    """
    debug_status = "[bold green]ON[/bold green]" if debug_mode else "[bold dim]OFF[/bold dim]"
    cwd = os.getcwd()
    
    unicode_banner = (
        "[bold cyan]  ██████╗ █████╗ ██╗     ███████╗███╗   ██╗██████╗  █████╗ ██████╗ [/bold cyan]\n"
        "[bold cyan] ██╔════╝██╔══██╗██║     ██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔══██╗[/bold cyan]\n"
        "[bold cyan] ██║     ███████║██║     █████╗  ██╔██╗ ██║██║  ██║███████║██████╔╝[/bold cyan]\n"
        "[bold cyan] ██║     ██╔══██║██║     ██╔══╝  ██║╚██╗██║██║  ██║██╔══██║██╔══██╗[/bold cyan]\n"
        "[bold cyan] ╚██████╗██║  ██║███████╗███████╗██║ ╚████║██████╔╝██║  ██║██║  ██║[/bold cyan]\n"
        "[bold cyan]  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝[/bold cyan]\n"
        "[bold bright_magenta]    █████╗  ██████╗ ███████╗███╗   ██╗████████╗                   [/bold bright_magenta]\n"
        "[bold bright_magenta]   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝                   [/bold bright_magenta]\n"
        "[bold bright_magenta]   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║                      [/bold bright_magenta]\n"
        "[bold bright_magenta]   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║                      [/bold bright_magenta]\n"
        "[bold bright_magenta]   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║                      [/bold bright_magenta]\n"
        "[bold bright_magenta]   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝                      [/bold bright_magenta]"
    )
    
    banner_text = (
        f"\n{unicode_banner}\n\n"
        f"  [dim](powered by Claude Agent SDK)[/dim]\n\n"
        f"  [bold white]Model:[/bold white]     [cyan]{BEDROCK_MODEL_ID}[/cyan]\n"
        f"  [bold white]Region:[/bold white]    [cyan]{AWS_REGION}[/cyan]\n"
        f"  [bold white]Time:[/bold white]      [cyan]{get_current_time_str()}[/cyan]\n"
        f"  [bold white]Workspace:[/bold white] [dim]{cwd}[/dim]\n"
        f"  [bold white]Debug:[/bold white]     {debug_status}\n\n"
        f"[bold bright_yellow]Examples:[/bold bright_yellow]\n"
        f"  [dim]•[/dim] 'Add a team sync meeting tomorrow at 3 PM'\n"
        f"  [dim]•[/dim] 'Show my schedule for this week'\n"
        f"  [dim]•[/dim] 'Find available free slots on Friday afternoon'\n\n"
        f"[bold bright_magenta]Commands:[/bold bright_magenta]\n"
        f"  [bold green]/debug [on|off][/bold green] : Toggle real-time agent reasoning & tool execution stream\n"
        f"  [bold green]/list[/bold green]          : View all scheduled events in database table\n"
        f"  [bold green]/clear[/bold green]         : Clear conversation memory history\n"
        f"  [bold green]/exit[/bold green]          : Exit the agent session\n"
    )
    
    console.print(Panel(banner_text, border_style="cyan", title="[bold white]Personal Schedule Agent[/bold white]", expand=False))
    console.print()

def list_all_events():
    repo = CalendarRepository()
    events = repo.search_events(status=None)
    if not events:
        console.print("[yellow]\u2139 No events registered in database.[/yellow]\n")
        return
        
    table = Table(title="\u25b6 All Scheduled Events", border_style="blue", header_style="bold magenta")
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold white")
    table.add_column("Start Time", style="green")
    table.add_column("End Time", style="green")
    table.add_column("Location", style="yellow")
    table.add_column("Attendees", style="magenta")
    table.add_column("Status", justify="center", style="bold blue")

    for ev in events:
        table.add_row(
            str(ev["id"]),
            ev["title"],
            ev["start_time"],
            ev["end_time"],
            ev["location"] or "-",
            ev["attendees"] or "-",
            ev["status"]
        )
        
    console.print(table)
    console.print()

def clean_agent_response(response: str) -> str:
    """
    최종 응답에서 ★ Insight, Insight 등의 사족/부가분석 블록을 제거하고 실제 결과만 추출합니다.
    """
    pattern = r"`★ Insight [─\-]+`[\s\S]*?`[─\-]+`"
    cleaned = re.sub(pattern, "", response)
    
    cleaned = re.sub(r"★ Insight[^\n]*\n", "", cleaned)
    cleaned = re.sub(r"^\s*•.*(분석|확인|작성했습니다).*\n?", "", cleaned, flags=re.MULTILINE)
    
    return cleaned.strip()

def handle_debug_event(event_type: str, data: Any, status: Optional[Any] = None):
    """기존 디버그 UI(Rich Panel) 100% 보존 + 로딩바 지원 및 영문 라벨 적용"""
    if event_type == "tool_use":
        tool_name = data.get("name", "unknown")
        tool_input = data.get("input", {})
        if status:
            status.update(f"[bold yellow]\u23f1 Executing tool call ({tool_name})...[/bold yellow]")
        console.print(
            Panel(
                f"[bold cyan]Tool Name:[/bold cyan] [white]{tool_name}[/white]\n"
                f"[bold cyan]Tool Input:[/bold cyan] [dim green]{tool_input}[/dim green]",
                title="[bold yellow]\u2139 [DEBUG] Tool Call Request[/bold yellow]",
                border_style="yellow",
                expand=False
            )
        )
        console.print()
    elif event_type == "tool_result":
        if status:
            status.update("[bold blue]\u23f1 Analyzing tool execution results...[/bold blue]")
        console.print(
            Panel(
                f"[bold green]Output:[/bold green] {data}",
                title="[bold blue]\u2139 [DEBUG] Tool Execution Result[/bold blue]",
                border_style="blue",
                expand=False
            )
        )
        console.print()
    elif event_type == "thought":
        if status:
            status.update("[bold green]\u23f1 Reasoning next steps...[/bold green]")
        console.print(f"[dim gray]\u25b6 [THOUGHT] {data}[/dim gray]\n")
    elif event_type == "error":
        console.print(f"[bold red]\u2716 [DEBUG ERROR] {data}[/bold red]\n")

def main():
    parser = argparse.ArgumentParser(description="Interactive Personal Calendar Agent CLI")
    parser.add_argument("--debug", action="store_true", help="Enable real-time debug stream mode.")
    args = parser.parse_args()

    # 디버그 모드 기본값을 True로 유지하되 로딩바와 동시 작동
    debug_mode = True if not args.debug else args.debug

    # 1. DB 초기화
    init_db()
    
    # 2. AWS Key 검사
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or AWS_ACCESS_KEY_ID == "your_aws_access_key_id_here":
        console.print(
            Panel(
                "[bold red]\u2716 Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file.[/bold red]",
                border_style="red"
            )
        )
        
    memory = ConversationMemory()
    try:
        agent = ClaudeCalendarAgent(memory=memory)
    except Exception as e:
        console.print(f"[bold red]\u2716 Error initializing agent: {e}[/bold red]")
        traceback.print_exc()
        agent = None

    print_banner(debug_mode)

    while True:
        try:
            user_input = Prompt.ask("[bold green]\u25b6 [USER][/bold green]").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["/exit", "exit", "quit"]:
                console.print("[bold cyan]\u2716 Exiting Personal Calendar Agent session. Have a great day![/bold cyan]")
                break
                
            elif user_input.lower() == "/clear":
                memory.clear()
                console.print("[bold yellow]\u2139 Conversation history cleared.[/bold yellow]\n")
                continue
                
            elif user_input.lower() == "/list":
                list_all_events()
                continue
                
            elif user_input.lower() == "/help":
                print_banner(debug_mode)
                continue
                
            elif user_input.lower().startswith("/debug"):
                parts = user_input.split()
                if len(parts) == 1:
                    cmd = "toggle"
                else:
                    cmd = parts[1].lower()
                    
                if cmd in ["on", "1", "true"]:
                    debug_mode = True
                    console.print("[bold green]\u2139 Debug mode enabled. (Real-time tool calls & reasoning stream will be displayed)[/bold green]\n")
                elif cmd in ["off", "0", "false"]:
                    debug_mode = False
                    console.print("[bold yellow]\u2139 Debug mode disabled. (Summary spinner status will be displayed)[/bold yellow]\n")
                else:
                    debug_mode = not debug_mode
                    status_str = "[bold green]ON[/bold green]" if debug_mode else "[bold yellow]OFF[/bold yellow]"
                    console.print(f"\u2139 Debug mode toggled to {status_str}.\n")
                continue

            if not agent:
                console.print("[bold red]\u2716 Agent not initialized. Cannot process request.[/bold red]\n")
                continue

            # 에이전트 작업 실행 (Claude Code 스타일 로딩바 & 누적 디버그 패널)
            with console.status("[bold green]\u23f1 Processing schedule request...[/bold green]", spinner="dots") as status:
                def debug_event_bridge(event_type: str, data: Any):
                    if debug_mode:
                        handle_debug_event(event_type, data, status=status)
                    else:
                        if event_type == "tool_use":
                            name = data.get("name", "unknown")
                            status.update(f"[bold cyan]\u2139 [TOOL CALL] {name}...[/bold cyan]")
                        elif event_type == "thought":
                            status.update("[bold green]\u25b6 [THOUGHT] Reasoning...[/bold green]")
                        elif event_type == "tool_result":
                            status.update("[bold blue]\u2714 [RESULT] Tool result reflected...[/bold blue]")

                raw_response = agent.run(user_input, verbose=True, debug=True, on_event=debug_event_bridge)
            console.print()

            # Insight 등 불필요 사족 필터링
            final_response = clean_agent_response(raw_response)

            # 에이전트 최종 응답 출력
            console.print(
                Panel(
                    Markdown(final_response),
                    title="[bold cyan]\u2714 [AGENT] Response[/bold cyan]",
                    border_style="cyan",
                    expand=False
                )
            )
            console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold cyan]\u2716 Exiting Personal Calendar Agent session. Have a great day![/bold cyan]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]\u2716 Error occurred: {e}[/bold red]\n")
            traceback.print_exc()

if __name__ == "__main__":
    main()
