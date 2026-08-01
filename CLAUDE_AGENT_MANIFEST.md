# 🤖 Claude Agent SDK Development Manifesto (CLAUDE_AGENT_MANIFEST.md)

This manifesto establishes a **standard agent development guidelines manifesto** based on Anthropic's official engineering principles ("Building Agents with the Claude Agent SDK"), defining Agent Harness architecture, In-process MCP tool binding, context compaction, and permission management best practices.

---

## 🌟 1. Six Core Pillars of Claude Agent SDK

### ① Agent Harness & Local Loop Execution

* **Concept**: The SDK encapsulates the most complex agent engineering layer — the **Agent Loop (Thought $\rightarrow$ Action $\rightarrow$ Observation $\rightarrow$ Repeat)** and infrastructure Harness — running directly inside local or server Python processes.
* **Implementation**: Delegates messaging loops and tool execution orchestration to SDK engines (`query()` or `ClaudeSDKClient`) without writing manual tool routing loops.

### ② In-Process MCP (Model Context Protocol) Tool Binding

* **Concept**: Eliminates external MCP process management overhead by binding MCP tool infrastructure directly inside the Python process using the `@tool` decorator and `create_sdk_mcp_server`.
* **Standard Specification**:
  - Type-safe Input Schema generation using `Pydantic` `BaseModel`.
  - Standard Anthropic MCP return format: `{"content": [{"type": "text", "text": "..."}]}`.

### ③ Interactive Session Management (`ClaudeSDKClient` vs `query`)

* **One-shot Tasks (`query()`)**: Use for single-turn task execution (e.g. "Fix a bug in file X").
* **Persistent Sessions (`ClaudeSDKClient`)**: Mandatory for interactive multi-turn conversations, state persistence, and bidirectional user-agent interactions.

### ④ Context Engineering, Skill System & Multi-Lingual Policy

* **Context Efficiency**: Prevents context window pollution by avoiding bloated instructions inside the System Prompt.
* **`SKILL.md` Playbooks**: Encapsulates domain-specific workflows (e.g. schedule conflict resolution playbooks) into modular `SKILL.md` skill files loaded dynamically at runtime.
* **Multi-Lingual Response & System Symbol Policy**:
  - Dynamically matches the user's query language for final output messages (Korean prompt $\rightarrow$ Korean response, English prompt $\rightarrow$ English response).
  - Preserves terminal debug logs, system symbols (`[TOOL CALL]`, `[THOUGHT]`, `mcp__calendar__*`, ▶, ✔, ⏱, ■, ●, ◆, ℹ, ✖) in English regardless of user query language.

### ⑤ Least Privilege Control, Pre-Tool-Hook & Security (`allowed_tools`, `pre_tool_hook`)

* **`allowed_tools`**: Restricts agent tool calls by declaring wildcard or explicit tool scopes (`allowed_tools=["mcp__<server_name>__*"]`) in `ClaudeAgentOptions`.
* **Pre-Tool-Hook**: Binds pre-execution callback hooks for human-in-the-loop approvals, parameter validations, RBAC, and audit logging. See [CLAUDE_AGENT_SDK_DETAILS.md](file:///Users/jason/dev/ai/my-personal-calendar-agent/CLAUDE_AGENT_SDK_DETAILS.md).

### ⑥ Multi-Cloud Provider Support (AWS Bedrock & GCP Vertex AI)

* **AWS Bedrock**: Set `CLAUDE_CODE_USE_BEDROCK=1` and AWS IAM credential environment variables.
* **GCP Vertex AI**: Set `CLAUDE_CODE_USE_VERTEX=1` and Vertex AI environment variables.
* **API Error 400 Prevention**: Specify `thinking={"type": "disabled"}` to prevent extended thinking block mismatches in multi-turn tool loops.

---

## 🏗️ 2. Standard Agent Project Boilerplate Structure

```text
my-agent-project/
├── pyproject.toml                # uv project & claude-agent-sdk config (requires-python >= 3.10)
├── README.md                     # Main project documentation & index
├── CLAUDE_AGENT_SDK_DETAILS.md   # Claude Agent SDK details & Pre-tool-hook guide
├── CLAUDE_AGENT_MANIFEST.md      # Agent development manifesto
├── config.py                     # Environment variables & Provider configuration
├── main.py                       # Rich CLI entrypoint with Claude Code style banner
├── storage/                      # Database & data persistence layer
├── tools/                        # Pydantic + @tool + create_sdk_mcp_server tools
├── agent/
│   ├── core.py                   # ClaudeSDKClient / query agent engine (skills enabled)
│   ├── prompt.py                 # Dynamic date mapping & multi-lingual prompt module
│   └── memory.py                 # Conversation history memory manager
├── .agents/
│   └── skills/                   # Project custom skills (calendar-smart-scheduler)
└── tests/                        # pytest unit & integration test suite
```

---

## 🚀 3. Developer Checklist for New Projects

1. [ ] **Python Version**: Set `requires-python = ">=3.10"` in `pyproject.toml` (minimum requirement for `claude-agent-sdk`).
2. [ ] **Tool Registration**: Define Pydantic Schema + `@tool` functions in `tools/`, then bind via `create_sdk_mcp_server`.
3. [ ] **Pre-Tool-Hook**: Register `pre_tool_hook` callback in options if destructive actions require human confirmation.
4. [ ] **Prevent Hallucinations**: Inject dynamic date fact tables in `agent/prompt.py` instead of relying on LLM date arithmetic.
5. [ ] **Multi-Lingual Policy**: Include multi-lingual language matching directives in System Prompt while preserving English system terms.
6. [ ] **Options Configuration**: Set `mcp_servers`, `allowed_tools`, `skills`, `setting_sources`, and `thinking={"type": "disabled"}` on `ClaudeAgentOptions`.
7. [ ] **Session Selection**: Use `ClaudeSDKClient` for interactive applications and `query()` for single-turn tasks.
8. [ ] **Terminal UX**: Apply single-width Unicode symbols and Rich dynamic spinner UI to eliminate column alignment distortion.

---

## 📚 Related & Official Documentation References

### Local Documentation
* [Claude Agent SDK Details & Pre-Tool-Hook Guide (CLAUDE_AGENT_SDK_DETAILS.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/CLAUDE_AGENT_SDK_DETAILS.md)
* [Bug Fix & Root Cause Analysis Report (BUG_FIX.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/BUG_FIX.md)
* [Main Project Guide (README.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/README.md)

### Official Documentation References
* **Anthropic Claude Agent SDK**: [Anthropic Engineering Blog - Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
* **Model Context Protocol (MCP)**: [MCP Official Specification & Documentation](https://modelcontextprotocol.io/introduction)
* **Anthropic Claude API**: [Anthropic API Documentation & Prompt Engineering Guide](https://docs.anthropic.com/en/docs/welcome)
* **AWS Bedrock Integration**: [AWS Bedrock User Guide - Anthropic Claude Models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
* **Pydantic Schema Validation**: [Pydantic Official Documentation](https://docs.pydantic.dev/latest/)
* **Rich Terminal UI**: [Rich Official Documentation](https://rich.readthedocs.io/en/latest/)
