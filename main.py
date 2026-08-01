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
    debug_status = "[bold green]ON[/bold green]" if debug_mode else "[bold dim]OFF[/bold dim]"
    
    banner_text = (
        f"[bold cyan]\u25b6 AWS Bedrock Claude Agent 기반 개인일정관리 에이전트[/bold cyan]\n\n"
        f"[bold white]\u23f1 현재 시각[/bold white]   : {get_current_time_str()}\n"
        f"[bold white]\u25a0 AWS Region[/bold white]: {AWS_REGION}\n"
        f"[bold white]\u25a0 Model ID[/bold white]  : {BEDROCK_MODEL_ID}\n"
        f"[bold white]\u2139 Debug Mode[/bold white]: {debug_status}\n\n"
        f"[bold yellow]\u25c6 사용 예시:[/bold yellow]\n"
        f"  * '내일 오후 3시에 팀장님과 미팅 등록해줘'\n"
        f"  * '오늘 일정 브리핑해줘'\n"
        f"  * '이번주 금요일 오후에 빈 시간대 탐색해줘'\n\n"
        f"[bold magenta]\u25c6 명령어 리스트:[/bold magenta]\n"
        f"  * [bold green]/debug [on|off][/bold green] : 실시간 에이전트 추론/도구호출 이력 출력 토글\n"
        f"  * [bold green]/list[/bold green]          : DB 등록 전체 일정 스타일 표 조회\n"
        f"  * [bold green]/clear[/bold green]         : 대화 메모리 초기화\n"
        f"  * [bold green]/exit[/bold green]          : 에이전트 종료"
    )
    
    console.print(Panel(banner_text, border_style="cyan", title="[bold white]Welcome[/bold white]", expand=False))
    console.print()

def list_all_events():
    repo = CalendarRepository()
    events = repo.search_events(status=None)
    if not events:
        console.print("[yellow]\u2139 등록된 일정이 없습니다.[/yellow]\n")
        return
        
    table = Table(title="\u25b6 전체 일정 목록", border_style="blue", header_style="bold magenta")
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("제목", style="bold white")
    table.add_column("시작 시간", style="green")
    table.add_column("종료 시간", style="green")
    table.add_column("장소", style="yellow")
    table.add_column("참석자", style="magenta")
    table.add_column("상태", justify="center", style="bold blue")

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
    """기존 디버그 UI(Rich Panel) 100% 보존 + 로딩바 지원 및 블록간 한 줄 띄움 처리"""
    if event_type == "tool_use":
        tool_name = data.get("name", "unknown")
        tool_input = data.get("input", {})
        if status:
            status.update(f"[bold yellow]\u23f1 도구 호출 중 ({tool_name})...[/bold yellow]")
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
            status.update("[bold blue]\u23f1 도구 결과 반영 및 분석 중...[/bold blue]")
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
            status.update("[bold green]\u23f1 추론 및 다음 단계 준비 중...[/bold green]")
        console.print(f"[dim gray]\u25b6 [THOUGHT] {data}[/dim gray]\n")
    elif event_type == "error":
        console.print(f"[bold red]\u2716 [DEBUG ERROR] {data}[/bold red]\n")

def main():
    parser = argparse.ArgumentParser(description="Rich CLI 기반 개인일정관리 에이전트")
    parser.add_argument("--debug", action="store_true", help="실시간 디버그 모드를 활성화하여 시작합니다.")
    args = parser.parse_args()

    # 디버그 모드 기본값을 True로 유지하되 로딩바와 동시 작동되도록 설정
    debug_mode = True if not args.debug else args.debug

    # 1. DB 초기화
    init_db()
    
    # 2. AWS Key 검사
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or AWS_ACCESS_KEY_ID == "your_aws_access_key_id_here":
        console.print(
            Panel(
                "[bold red]\u2716 .env 파일에 AWS_ACCESS_KEY_ID와 AWS_SECRET_ACCESS_KEY를 설정해야 작동합니다.[/bold red]",
                border_style="red"
            )
        )
        
    memory = ConversationMemory()
    try:
        agent = ClaudeCalendarAgent(memory=memory)
    except Exception as e:
        console.print(f"[bold red]\u2716 에이전트 초기화 중 오류 발생: {e}[/bold red]")
        traceback.print_exc()
        agent = None

    print_banner(debug_mode)

    while True:
        try:
            user_input = Prompt.ask("[bold green]\u25b6 [USER][/bold green]").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["/exit", "exit", "quit"]:
                console.print("[bold cyan]\u2716 일정관리 에이전트를 종료합니다. 좋은 하루 되세요![/bold cyan]")
                break
                
            elif user_input.lower() == "/clear":
                memory.clear()
                console.print("[bold yellow]\u2139 에이전트 대화 이력이 초기화되었습니다.[/bold yellow]\n")
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
                    console.print("[bold green]\u2139 디버그 모드가 활성화되었습니다. (모든 툴 호출 및 세부 처리 이력이 출력됩니다)[/bold green]\n")
                elif cmd in ["off", "0", "false"]:
                    debug_mode = False
                    console.print("[bold yellow]\u2139 디버그 모드가 비활성화되었습니다. (간략한 동적 로딩바만 표시됩니다)[/bold yellow]\n")
                else:
                    debug_mode = not debug_mode
                    status_str = "[bold green]ON[/bold green]" if debug_mode else "[bold yellow]OFF[/bold yellow]"
                    console.print(f"\u2139 디버그 모드가 {status_str} 상태로 전환되었습니다.\n")
                continue

            if not agent:
                console.print("[bold red]\u2716 에이전트가 초기화되지 않아 요청을 수행할 수 없습니다.[/bold red]\n")
                continue

            # 에이전트 작업 실행 (기존 Rich Panel 디버그 UI 100% 누적 + 각 작업별 실시간 로딩바 동시 가동)
            with console.status("[bold green]\u23f1 요청을 확인하고 일정을 처리하는 중입니다...[/bold green]", spinner="dots") as status:
                def debug_event_bridge(event_type: str, data: Any):
                    if debug_mode:
                        handle_debug_event(event_type, data, status=status)
                    else:
                        if event_type == "tool_use":
                            name = data.get("name", "unknown")
                            status.update(f"[bold cyan]\u2139 [TOOL CALL] {name}...[/bold cyan]")
                        elif event_type == "thought":
                            status.update("[bold green]\u25b6 [THOUGHT] 추론 중...[/bold green]")
                        elif event_type == "tool_result":
                            status.update("[bold blue]\u2714 [RESULT] 도구 결과 반영 중...[/bold blue]")

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
            console.print("\n[bold cyan]\u2716 일정관리 에이전트를 종료합니다. 좋은 하루 되세요![/bold cyan]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]\u2716 오류 발생: {e}[/bold red]\n")
            traceback.print_exc()

if __name__ == "__main__":
    main()
