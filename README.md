# 개인일정관리 에이전트

Anthropic의 공식 파이썬 패키지인 **`claude-agent-sdk` (v0.2.128)**와 In-process **Model Context Protocol (MCP)** 기술, 그리고 **AWS Bedrock** 환경을 결합하여 구축한 지능형 개인 일정 관리 AI 에이전트입니다.

---

## 🌟 주요 특징 및 아키텍처

### 1. 공식 `claude-agent-sdk` & In-Process MCP 아키텍처
* **`@tool` 데코레이터 & Pydantic 스키마 (`tools/`)**: `claude_agent_sdk.tool` 데코레이터와 Pydantic `BaseModel`을 적용하여 툴 입력/출력 인자의 타입 안전성과 자동 JSON Schema 생성을 처리합니다.
* **In-Process MCP Server (`create_sdk_mcp_server`)**: 별도의 외부 MCP 프로세스 없이 파이썬 프로세스 내에서 다이렉트로 연동되는 SDK 전용 MCP Server를 구축하였습니다 (`mcp_servers={"calendar": calendar_mcp_server}`).
* **`ClaudeAgentOptions` & `query` Engine (`agent/core.py`)**: 비동기 에이전트 추론 루프, 자동 툴 호출(Tool Execution), 관찰(Observation) 수집 및 스트리밍 응답 파싱.

### 2. AWS Bedrock 환경 완전 연동 (`CLAUDE_CODE_USE_BEDROCK=1`)
* `CLAUDE_CODE_USE_BEDROCK=1` 및 AWS IAM 자격 증명 환경 변수를 주입하여 Direct Anthropic API뿐만 아니라 **AWS Bedrock 엔드포인트** 상에서 에이전트를 온전히 온보딩하고 실행합니다.
* `thinking={"type": "disabled"}` 옵션을 적용하여 멀티턴 툴 호출 시 Extended Thinking 블록 불일치로 인한 API Error 400을 원천 방지하였습니다.

### 3. 동적 날짜 매핑 주입 (LLM 환각 차단)
* Python `datetime` 연산으로 생성된 **실시간 [이번 주/다음 주 요일별 YYYY-MM-DD 매핑 테이블]**을 System Prompt에 동적 주입하여 "이번주 토요일", "다음주 수요일" 등 상대적 시각 표현 지시 시 과거 날짜로 오등록되는 환각을 100% 방지합니다 ([BUG_FIX.md](file:///Users/jason/dev/ai/my-personal-calendar-agent/BUG_FIX.md) 참조).

### 4. 동적 다국어 응답 매니페스트 (Multi-lingual Policy)
* **언어 매칭 (Language Matching)**: 사용자가 한국어로 질문하면 한국어로, 영어(English)로 질문하면 영어로 에이전트 답변이 동적 생성됩니다.
* **시스템/로그 영문 보존**: `[TOOL CALL]`, `[THOUGHT]`, `mcp__calendar__*`, ▶, ✔, ⏱, ■, ●, ◆, ℹ, ✖ 등 터미널 디버그 로그 및 특수 기호는 사용자 언어와 무관하게 기존 영문/기호 규격을 100% 보존합니다.

### 5. Rich 기반 CLI UI, 단일 폭 유니코드 심볼 & 동적 스피너
* **유니코드 특수문자 표기**: 2셀 가변 폭 이모지 대신 단일 폭 유니코드 기호(`▶`, `✔`, `⏱`, `■`, `●`, `◆`, `ℹ`, `✖`)를 도입하여 터미널 컬럼 폭 비틀림을 완전 방지했습니다.
* **동적 스피너 & 단계별 로그 누적**: 하단에서 실시간 스피너(`⏱`)가 회전함과 동시에 각 디버그 작업(Tool Call 패널, Output 패널, Thought)의 수행 이력이 한 줄 띄움 간격으로 화면에 깔끔하게 누적 기록됩니다.

### 6. 프로젝트 전용 커스텀 스킬 (`calendar-smart-scheduler`)
* `ClaudeAgentOptions(skills=["calendar-smart-scheduler"], setting_sources=["user", "project"])`를 수동 바인딩하여 일정 등록 전 사전 충돌 검사(`check_conflicts`), 대체 시간대 추천(`get_free_slots`), 표준 요약 출력을 자동 수행합니다.

### 7. 유저 레벨 동적 MCP 확장 (`mcp.json` & `tools/mcp_loader.py`)
* **선언적 MCP 구성**: 프로젝트 루트의 [`mcp.json`](file:///Users/jason/dev/ai/my-personal-calendar-agent/mcp.json) 파일에 유저가 커스텀 MCP 서버(예: filesystem, slack 등) 및 `allowed_tools` 규격을 정의하면, 런타임 시 내장 `calendar` MCP 서버와 안전하게 자동 병합되어 적용됩니다.

---

## 🏗 프로젝트 구조

```text
my-personal-calendar-agent/
├── pyproject.toml                # uv 프로젝트 & claude-agent-sdk 의존성 설정
├── mcp.json                      # 유저 레벨 동적 MCP 서버 & allowed_tools 설정 파일
├── README.md                     # 프로젝트 설명서 & 전체 인덱스
├── CLAUDE_AGENT_SDK_DETAILS.md   # Claude Agent SDK 상세 & Pre-tool-hook 지침서
├── CLAUDE_AGENT_MANIFEST.md      # Anthropic 공식 기준 에이전트 개발 마니페스트
├── BUG_FIX.md                    # 버그 조치 및 원인 분석 문서
├── requirements.txt              # pip 호환 의존성 목록
├── .env.example                  # AWS Bedrock 키 설정 서식
├── config.py                     # AWS & DB 환경설정 모듈 (인라인 주석 정제 로직 포함)
├── main.py                       # prompt_toolkit 기반 대화형 CLI 엔트리포인트
├── storage/
│   ├── db.py                     # SQLite 데이터베이스 스키마 정의
│   └── calendar_repository.py    # 일정 데이터 CRUD 처리 계층
├── tools/
│   ├── __init__.py               # create_sdk_mcp_server 기반 MCP Server 구축
│   ├── mcp_loader.py             # mcp.json 로드 및 내장 MCP 서버 병합 모듈
│   ├── calendar_tools.py         # @tool 기반 일정 검색, 등록, 수정, 삭제, 충돌 검사 툴
│   └── analytics_tools.py        # @tool 기반 빈 시간대 추천, 일정 브리핑 툴
├── agent/
│   ├── core.py                   # 공식 claude_agent_sdk (query, options) 엔진
│   ├── prompt.py                 # 동적 날짜 매핑 주입 System Prompt 모듈
│   └── memory.py                 # 대화 이력 메모리 관리
└── tests/
    ├── test_db.py                # DB 테스트
    ├── test_mcp_loader.py        # mcp.json 로더 테스트
    └── test_tools.py             # Tools 테스트
```

---

## 🚀 빠른 시작 가이드 (`uv`)

### 1. 프로젝트 환경 구축 및 동기화
`uv` 패키지 관리자를 사용하여 가상환경과 의존성을 동기화합니다:
```bash
uv sync
```

### 2. AWS Bedrock 환경 변수 설정
`.env.example`을 복사하여 `.env` 파일을 생성하고 AWS Bedrock IAM 자격 증명을 입력합니다:
```bash
cp .env.example .env
```
`.env` 파일 편집 예시:
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

### 3. 테스트 케이스 실행
```bash
uv run pytest
```

### 4. 개인일정관리 에이전트 실행
```bash
uv run main.py
```

---

## 💬 대화 및 사용 예시

```text
👤 사용자 > 내일 오전 10:30부터 30분간 개발 리뷰 콜 일정 등록해줘.

⏳ 요청을 확인하고 일정을 처리하는 중입니다. 잠시만 기다려주세요...

🤖 Agent >
내일(2026-07-31) 오전 10:30부터 30분간 '개발 리뷰 콜' 일정을 성공적으로 등록했습니다!
- 일정 ID: 6
- 제목: 서버사이드 태깅 콜
- 시간: 2026-07-31 10:30 ~ 11:00
- 장소: 온라인
- 설명: 온라인 콜 예정
```

---

## 📖 전체 문서 인덱스 (Documentation Index)

* 📘 **[Claude Agent SDK 상세 지침 및 Pre-Tool-Hook 가이드 (CLAUDE_AGENT_SDK_DETAILS.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/CLAUDE_AGENT_SDK_DETAILS.md)**
  * **에이전트 4대 핵심 구성 요소**: 메모리(Memory), 스킬(Skills/`SKILL.md`), 서브에이전트(Subagents Delegation), MCP(Model Context Protocol: In-Process vs Remote) 개념 및 파이썬 구현 예시
  * **Pre-Tool-Hook 동작 원리**: Sequence Diagram, Human-in-the-Loop 승인, 파라미터 검증, RBAC, 감사 로깅 유스케이스 및 코드 예시
  * **SDK 런타임 제어**: In-Process MCP, 세션 제어(`ClaudeSDKClient`), 최소 권한 설정(`allowed_tools`), 멀티 클라우드 Provider 지원
* 📙 **[Claude Agent 개발 마니페스트 (CLAUDE_AGENT_MANIFEST.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/CLAUDE_AGENT_MANIFEST.md)**
  * Anthropic 공식 파이썬 패키지 개발 6대 핵심 기둥 및 표준 디렉토리 보일러플레이트, 개발 체크리스트
* 📗 **[버그 조치 및 원인 분석 보고서 (BUG_FIX.md)](file:///Users/jason/dev/ai/my-personal-calendar-agent/BUG_FIX.md)**
  * 상대적 날짜 지시("이번주 토요일") 환각 원인 분석 및 실시간 요일 매핑 테이블 주입을 통한 100% 방지 조치 보고서

---

## 🔗 공식 문서 References (Official Documentation References)

* **Anthropic Claude Agent SDK**: [Anthropic Engineering Blog - Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
* **Model Context Protocol (MCP)**: [MCP Official Specification & Documentation](https://modelcontextprotocol.io/introduction)
* **Anthropic Claude API & Models**: [Anthropic API Documentation & Prompt Engineering Guide](https://docs.anthropic.com/en/docs/welcome)
* **AWS Bedrock Integration**: [AWS Bedrock User Guide - Anthropic Claude Models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
* **Pydantic Schema Validation**: [Pydantic Official Documentation](https://docs.pydantic.dev/latest/)
* **Rich Terminal UI**: [Rich Official Documentation](https://rich.readthedocs.io/en/latest/)


