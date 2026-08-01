# 🐛 BUG_FIX: Relative Date Parsing Error (2023 Past Year Hallucination Fix)

---

## 1. Issue Overview
* **Issue Description**: When users requested relative schedule creation (e.g., "Schedule study session for this Saturday 3 PM to 5 PM"), the agent created events with past year dates (`2023-06-03`, `2023-06-04`) instead of the current year (`2026-08-01`).

---

## 2. Root Cause Analysis

### ① LLM Training Cutoff Calendar Bias
* Pre-trained LLM models (Claude) have strong internal training weights for past calendars (e.g. `2023-06-03` as Saturday).
* Providing only a static string like `"Current Time: 2026-07-30"` caused the LLM to hallucinate using pre-trained 2023 date templates when resolving relative phrases like "this Saturday".

### ② Limitations of Pure LLM Calendar Arithmetic
* LLMs cannot guarantee 100% accurate calendar arithmetic (e.g., calculating leap years, month boundaries, weekday offsets) through unassisted reasoning alone.

### ③ Lack of Explicit Relative Date Mapping Tables
* The system prompt previously lacked an explicit `YYYY-MM-DD` weekday lookup table relative to today's date, forcing the LLM to infer dates independently.

---

## 3. Fix & Implementation

Instead of relying on LLM date arithmetic, **Python code calculates exact YYYY-MM-DD dates for this week and next week in real-time, injecting them as an explicit lookup table into the System Prompt**.

### 📄 Code Modifications ([agent/prompt.py](file:///Users/jason/dev/ai/my-personal-calendar-agent/agent/prompt.py))

1. **`get_relative_date_info()` Function**:
   Uses Python `datetime` and `timedelta` to dynamically compute exact dates for Today, Tomorrow, This Week (Mon–Sun), and Next Week (Mon–Sun).

2. **Dynamic System Prompt Structure**:
```text
[CURRENT REFERENCE TIME & DAY MAPPING TABLE]
- Current Time: 2026-07-30 22:37:00 (Thursday)
- Today: 2026-07-30 (Thursday)
- Tomorrow: 2026-07-31

[Accurate YYYY-MM-DD Date Mapping for THIS WEEK]:
  • This week Monday: 2026-07-27
  • This week Tuesday: 2026-07-28
  • This week Wednesday: 2026-07-29
  • This week Thursday: 2026-07-30 <- (Today)
  • This week Friday: 2026-07-31
  • This week Saturday: 2026-08-01
  • This week Sunday: 2026-08-02
```

3. **Strict System Directives**:
```text
- Always reference the [Accurate YYYY-MM-DD Date Mapping] table above when parsing dates.
- Never compute past cutoff years (e.g. 2023) or arbitrary dates.
```

---

## 4. Verification Results

| Relative Expression | Before Fix (Error) | After Fix (Resolved) |
| --- | --- | --- |
| This Saturday | `2023-06-03` | **`2026-08-01` (Saturday)** |
| This Sunday | `2023-06-04` | **`2026-08-02` (Sunday)** |

Unit test (`scratch/test_date_parsing.py`) and all pytest test cases pass cleanly.

---

## 5. Recent Enhancements

### ① Dynamic Multi-Lingual Matching Policy
* Updated System Prompt ([`agent/prompt.py`](file:///Users/jason/dev/ai/my-personal-calendar-agent/agent/prompt.py)) and Skill ([`SKILL.md`](file:///Users/jason/dev/ai/my-personal-calendar-agent/.agents/skills/calendar-smart-scheduler/SKILL.md)) rules to match the user's prompt language while preserving English system terms (`[TOOL CALL]`, `[THOUGHT]`, `mcp__calendar__*`, ▶, ✔, ⏱).

### ② Single-Width Unicode Symbol Formatting
* Replaced 2-cell wide emojis (📅, 📊, 🛠️, 📌) with single-width Unicode symbols (`▶`, `✔`, `⏱`, `■`, `●`, `◆`, `ℹ`, `✖`) to eliminate terminal column misalignment.

### ③ Rich CLI Dynamic Spinner & Log Accumulation UI
* Integrated dynamic loading spinner (`console.status`) with line-by-line persistent debug panel accumulation in `main.py`.

---

## 🔗 Official Documentation References

* **Anthropic Claude Agent SDK**: [Anthropic Engineering Blog - Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
* **Model Context Protocol (MCP)**: [MCP Official Specification & Documentation](https://modelcontextprotocol.io/introduction)
* **Anthropic Claude API & Prompt Engineering**: [Anthropic API Documentation](https://docs.anthropic.com/en/docs/welcome)
* **AWS Bedrock Integration**: [AWS Bedrock User Guide - Anthropic Claude Models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
