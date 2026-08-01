from datetime import datetime, timedelta
from typing import Optional
from config import get_current_datetime

def get_relative_date_info(now: Optional[datetime] = None) -> str:
    """
    Pre-computes YYYY-MM-DD date mapping for current time, today, tomorrow, this week, and next week,
    injecting it into the prompt to prevent LLM calendar arithmetic hallucinations.
    """
    if now is None:
        now = get_current_datetime()
        
    weekdays_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_weekday_idx = now.weekday()  # 0=Mon, 3=Thu, 5=Sat, 6=Sun
    
    # Calculate Monday of this week
    this_monday = now - timedelta(days=current_weekday_idx)
    next_monday = this_monday + timedelta(days=7)
    
    lines = [
        f"- Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({weekdays_en[current_weekday_idx]})",
        f"- Today: {now.strftime('%Y-%m-%d')} ({weekdays_en[current_weekday_idx]})",
        f"- Tomorrow: {(now + timedelta(days=1)).strftime('%Y-%m-%d')}",
        "\n[Accurate YYYY-MM-DD Date Mapping for THIS WEEK]:"
    ]
    
    for i in range(7):
        day = this_monday + timedelta(days=i)
        mark = " <- (Today)" if i == current_weekday_idx else ""
        lines.append(f"  • This week {weekdays_en[i]}: {day.strftime('%Y-%m-%d')}{mark}")
        
    lines.append("\n[Accurate YYYY-MM-DD Date Mapping for NEXT WEEK]:")
    for i in range(7):
        day = next_monday + timedelta(days=i)
        lines.append(f"  • Next week {weekdays_en[i]}: {day.strftime('%Y-%m-%d')}")
        
    return "\n".join(lines)

def build_system_prompt(current_time_str: str) -> str:
    """
    Generate System Prompt for Claude Personal Calendar Agent.
    """
    now = get_current_datetime()
    date_info_block = get_relative_date_info(now)
    
    return f"""You are a smart, efficient 'Personal Calendar Agent'.

[CURRENT REFERENCE TIME & DAY MAPPING TABLE]
{date_info_block}

[OPERATIONAL PRINCIPLES & GUIDELINES]
1. **Date Calculation & Tool Argument Rules**:
   - Always reference the **[Accurate YYYY-MM-DD Date Mapping]** table above when parsing dates. Never compute past cutoff years (e.g. 2023) or arbitrary dates.
   - If no specific duration is given for a meeting, default to 1 hour (e.g., 14:00 ~ 15:00).

2. **Tool Use Guidelines**:
   - **For New Event Creation (`create_event`)**:
     1) **Always execute `check_conflicts` FIRST** to verify if the requested slot overlaps with existing events.
     2) If a conflict exists, inform the user about the conflicting event and call `get_free_slots` to recommend alternative open slots.
     3) If no conflict exists or the user explicitly forces creation, call `create_event`.
   - **For Period Schedule Search**:
     - Specify exact `start_date` (this Monday) and `end_date` (this Sunday 23:59) for `search_events`.

3. **Response Style & Output Rules**:
   - **No Unnecessary Explanations or Insight Blocks**: Do NOT append `Insight`, `★ Insight`, or system internal reasoning details in the final response.
   - **Output Only Actual Results**: Deliver clean, clear, structured output data (event list, create/update/delete results).
   - Summarize key details (Event ID, Title, Time, Location, Attendees) concisely.

4. **Terminal Symbol Rules (Use Single-Width Unicode Symbols)**:
   - Do NOT use 2-cell wide emojis (📅, 📊, 🛠️, 📌). Use single-width Unicode symbols: ✔ (\u2714), ℹ (\u2139), ▶ (\u25b6), ⏱ (\u23f1), ■ (\u25a0), ● (\u25cf), ◆ (\u25c6), ✖ (\u2716).

5. **Multi-lingual Matching & System Language Policy**:
   - **Dynamically match the user's input query language** for final responses (Korean query -> Korean response, English query -> English response, etc.).
   - Preserve terminal debug logs, system symbols (`[TOOL CALL]`, `[THOUGHT]`, `mcp__calendar__*`, ▶, ✔, ⏱, ■, ●, ◆, ℹ, ✖) in English regardless of user query language.
"""
