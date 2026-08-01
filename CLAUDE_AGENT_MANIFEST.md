# 🤖 Anthropic 공식 가이드 기반 Claude Agent SDK 개발 마니페스트 (CLAUDE_AGENT_MANIFEST.md)

본 마니페스트는 **Anthropic 공식 블로그 ("Building Agents with the Claude Agent SDK")**에 명시된 핵심 아키텍처 원칙, Agent Harness 구축 방법, In-process MCP 툴 연동, 컨텍스트 엔지니어링 및 권한 관리 모범 사례를 종합하여 정립한 **표준 개발 마니페스트 지침서**입니다.

---

## 🌟 1. Claude Agent SDK의 6대 핵심 기둥 (6 Core Pillars)

### ① Agent Harness & Local Loop Execution

* **개념**: SDK는 에이전트 개발 시 가장 복잡한 영역인 **Agent Loop (사고 $\rightarrow→$ 행동 $\rightarrow→$ 관찰 $\rightarrow→$ 반복)**와 인프라 Harness를 내장하여 사용자의 로컬/서버 프로세스 내부에서 자율 구동시킵니다.
* **적용**: 개발자가 수동으로 툴 호출 및 메시지 루프를 작성하지 않고 SDK의 `query()` 또는 `ClaudeSDKClient` 엔진에 위임합니다.

### ② In-Process MCP (Model Context Protocol) 툴 연동

* **개념**: 외부 MCP 서버 프로세스 관리 부담을 없애기 위해 `@tool` 데코레이터와 `create_sdk_mcp_server`를 통해 프로세스 내(In-process)에 MCP 인프라를 바인딩합니다.
* **표준 규격**:
  - `Pydantic` `BaseModel`을 통한 타입 안전한 Input Schema 자동 생성
  - Anthropic MCP 표준 반환 구조인 `{"content": [{"type": "text", "text": "..."}]}` 적용

### ③ 양방향 대화 세션 관리 (`ClaudeSDKClient` vs `query`)

* **단발성 작업 (`query()`)**: "특정 파일의 버그를 수정해줘" 같은 단일 태스크 처리 시 사용.
* **지속적 세션 (`ClaudeSDKClient`)**: 사용자와 에이전트 간 연속적인 멀티턴 대화, 상태 유지, 양방향 상호작용이 필요한 에이전트 개발 시 **`ClaudeSDKClient`** 사용 필수.

### ④ 컨텍스트 엔지니어링, 스킬 시스템 & 다국어 매니페스트 (Context Compaction, `SKILL.md` & Multi-lingual Policy)

* **컨텍스트 절약 규칙**: 에이전트에게 필요한 모든 방대한 지침을 System Prompt에 집어넣어 Context Window를 오염시키지 않습니다.
* **`SKILL.md` 플레이북 구조**: 특정 전문 업무(예: 일정 충돌 해결 플레이북)는 모듈화된 `SKILL.md` 파일로 분리하고, 에이전트가 해당 작업이 필요할 때만 런타임에 로드하도록 설계합니다.
* **다국어 응답 및 시스템 언어 보존 매니페스트 (Multi-lingual Matching & System Language Policy)**:
  - 사용자가 질의하는 언어에 맞춰 최종 답변 언어를 동적으로 선택합니다. (한국어 질문 $\rightarrow$ 한국어 응답, 영어 질문 $\rightarrow$ 영어 응답)
  - 단, `[TOOL CALL]`, `[THOUGHT]`, `mcp__calendar__*`, ▶, ✔, ⏱, ■, ●, ◆, ℹ, ✖ 등 터미널 디버그 로그, 시스템 특수문자 및 MCP 도구 명칭의 영문 표현은 사용자 언어와 상관없이 기존 영문 및 기호를 100% 보존합니다.

### ⑤ 최소 권한 제어, Pre-Tool-Hook & 안전성 (`allowed_tools`, `pre_tool_hook`)

* **`allowed_tools`**: 에이전트가 오직 허용된 툴만 호출할 수 있도록 `ClaudeAgentOptions` 상에 와일드카드 및 명시적 인자 스코프를 지정합니다 (`allowed_tools=["mcp__<server_name>__*"]`).
* **Pre-Tool-Hook**: 도구 실행 직전 검증, 승인(Human-in-the-loop), 권한 제어 및 보안 감사를 처리하는 사전 콜백 후크를 바인딩합니다. 자세한 설명은 [CLAUDE_AGENT_SDK_DETAILS.md](file:///Users/jason/dev/ai/my-personal-calendar-agent/CLAUDE_AGENT_SDK_DETAILS.md)를 참조하세요.

### ⑥ 멀티 클라우드 Provider 지원 (Bedrock & Vertex AI)

* **AWS Bedrock**: `CLAUDE_CODE_USE_BEDROCK=1` 및 AWS IAM 자격 증명 환경 변수 설정.
* **GCP Vertex AI**: `CLAUDE_CODE_USE_VERTEX=1` 및 Vertex AI 환경 변수 설정.
* **API Error 400 방지**: 툴 루프 시 Extended Thinking 블록 불일치를 차단하기 위해 `thinking={"type": "disabled"}` 지정.

---

## 🏗️ 2. 표준 에이전트 프로젝트 디렉토리 구조 (Boilerplate)

```text
my-agent-project/
├── pyproject.toml                # uv 기반 프로젝트 & claude-agent-sdk (requires-python >= 3.10)
├── README.md                     # 프로젝트 설명 및 전체 인덱스 문서
├── CLAUDE_AGENT_SDK_DETAILS.md   # Claude Agent SDK 상세 & Pre-tool-hook 지침서
├── CLAUDE_AGENT_MANIFEST.md      # 에이전트 개발 마니페스트
├── config.py                     # 환경 변수 및 Provider 설정 (인라인 주석 정제 포함)
├── main.py                       # prompt_toolkit 기반 대화형 CLI
├── storage/                      # 데이터베이스 및 외부 서비스 계층
├── tools/                        # Pydantic + @tool + create_sdk_mcp_server 도구 모음
├── agent/
│   ├── core.py                   # ClaudeSDKClient / query 에이전트 엔진 (skills 옵션 적용)
│   ├── prompt.py                 # 동적 런타임 팩트/매핑표/다국어 정책 주입 모듈
│   └── memory.py                 # 대화 이력 및 세션 상태 관리
├── .agents/
│   └── skills/                   # 프로젝트 전용 커스텀 스킬 (calendar-smart-scheduler)
└── tests/                        # pytest 유닛 및 통합 테스트
```

---

## 🚀 3. 다른 프로젝트 적용 시 개발 체크리스트 (Developer Checklist)

1. [ ] **Python 버전 설정**: `pyproject.toml`에 `requires-python = ">=3.10"` 지정 (`claude-agent-sdk` 최소 요건).
2. [ ] **도구 정의**: `tools/`에 Pydantic Schema + `@tool` 구현 후 `create_sdk_mcp_server`로 In-process MCP 바인딩.
3. [ ] **Pre-Tool-Hook 등록**: 파괴적 작업 승인이나 인자 검증이 필요할 경우 `pre_tool_hook` 콜백 함수 구현 및 옵션 바인딩.
4. [ ] **환각 방지**: 상대적 날짜나 셈이 필요한 팩트는 LLM에게 추론시키지 말고 코드 팩트(매핑 테이블 등)를 `agent/prompt.py`에서 주입.
5. [ ] **다국어 응답 매니페스트**: 사용자 입력 언어에 맞춘 답변 및 시스템/로그 영문 보존 지침을 System Prompt에 기술.
6. [ ] **옵션 설정**: `ClaudeAgentOptions`에 `mcp_servers`, `allowed_tools`, `skills`, `setting_sources`, `thinking={"type": "disabled"}` 설정.
7. [ ] **세션 선택**: 대화형 에이전트는 `ClaudeSDKClient`, 단발성 처리는 `query()` 채택.
8. [ ] **터미널 UX**: 컬럼 폭 왜곡 방지를 위한 단일 폭 유니코드 기호 적용 및 동적 스피너 렌더링.

---

## 📚 관련 문서 & 공식 문서 References

### 프로젝트 로컬 문서
* [Claude Agent SDK 상세 지침 및 Pre-Tool-Hook 가이드 (CLAUDE_AGENT_SDK_DETAILS.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/CLAUDE_AGENT_SDK_DETAILS.md)
* [버그 조치 및 원인 분석 문서 (BUG_FIX.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/BUG_FIX.md)
* [프로젝트 메인 안내서 (README.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/README.md)

### 공식 기술 문서 (Official Documentation References)
* **Anthropic Claude Agent SDK**: [Anthropic Engineering Blog - Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
* **Model Context Protocol (MCP)**: [MCP Official Specification & Documentation](https://modelcontextprotocol.io/introduction)
* **Anthropic Claude API**: [Anthropic API Documentation & Prompt Engineering Guide](https://docs.anthropic.com/en/docs/welcome)
* **AWS Bedrock Integration**: [AWS Bedrock User Guide - Anthropic Claude Models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
* **Pydantic Schema Validation**: [Pydantic Official Documentation](https://docs.pydantic.dev/latest/)
* **Rich Terminal UI**: [Rich Official Documentation](https://rich.readthedocs.io/en/latest/)
