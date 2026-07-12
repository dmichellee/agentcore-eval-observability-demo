# Vroom&Dash - 장난감 자동차 고객 지원 에이전트

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | Vroom&Dash 고객 지원 에이전트 |
| 브랜드명 | **Vroom&Dash** (장난감 자동차 전문 쇼핑몰) |
| 목적 | 장난감 자동차 쇼핑몰의 고객 문의를 AI 에이전트가 자동 응답 |
| 응답 언어 | 한국어 전용 |

## 2. 에이전트 주요 업무

### 2.1 주문/배송 조회
- 주문번호로 주문 상태 확인 (주문접수, 결제완료, 배송준비, 배송중, 배송완료)
- 배송 추적 정보 제공
- 반품/교환 요청 접수 및 안내

### 2.2 상품 문의
- 장난감 자동차 스펙 안내 (크기, 재질, 권장 연령, 배터리 유형 등)
- 재고 확인
- 가격 및 할인 정보
- 고객 취향 기반 상품 추천

### 2.3 기술 지원
- 장난감 자동차 조립 방법 안내
- 고장/불량 시 해결 방법 안내
- 배터리 교체 및 충전 방법
- 리모컨 페어링 등 사용법 안내

## 3. 기술 스택

### 3.1 에이전트 (백엔드)

| 구성 요소 | 기술 |
|-----------|------|
| 에이전트 프레임워크 | **Strands Agents SDK** (Python) |
| LLM 모델 | **Claude Haiku 4.5** (Amazon Bedrock) |
| 배포 | **Amazon Bedrock AgentCore** |
| 데이터 | 데모용 목업 데이터 (JSON/Python dict) |

### 3.2 프론트엔드

| 구성 요소 | 기술 |
|-----------|------|
| 프레임워크 | **React** |
| UI 형태 | 전용 채팅 페이지 |
| 스타일링 | CSS (frontend-design 스킬 활용, 고품질 디자인) |

## 4. 에이전트 Tool 구성

| Tool 이름 | 설명 | 입력 | 출력 |
|-----------|------|------|------|
| `lookup_order` | 주문 조회 | 주문번호 | 주문 상태, 상품명, 결제금액, 배송 정보 |
| `track_delivery` | 배송 추적 | 주문번호 | 배송 상태, 현재 위치, 예상 도착일 |
| `request_return` | 반품/교환 요청 | 주문번호, 사유 | 접수 확인, 반품 절차 안내 |
| `search_products` | 상품 검색 | 검색 키워드, 필터(연령, 가격대, 유형) | 상품 목록 |
| `get_product_detail` | 상품 상세 정보 | 상품ID | 스펙, 가격, 재고, 이미지 URL |
| `recommend_products` | 상품 추천 | 고객 취향/조건 | 추천 상품 목록 + 추천 사유 |
| `get_tech_guide` | 기술 지원 가이드 (KB RAG 벡터 검색) | 자연어 검색 질문 (query) | 검색된 가이드 내용, 출처, 신뢰도 |

## 5. 목업 데이터 구성

### 5.1 상품 카탈로그 (30개)
```
- 상품ID, 상품명, 카테고리(RC카/미니카/조립키트/트랙세트)
- 브랜드, 가격, 할인율, 재고수량
- 권장연령, 크기, 재질, 배터리유형
- 설명, 이미지URL
```

### 5.2 주문 데이터 (15건: 고객 3명 x 5건)
```
- 주문번호, 고객명, 상품ID, 수량, 결제금액
- 주문일시, 주문상태
- 배송사, 운송장번호, 배송상태, 예상도착일
- 고객 3명: 각각 주문 상태가 다양하게 분포 (주문접수~배송완료)
```

### 5.3 기술 지원 가이드 (카테고리별)
```
- 가이드ID, 상품ID, 문의유형(조립/고장/배터리/리모컨)
- 단계별 해결 방법
```

## 6. 프론트엔드 요구사항

### 6.1 페이지 구성
- **전용 채팅 페이지**: 전체 화면 채팅 인터페이스
- Vroom&Dash 브랜드 로고 및 헤더
- 에이전트 환영 메시지로 시작

### 6.2 채팅 UI 기능
- 사용자/에이전트 메시지 구분 표시
- 타이핑 인디케이터 (에이전트 응답 대기 중)
- 메시지 타임스탬프
- 상품 카드 형태의 리치 응답 지원 (이미지, 가격 등)
- 주문 상태 시각화 (스테퍼/타임라인)

### 6.3 디자인 방향
- 장난감/키즈 느낌의 밝고 활기찬 디자인
- 고품질 프로덕션 수준 UI (frontend-design 스킬 활용)

## 7. 시스템 아키텍처

> **핵심 설계 원칙**: Amazon Bedrock AgentCore의 관리형 서비스(Runtime, Identity, Memory, Gateway, Evaluation, Observability)를 활용하되, 필요한 AWS 리소스(DynamoDB, Knowledge Base 등)는 직접 프로비저닝하여 에이전트를 구성합니다.

### 7.1 전체 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 클라이언트 계층                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                          React 채팅 UI (SPA)                               │ │
│  │   - 채팅 인터페이스 (메시지 입력/표시)                                       │ │
│  │   - 리치 응답 렌더링 (상품 카드, 주문 타임라인)                               │ │
│  │   - 세션 ID 관리 (localStorage)                                            │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTPS (Invoke API)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            AgentCore Identity                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │   - 클라이언트 인증 (OAuth 2.0 - Cognito User Pool)                         │ │
│  │   - 세션별 접근 권한 검증                                                   │ │
│  │   - 요청 유효성 검사                                                        │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 인증 통과 후
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Amazon Bedrock AgentCore 플랫폼                          │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         AgentCore Runtime                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │                     Strands Agent 인스턴스                        │    │   │
│  │  │   - System Prompt + LLM (Claude Haiku 4.5)                       │    │   │
│  │  │   - Tool Orchestration                                           │    │   │
│  │  │   - 세션별 격리 실행 환경                                          │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                     │                                    │   │
│  │       ┌─────────────┬───────────────┼───────────────┬─────────────┐     │   │
│  │       │             │               │               │             │     │   │
│  │       ▼             ▼               ▼               ▼             ▼     │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────────┐  ┌───────────┐  ┌───────┐ │   │
│  │  │AgentCore│  │ Amazon   │  │ AgentCore   │  │ AgentCore │  │Agent- │ │   │
│  │  │Memory   │  │ Bedrock  │  │ Gateway     │  │Observabil.│  │Core   │ │   │
│  │  │(자체    │  │(Claude   │  │             │  │           │  │Eval.  │ │   │
│  │  │ 관리형) │  │ Haiku)   │  │             │  │           │  │       │ │   │
│  │  └─────────┘  └──────────┘  └──────┬──────┘  └───────────┘  └───────┘ │   │
│  │   대화/세션/     LLM 추론          │           트레이싱/       품질    │   │
│  │   장기메모리                        │           메트릭         평가    │   │
│  └─────────────────────────────────────┼────────────────────────────────────┘   │
│                                        │                                        │
│                                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      AWS Lambda Functions (Tool Handlers)               │   │
│  │                                                                          │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │   │
│  │  │ order-tools      │  │ product-tools    │  │ tech-guide-tool  │       │   │
│  │  │ ────────────────│  │ ────────────────│  │ ────────────────│       │   │
│  │  │ - lookup_order   │  │ - search_products│  │ - get_tech_guide │       │   │
│  │  │ - track_delivery │  │ - get_product_   │  │                  │       │   │
│  │  │ - request_return │  │   detail         │  │                  │       │   │
│  │  │                  │  │ - recommend_     │  │                  │       │   │
│  │  │                  │  │   products       │  │                  │       │   │
│  │  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │   │
│  │           │                      │                      │                │   │
│  └───────────┼──────────────────────┼──────────────────────┼────────────────┘   │
│              │                      │                      │                    │
│              ▼                      ▼                      ▼                    │
│  ┌─────────────────────────────────────────────┐  ┌─────────────────────────┐  │
│  │            Amazon DynamoDB                  │  │  Bedrock Knowledge Base │  │
│  │         (목업 비즈니스 데이터)               │  │    (기술 가이드 RAG)    │  │
│  │                                             │  │                         │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────┐ │  │  - 기술 문서 벡터 검색  │  │
│  │  │ products    │ │ orders      │ │custom-│ │  │  - RAG 기반 응답 생성   │  │
│  │  │ (상품 30개) │ │ (주문 15건) │ │ers    │ │  │                         │  │
│  │  └─────────────┘ └─────────────┘ └───────┘ │  └────────────┬────────────┘  │
│  └─────────────────────────────────────────────┘               │               │
│                                                                 ▼               │
│                                                    ┌─────────────────────────┐ │
│                                                    │   Amazon S3 Vectors     │ │
│                                                    │  (벡터 저장소)          │ │
│                                                    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 AgentCore Identity (인증/인가)

AgentCore Identity는 클라이언트가 AgentCore Runtime을 호출할 때 인증과 인가를 담당하는 서비스입니다.

#### 7.2.1 Identity 서비스 개요

| 기능 | 설명 |
|------|------|
| **클라이언트 인증** | OAuth 2.0 기반 인증 (Amazon Cognito User Pool 연동) |
| **세션 권한 검증** | 세션 ID별 접근 권한 확인 |
| **요청 검증** | 입력값 유효성 검사, 페이로드 크기 제한 |

#### 7.2.2 인증 흐름

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            인증/인가 흐름                                     │
│                                                                              │
│  [클라이언트]                                                                 │
│       │                                                                      │
│       │ 1. API 요청 + OAuth Token                                             │
│       │    (Cognito User Pool에서 발급받은 JWT)                              │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        AgentCore Identity                                │ │
│  │                                                                          │ │
│  │  2. 인증 정보 검증                                                        │ │
│  │     └─ OAuth: Cognito JWT 토큰 검증, 스코프 확인                          │ │
│  │                                                                          │ │
│  │  3. 권한 검증                                                             │ │
│  │     └─ 세션 ID 접근 권한                                                  │ │
│  │                                                                          │ │
│  │  4. 결과                                                                  │ │
│  │     ├─ 성공: 요청을 Runtime으로 전달                                      │ │
│  │     └─ 실패: 401/403 오류 반환                                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│       │                                                                      │
│       ▼ (인증 성공 시)                                                        │
│  [AgentCore Runtime]                                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 7.2.3 Identity 설정 (Vroom&Dash)

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| Auth Mode | `OAUTH` | OAuth 2.0 인증 |
| OAuth Provider | Amazon Cognito User Pool | 사용자 인증 및 JWT 발급 |
| Cognito User Pool ID | `us-east-1_xxxxxxxxx` | Cognito User Pool 식별자 |
| Cognito App Client ID | `xxxxxxxxxxxxxxxxxxxxxxxxxx` | 프론트엔드용 앱 클라이언트 |
| Session Isolation | `enabled` | 세션 간 데이터 격리 |
| Allowed Origins | `["https://vroomdash.example.com"]` | CORS 허용 오리진 |

### 7.3 AgentCore Memory (세션/대화 관리)

AgentCore Memory는 에이전트의 대화 히스토리를 세션 단위로 관리하는 서비스입니다. Strands Agents SDK와 연동하여 멀티턴 대화의 컨텍스트를 자동으로 유지합니다.

#### 7.3.1 Memory 서비스 개요

| 기능 | 설명 |
|------|------|
| **대화 히스토리 관리** | 세션별 메시지(user/assistant) 저장 및 검색 |
| **세션 격리** | 세션 ID 기반으로 대화 컨텍스트 분리 |
| **컨텍스트 윈도우** | LLM 호출 시 최근 대화를 자동으로 포함 |

#### 7.3.2 Memory 구성 요소

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AgentCore Memory                                 │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Conversation History                         │   │
│  │                                                                   │   │
│  │  Session: sess_abc123                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────┐│   │
│  │  │ turn 1:                                                      ││   │
│  │  │   [user]: "주문번호 ORD-001 조회해줘"                         ││   │
│  │  │   [assistant]: "주문번호 ORD-001을 확인했습니다..."           ││   │
│  │  │                                                              ││   │
│  │  │ turn 2:                                                      ││   │
│  │  │   [user]: "배송은 언제 도착해?"                               ││   │
│  │  │   [assistant]: "예상 도착일은 내일(1월 16일)입니다..."        ││   │
│  │  └─────────────────────────────────────────────────────────────┘│   │
│  │                                                                   │   │
│  │  Session: sess_xyz789                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────┐│   │
│  │  │ turn 1:                                                      ││   │
│  │  │   [user]: "5살 아이 RC카 추천해줘"                            ││   │
│  │  │   [assistant]: "5세 아이에게 적합한 RC카를 추천드립니다..."    ││   │
│  │  └─────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 7.3.3 Memory 설정

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| Memory ID | `vroom-dash-memory` | 메모리 인스턴스 식별자 |
| Session TTL | 24시간 | 단기 메모리 세션 유지 기간 |
| Max Messages | 100 | 세션당 최대 저장 메시지 수 |

**Long-term Memory 전략 (Vroom&Dash 맞춤 설정):**

| 전략 | 용도 | 네임스페이스 |
|------|------|-------------|
| `SEMANTIC` | 고객 정보, 주문 관련 팩트 추출 | `/facts/{actorId}/` |
| `SUMMARIZATION` | 대화 요약 저장 | `/summaries/{actorId}/{sessionId}/` |
| `USER_PREFERENCE` | 고객 선호도 학습 (연령대, 선호 브랜드 등) | `/preferences/{actorId}/` |

**Memory 생성 CLI 명령:**
```bash
agentcore add memory --name vroom-dash-memory \
  --strategies SEMANTIC,SUMMARIZATION,USER_PREFERENCE
agentcore deploy
```

#### 7.3.4 Strands Agent와 Memory 연동 (AgentCoreMemorySessionManager)

Strands SDK에서 AgentCore Memory와 연동하려면 `AgentCoreMemorySessionManager`를 사용합니다.

| 구성 요소 | 설명 |
|-----------|------|
| `AgentCoreMemoryConfig` | Memory 연동 설정 (memory_id, session_id, actor_id) |
| `AgentCoreMemorySessionManager` | Strands Agent의 session_manager로 전달하는 클래스 |
| `memory_id` | AgentCore Memory 인스턴스 식별자 |
| `session_id` | 대화 세션 식별자 (클라이언트에서 전달) |
| `actor_id` | 사용자/액터 식별자 (장기 메모리 네임스페이스용) |
| `batch_size` | 메시지 배치 크기 (API 호출 최적화, 기본값 1) |

**연동 코드 예시:**
```python
from strands import Agent
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Memory 설정
agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id="vroom-dash-memory",
    session_id=session_id,  # 클라이언트에서 전달받은 세션 ID
    actor_id=user_id        # 사용자 식별자
)

# Session Manager 생성
session_manager = AgentCoreMemorySessionManager(
    agentcore_memory_config=agentcore_memory_config,
    region_name="us-east-1"
)

# Agent에 session_manager 전달
agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    model=bedrock_model,
    tools=tools,
    session_manager=session_manager  # Memory 연동
)
```

#### 7.3.5 세션 흐름

```
[신규 세션]                        [기존 세션]
     │                                  │
     │ session_id 없음                  │ session_id 있음
     ▼                                  ▼
새 session_id 생성              기존 대화 히스토리 로드
     │                                  │
     ▼                                  ▼
빈 히스토리로 시작              이전 컨텍스트와 함께 LLM 호출
     │                                  │
     └──────────────┬───────────────────┘
                    ▼
            대화 턴 진행
                    │
                    ▼
         히스토리에 메시지 추가
         (user + assistant)
                    │
                    ▼
         TTL 만료 시 세션 삭제
```

### 7.4 AgentCore Gateway (Runtime의 Tool 호출 경로)

AgentCore Gateway는 **AgentCore Runtime이 Tool을 호출할 때 사용하는 서비스**입니다. 클라이언트 앞단이 아니라, Runtime 내부에서 Tool을 실행할 때 Gateway를 통해 실제 Tool Handler에 접근합니다.

#### 7.4.1 Gateway 서비스 개요

| 기능 | 설명 |
|------|------|
| **Tool Registry** | Tool 정의 및 스키마 중앙 관리 |
| **Tool 라우팅** | Runtime의 Tool 호출을 적절한 Handler로 라우팅 |
| **MCP 프로토콜** | Model Context Protocol 기반 Tool 통신 |
| **스키마 검증** | Tool 입출력 스키마 자동 검증 |
| **Tool별 접근 제어** | Tool 호출 권한 관리 |

#### 7.4.2 Gateway의 위치와 역할

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Gateway의 올바른 위치: Runtime → Gateway → Lambda         │
│                                                                              │
│                                                                              │
│  [클라이언트] ──────X────────▶ [AgentCore Gateway]   (잘못된 흐름)            │
│                                                                              │
│                                                                              │
│  [클라이언트] ──▶ [Identity] ──▶ [Runtime] ──▶ [Gateway] ──▶ [Lambda]        │
│                                                    │           (올바른 흐름) │
│                                                    │                        │
│                                                    ▼                        │
│                                        ┌─────────────────────┐              │
│                                        │  AWS Lambda Function│              │
│                                        │  (Tool Handler)     │              │
│                                        │         │           │              │
│                                        │    ┌────┴────┐      │              │
│                                        │    ▼         ▼      │              │
│                                        │ DynamoDB   KB/RAG   │              │
│                                        │ (목업 데이터)(기술 지원)│              │
│                                        └─────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 7.4.3 Gateway 아키텍처 (Runtime 내부 연동)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AgentCore Gateway                                │
│                       (Runtime의 Tool 호출 경로)                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         Tool Registry                                  │ │
│  │                                                                        │ │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │ │
│  │  │ lookup_order   │ │ track_delivery │ │ request_return │             │ │
│  │  │ ──────────────│ │ ──────────────│ │ ──────────────│             │ │
│  │  │ handler:      │ │ handler:      │ │ handler:      │             │ │
│  │  │ Lambda→DynamoDB│ │ Lambda→DynamoDB│ │ Lambda→DynamoDB│             │ │
│  │  └────────────────┘ └────────────────┘ └────────────────┘             │ │
│  │                                                                        │ │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │ │
│  │  │ search_products│ │get_product_    │ │recommend_      │             │ │
│  │  │ handler:      │ │detail          │ │products        │             │ │
│  │  │ Lambda→DynamoDB│ │ handler:      │ │ handler:       │             │ │
│  │  └────────────────┘ │ Lambda→DynamoDB│ │ Lambda→DynamoDB│             │ │
│  │                     └────────────────┘ └────────────────┘             │ │
│  │                                                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │ get_tech_guide                                                   │  │ │
│  │  │ ────────────────────────────────────────────────────────────────│  │ │
│  │  │ handler: Lambda → Bedrock Knowledge Base (RAG 검색)              │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│  ┌───────────────────────────────────┴───────────────────────────────────┐ │
│  │                         Tool Handler 연결                              │ │
│  │                                                                        │ │
│  │  Runtime이 Tool 호출 시:                                               │ │
│  │  1. Gateway가 Tool Registry에서 Handler(Lambda ARN) 조회               │ │
│  │  2. 입력 스키마 검증                                                   │ │
│  │  3. Lambda Function 호출 (동기 Invoke)                                │ │
│  │  4. Lambda가 DynamoDB 또는 Knowledge Base 조회                        │ │
│  │  5. 출력 스키마 검증                                                   │ │
│  │  6. 결과를 Runtime에 반환                                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.4.4 Gateway 설정

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| Gateway ID | `vroom-dash-gateway` | 게이트웨이 식별자 |
| Timeout | 30초 | Tool 실행 타임아웃 |
| Retry Policy | 3회 | Tool 실패 시 재시도 횟수 |

#### 7.4.5 Tool 등록 스키마 (Vroom&Dash 전용)

| Tool | Input Schema | Output Schema | Handler (Lambda) | 데이터 소스 |
|------|--------------|---------------|------------------|-------------|
| `lookup_order` | `{order_id: string}` | `{order_id, status, items[], total, shipping}` | `vroom-dash-order-tools` | DynamoDB: orders |
| `track_delivery` | `{order_id: string}` | `{status, location, carrier, eta}` | `vroom-dash-order-tools` | DynamoDB: orders |
| `request_return` | `{order_id: string, reason: string}` | `{return_id, instructions[]}` | `vroom-dash-order-tools` | DynamoDB: orders |
| `search_products` | `{query: string, filters?: {age?, price?, type?}}` | `{products[], total}` | `vroom-dash-product-tools` | DynamoDB: products |
| `get_product_detail` | `{product_id: string}` | `{id, name, specs, price, stock, images[]}` | `vroom-dash-product-tools` | DynamoDB: products |
| `recommend_products` | `{preferences: object}` | `{recommendations[], reasoning}` | `vroom-dash-product-tools` | DynamoDB: products |
| `get_tech_guide` | `{query: string}` | `{query, results[{content, source, confidence}], total}` | `vroom-dash-tech-guide` | **Knowledge Base** (RAG 벡터 검색) |

#### 7.4.6 Runtime-Gateway-Lambda 연동 흐름

```
┌────────────────────┐    ┌────────────────────┐    ┌──────────────┐    ┌───────────┐
│  AgentCore Runtime │    │  AgentCore Gateway │    │ AWS Lambda   │    │ DynamoDB/ │
│   (Strands Agent)  │    │                    │    │ (Tool Handler)│    │ KB        │
└─────────┬──────────┘    └─────────┬──────────┘    └──────┬───────┘    └─────┬─────┘
          │                         │                       │                  │
          │ 1. LLM이 Tool 호출 결정 │                       │                  │
          │   (lookup_order)        │                       │                  │
          │                         │                       │                  │
          │ 2. Tool 호출 요청       │                       │                  │
          │ ───────────────────────>│                       │                  │
          │                         │                       │                  │
          │                         │ 3. Lambda ARN 조회    │                  │
          │                         │   + 스키마 검증       │                  │
          │                         │                       │                  │
          │                         │ 4. Lambda Invoke      │                  │
          │                         │ ─────────────────────>│                  │
          │                         │                       │                  │
          │                         │                       │ 5. DynamoDB      │
          │                         │                       │    Query/Scan    │
          │                         │                       │ ────────────────>│
          │                         │                       │                  │
          │                         │                       │ 6. 데이터 반환   │
          │                         │                       │ <────────────────│
          │                         │                       │                  │
          │                         │ 7. Lambda 결과        │                  │
          │                         │ <─────────────────────│                  │
          │                         │                       │                  │
          │                         │ 8. 출력 스키마 검증   │                  │
          │                         │                       │                  │
          │ 9. Tool 결과 반환       │                       │                  │
          │ <───────────────────────│                       │                  │
          │                         │                       │                  │
          │ 10. LLM이 응답 생성     │                       │                  │
          │                         │                       │                  │
```

### 7.5 Bedrock Knowledge Base (기술 지원 RAG)

기술 지원 가이드 검색을 위해 Amazon Bedrock Knowledge Base를 사용합니다. `get_tech_guide` Tool이 Knowledge Base를 조회하여 RAG(Retrieval-Augmented Generation) 방식으로 관련 기술 문서를 검색합니다.

#### 7.5.1 Knowledge Base 개요

| 항목 | 설명 |
|------|------|
| **용도** | 장난감 자동차 기술 지원 문서 검색 |
| **데이터 소스** | 조립 가이드, 고장 해결, 배터리 교체, 리모컨 페어링 문서 |
| **검색 방식** | 벡터 유사도 검색 (RAG) |
| **임베딩 모델** | Amazon Titan Embeddings |

#### 7.5.2 Knowledge Base 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Bedrock Knowledge Base (RAG)                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        데이터 수집 파이프라인                           │ │
│  │                                                                        │ │
│  │  [S3: 기술 가이드 원본]                                                 │ │
│  │         │                                                              │ │
│  │         ▼                                                              │ │
│  │  [문서 파싱 & 청킹]                                                     │ │
│  │         │                                                              │ │
│  │         ▼                                                              │ │
│  │  [Titan Embeddings: 벡터 변환]                                         │ │
│  │         │                                                              │ │
│  │         ▼                                                              │ │
│  │  [벡터 저장 (Amazon S3 Vectors)]                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                          검색 흐름 (RAG)                               │ │
│  │                                                                        │ │
│  │  [get_tech_guide Tool 호출]                                            │ │
│  │         │                                                              │ │
│  │         │ query: "RC카 PRD-001 리모컨 페어링 방법"                      │ │
│  │         ▼                                                              │ │
│  │  [쿼리 임베딩 생성]                                                     │ │
│  │         │                                                              │ │
│  │         ▼                                                              │ │
│  │  [벡터 유사도 검색] ──▶ Top-K 관련 문서 검색                            │ │
│  │         │                                                              │ │
│  │         ▼                                                              │ │
│  │  [검색 결과 반환]                                                       │ │
│  │     - 관련 기술 가이드 텍스트                                          │ │
│  │     - 출처 정보 (문서명, 섹션)                                         │ │
│  │     - 신뢰도 점수                                                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.5.3 Knowledge Base 설정

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| Knowledge Base ID | `vroom-dash-tech-kb` | KB 식별자 |
| Data Source | S3 버킷 (`vroom-dash-tech-guides-dev-{ACCOUNT_ID}`) | 원본 문서 저장소 |
| Embedding Model | `cohere.embed-multilingual-v3` | 임베딩 모델 |
| Vector Store | Amazon S3 Vectors | 벡터 저장소 |
| Non-filterable Keys | `AMAZON_BEDROCK_TEXT`, `AMAZON_BEDROCK_METADATA` | 청크 텍스트/소스 메타데이터 (2KB filterable 제한 회피) |
| Chunk Size | 512 tokens | 문서 청크 크기 |
| Chunk Overlap | 50 tokens | 청크 간 중복 |
| Top-K | 3 | 검색 결과 개수 |

#### 7.5.4 기술 가이드 문서 구조

```
S3: vroom-dash-tech-guides-dev-{ACCOUNT_ID}/
├── assembly/                    # 조립 가이드
│   ├── rc-car-basic.md
│   ├── rc-car-advanced.md
│   └── track-set-assembly.md
├── troubleshooting/             # 고장 해결
│   ├── motor-issues.md
│   ├── battery-issues.md
│   └── controller-issues.md
├── battery/                     # 배터리 관련
│   ├── charging-guide.md
│   ├── battery-replacement.md
│   └── battery-safety.md
└── pairing/                     # 페어링 가이드
    ├── remote-pairing.md
    ├── app-connection.md
    └── bluetooth-setup.md
```

#### 7.5.5 get_tech_guide Tool과 KB 연동

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    get_tech_guide Tool 실행 흐름                              │
│                                                                              │
│  [사용자 질문]                                                                │
│  "RC카 리모컨이 연결이 안 돼요"                                               │
│         │                                                                    │
│         ▼                                                                    │
│  [LLM이 get_tech_guide 호출 결정]                                            │
│  input: {query: "RC카 리모컨이 연결이 안 돼요"}                               │
│         │                                                                    │
│         ▼                                                                    │
│  [Gateway가 Knowledge Base Handler(Lambda) 호출]                             │
│         │                                                                    │
│         ▼                                                                    │
│  [Knowledge Base RAG 벡터 검색]                                              │
│  쿼리: "RC카 리모컨이 연결이 안 돼요" (자연어 그대로 벡터 검색)                 │
│         │                                                                    │
│         ▼                                                                    │
│  [검색 결과]                                                                  │
│  {                                                                           │
│    "query": "RC카 리모컨이 연결이 안 돼요",                                   │
│    "results": [                                                              │
│      {                                                                       │
│        "content": "# 2.4GHz 리모컨 페어링 방법\n1. 전원을 끕니다...",         │
│        "source": "s3://vroom-dash-tech-guides-dev-<ACCOUNT_ID>/.../remote-pairing.md",   │
│        "confidence": 0.92                                                    │
│      }                                                                       │
│    ],                                                                        │
│    "total": 1                                                                │
│  }                                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  [LLM이 검색 결과를 바탕으로 친절한 응답 생성]                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.6 AgentCore Evaluation (에이전트 품질 평가)

AgentCore Evaluation은 에이전트의 응답 품질을 체계적으로 평가하고 지속적인 개선을 지원합니다.

#### 7.6.1 Evaluation 서비스 개요

| 기능 | 설명 |
|------|------|
| **자동 평가** | 사전 정의된 기준으로 응답 자동 평가 |
| **사용자 피드백** | 엄지 척/다운 피드백 수집 및 분석 |
| **테스트 세트** | 골든 테스트 케이스 관리 및 회귀 테스트 |
| **A/B 테스트** | 프롬프트/모델 변경 시 성능 비교 |
| **대시보드** | 평가 결과 시각화 및 트렌드 분석 |

#### 7.6.2 평가 기준 (Vroom&Dash 맞춤)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AgentCore Evaluation                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        평가 차원 (Dimensions)                          │ │
│  │                                                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │ │
│  │  │    정확성        │  │    유용성        │  │    안전성        │        │ │
│  │  │  (Accuracy)     │  │ (Helpfulness)   │  │   (Safety)      │        │ │
│  │  │                 │  │                 │  │                 │        │ │
│  │  │ - Tool 결과와   │  │ - 문의 해결 여부 │  │ - 부적절 응답    │        │ │
│  │  │   응답 일치     │  │ - 추가 안내 제공 │  │   여부          │        │ │
│  │  │ - 사실 정확성   │  │ - 고객 만족도   │  │ - 개인정보 노출  │        │ │
│  │  │                 │  │                 │  │ - 브랜드 톤 유지 │        │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │ │
│  │                                                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                             │ │
│  │  │   완전성        │  │   효율성        │                             │ │
│  │  │(Completeness)   │  │ (Efficiency)    │                             │ │
│  │  │                 │  │                 │                             │ │
│  │  │ - 필요 정보     │  │ - 응답 시간     │                             │ │
│  │  │   모두 포함     │  │ - Tool 호출 수  │                             │ │
│  │  │ - 후속 질문     │  │ - 토큰 사용량   │                             │ │
│  │  │   불필요        │  │                 │                             │ │
│  │  └─────────────────┘  └─────────────────┘                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      테스트 세트 (Golden Set)                          │ │
│  │                                                                        │ │
│  │  Category: 주문 조회                                                   │ │
│  │  ├─ TC-001: "주문번호 ORD-001 조회해줘"                                │ │
│  │  │   Expected: 주문 상태, 상품명, 배송 정보 포함                        │ │
│  │  ├─ TC-002: "내 주문 어디까지 왔어?"                                   │ │
│  │  │   Expected: 주문번호 확인 요청 또는 최근 주문 조회                   │ │
│  │                                                                        │ │
│  │  Category: 상품 문의                                                   │ │
│  │  ├─ TC-010: "5살 아이한테 맞는 RC카 추천해줘"                          │ │
│  │  │   Expected: 5세 적합 상품 2-3개 추천 + 이유                         │ │
│  │                                                                        │ │
│  │  Category: 기술 지원                                                   │ │
│  │  ├─ TC-020: "리모컨이 안 돼요"                                        │ │
│  │  │   Expected: 상품 확인 → 페어링 가이드 안내                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.6.3 Evaluation 설정 (구현 완료)

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| Online Eval Config ID | `VroomDash_online_eval-<CONFIG_SUFFIX>` | 온라인 평가 설정 |
| Agent Runtime ID | `VroomDash_VroomDash-<RUNTIME_SUFFIX>` | 평가 대상 런타임 |
| Auto-eval Rate | 100% (dev) | 자동 평가 샘플링 비율 |
| Evaluator Model | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 커스텀 평가용 LLM (inference profile) |
| Golden Set Size | 18 시나리오 | agentcore/eval/golden-test-set.json |
| Builtin Evaluators | 4개 | GoalSuccessRate, Correctness, ToolSelectionAccuracy, ToolParameterAccuracy |
| Custom Evaluators | 2개 | VroomDash_Accuracy (TRACE), VroomDash_Helpfulness (TRACE) |
| 설정 방식 | `agentcore.json` evaluators/onlineEvalConfigs 배열 | agentcore deploy 시 자동 반영 |
| 온디맨드 평가 | `scripts/08-run-evaluation.sh` | agentcore run eval CLI 사용 |
| 평가 결과 로그 | `/aws/bedrock-agentcore/evaluations/results/VroomDash_online_eval-*` | CloudWatch Logs |
| IAM 실행 역할 | `AgentCoreEvalRole-VroomDash_online_eval` | bedrock-agentcore.amazonaws.com assume |

#### 7.6.4 평가 워크플로우

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          평가 워크플로우                                  │
│                                                                          │
│  [실시간 평가]                                                            │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│  │ 대화 완료   │───▶│ 샘플링     │───▶│ 자동 평가   │───▶│ 점수 저장   │   │
│  │            │    │ (10%)      │    │ (5개 차원)  │    │            │   │
│  └────────────┘    └────────────┘    └────────────┘    └────────────┘   │
│                                                                          │
│  [정기 평가 (회귀 테스트)]                                                │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│  │ 스케줄     │───▶│ Golden Set │───▶│ 전체 평가   │───▶│ 리포트     │   │
│  │ (매일 2AM) │    │ 실행       │    │            │    │ 생성       │   │
│  └────────────┘    └────────────┘    └────────────┘    └────────────┘   │
│                                                                          │
│  [사용자 피드백]                                                          │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐                     │
│  │ 피드백     │───▶│ 라벨링     │───▶│ 분석/개선   │                     │
│  │ (thumbs)   │    │ (이유 분류)│    │ 포인트 도출 │                     │
│  └────────────┘    └────────────┘    └────────────┘                     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.7 AgentCore Observability (모니터링/트레이싱)

AgentCore Observability는 에이전트의 모든 활동을 추적하고 모니터링하는 관리형 서비스입니다.

#### 7.7.1 Observability 서비스 개요

| 기능 | 설명 |
|------|------|
| **분산 트레이싱** | 요청부터 응답까지 전체 흐름 추적 |
| **메트릭 수집** | 지연시간, 오류율, Tool 호출 통계 |
| **로그 수집** | 구조화된 로그 자동 수집 |
| **알림** | 임계값 기반 자동 알림 |
| **대시보드** | 실시간 모니터링 대시보드 |

#### 7.7.2 트레이싱 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AgentCore Observability                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         Trace 구조 예시                                 │ │
│  │                                                                        │ │
│  │  Trace ID: abc-123-xyz                                                │ │
│  │  │                                                                     │ │
│  │  ├─ [Span] Gateway Request                              (0ms - 2500ms)│ │
│  │  │   ├─ request_id: req_001                                           │ │
│  │  │   ├─ session_id: sess_abc                                          │ │
│  │  │   └─ user_message: "주문번호 ORD-001 조회해줘"                      │ │
│  │  │                                                                     │ │
│  │  ├─ [Span] Memory Load                                   (5ms - 15ms) │ │
│  │  │   ├─ history_count: 5                                              │ │
│  │  │   └─ session_state: {current_order: null}                          │ │
│  │  │                                                                     │ │
│  │  ├─ [Span] LLM Inference                               (20ms - 800ms) │ │
│  │  │   ├─ model: claude-3-5-haiku                                       │ │
│  │  │   ├─ input_tokens: 512                                             │ │
│  │  │   ├─ output_tokens: 128                                            │ │
│  │  │   └─ tool_calls: ["lookup_order"]                                  │ │
│  │  │                                                                     │ │
│  │  ├─ [Span] Tool: lookup_order                         (810ms - 950ms) │ │
│  │  │   ├─ input: {order_id: "ORD-001"}                                  │ │
│  │  │   ├─ output: {status: "배송중", ...}                               │ │
│  │  │   └─ status: success                                               │ │
│  │  │                                                                     │ │
│  │  ├─ [Span] LLM Inference (Final)                     (960ms - 1800ms) │ │
│  │  │   ├─ input_tokens: 640                                             │ │
│  │  │   └─ output_tokens: 256                                            │ │
│  │  │                                                                     │ │
│  │  ├─ [Span] Memory Save                              (1810ms - 1820ms) │ │
│  │  │   └─ saved_messages: 2                                             │ │
│  │  │                                                                     │ │
│  │  └─ [Span] Response                                 (1825ms - 1830ms) │ │
│  │      └─ response_length: 150 chars                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.7.3 메트릭 정의

| 메트릭 이름 | 타입 | 설명 | 알림 임계값 |
|-------------|------|------|------------|
| `request_latency_p50` | Histogram | 50번째 백분위 지연시간 | - |
| `request_latency_p99` | Histogram | 99번째 백분위 지연시간 | > 5초 |
| `error_rate` | Counter | 오류 발생 비율 | > 5% |
| `tool_call_count` | Counter | Tool 호출 횟수 (Tool별) | - |
| `tool_error_rate` | Counter | Tool 오류 비율 | > 10% |
| `token_usage` | Counter | 토큰 사용량 (input/output) | - |
| `active_sessions` | Gauge | 활성 세션 수 | - |
| `memory_operations` | Counter | 메모리 읽기/쓰기 횟수 | - |

#### 7.7.4 로그 형식

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            구조화된 로그 형식                                │
│                                                                             │
│  {                                                                          │
│    "timestamp": "2024-01-15T10:30:45.123Z",                                │
│    "level": "INFO",                                                         │
│    "trace_id": "abc-123-xyz",                                              │
│    "span_id": "span_456",                                                  │
│    "session_id": "sess_abc",                                               │
│    "event": "tool_execution",                                              │
│    "tool_name": "lookup_order",                                            │
│    "duration_ms": 140,                                                     │
│    "status": "success",                                                    │
│    "metadata": {                                                           │
│      "input": {"order_id": "ORD-001"},                                     │
│      "output_size": 256                                                    │
│    }                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.7.5 Observability 설정

> **참고**: AgentCore Observability는 별도 인스턴스 ID가 아닌 CloudWatch Transaction Search 활성화를 통해 설정됩니다. AgentCore Runtime은 기본적으로 세션 메트릭을 자동 수집하며, 상세 트레이스는 ADOT(AWS Distro for OpenTelemetry) SDK를 통해 계측합니다.

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| CloudWatch Transaction Search | 활성화 필수 | 트레이스/스팬 조회를 위한 1회성 설정 |
| Log Level | `INFO` (prod), `DEBUG` (dev) | CloudWatch Logs 로그 수준 |
| Trace Sampling | 100% (dev), 10% (prod) | X-Ray 트레이스 샘플링 비율 |
| Retention | 30일 | CloudWatch Logs 보존 기간 |
| CloudWatch Alarms | 활성화 | 임계값 기반 알림 |

#### 7.7.6 대시보드 구성

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Vroom&Dash Agent 대시보드                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [실시간 현황]                                                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │ 활성 세션       │ │ 분당 요청 수    │ │ 평균 응답 시간   │               │
│  │      24        │ │      156       │ │     1.2초       │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                                                                             │
│  [Tool 사용 현황 - 최근 1시간]                                               │
│  lookup_order      ████████████████████ 45%                                │
│  search_products   ████████████ 28%                                        │
│  get_product_detail████████ 18%                                            │
│  recommend_products███ 5%                                                  │
│  기타              ██ 4%                                                   │
│                                                                             │
│  [오류 추이 - 24시간]                                                       │
│       5% ─┼─────────────────────────────────────────                       │
│       4% ─┼──────────────────────────────────────── (임계값)               │
│       3% ─┼─────────────────────────────────────────                       │
│       2% ─┼────────╲    ╱────────────────────────────                      │
│       1% ─┼─────────╲──╱──────────────────────────────                     │
│       0% ─┼───────────────────────────────────────────                     │
│           00:00    06:00    12:00    18:00    24:00                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.8 Strands Agent 내부 구조 (AgentCore 서비스 통합)

#### 7.8.1 통합 Agent 구성 (AgentCoreMemorySessionManager 사용)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Strands Agent (AgentCore 통합)                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         System Prompt                                  │ │
│  │  - 역할: Vroom&Dash 고객 지원 전문가                                    │ │
│  │  - 톤: 친근하고 밝은 한국어                                             │ │
│  │  - Tool 사용 가이드라인                                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│  ┌───────────────────────────────────┴───────────────────────────────────┐ │
│  │                         Model Provider                                 │ │
│  │  - Provider: Amazon Bedrock                                           │ │
│  │  - Model: global.anthropic.claude-haiku-4-5-20251001-v1:0                     │ │
│  │  - Temperature: 0.7 | Max Tokens: 2048                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│  ┌───────────────────────────────────┴───────────────────────────────────┐ │
│  │                    AgentCore 서비스 연동                                │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │ # AgentCore Memory 연동 (AgentCoreMemorySessionManager)          │ │ │
│  │  │ from bedrock_agentcore.memory.integrations.strands.config import │ │ │
│  │  │     AgentCoreMemoryConfig                                        │ │ │
│  │  │ from bedrock_agentcore.memory.integrations.strands.session_manager│ │ │
│  │  │     import AgentCoreMemorySessionManager                         │ │ │
│  │  │                                                                  │ │ │
│  │  │ config = AgentCoreMemoryConfig(                                  │ │ │
│  │  │     memory_id="vroom-dash-memory",                               │ │ │
│  │  │     session_id=session_id,                                       │ │ │
│  │  │     actor_id=user_id                                             │ │ │
│  │  │ )                                                                │ │ │
│  │  │ session_manager = AgentCoreMemorySessionManager(config)          │ │ │
│  │  │   - 세션별 대화 히스토리 자동 관리 (단기 메모리)                   │ │ │
│  │  │   - 장기 메모리: 요약, 사용자 선호도, 의미론적 팩트 추출           │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │ # AgentCore Gateway 연동 (MCP 프로토콜)                          │ │ │
│  │  │ from strands.tools.mcp import MCPClient                          │ │ │
│  │  │ mcp_client = MCPClient(gateway_endpoint="vroom-dash-gateway")    │ │ │
│  │  │ tools = mcp_client.list_tools()                                  │ │ │
│  │  │   - Tool Registry에서 Lambda 함수 매핑 로드                       │ │ │
│  │  │   - Tool 스키마 자동 검증                                         │ │ │
│  │  │   - Lambda → DynamoDB/KB 호출                                    │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │ # AgentCore Observability (OpenTelemetry/ADOT 연동)              │ │ │
│  │  │ - AgentCore Runtime은 기본적으로 세션 메트릭 자동 수집            │ │ │
│  │  │ - 상세 트레이스/스팬은 ADOT SDK로 계측 필요                        │ │ │
│  │  │ - 메트릭/로그는 Amazon CloudWatch로 자동 전송                     │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         Agent 생성                                     │ │
│  │  agent = Agent(                                                       │ │
│  │      system_prompt=SYSTEM_PROMPT,                                     │ │
│  │      model=bedrock_model,                                             │ │
│  │      tools=tools,                                                     │ │
│  │      session_manager=session_manager  # Memory 연동 핵심              │ │
│  │  )                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.8.2 Agent 실행 흐름

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Agent 실행 흐름                                    │
│                                                                              │
│  [1. 요청 수신]                                                               │
│  Client → Identity(인증) → Runtime(Agent)                                    │
│  └─ Observability: trace 시작                                                │
│                                                                              │
│  [2. 컨텍스트 로드]                                                           │
│  Agent → Memory                                                              │
│  └─ 세션별 대화 히스토리 로드 (이전 대화 컨텍스트)                             │
│                                                                              │
│  [3. LLM 추론 (1차)]                                                         │
│  Agent → Bedrock                                                             │
│  └─ System Prompt + Context + User Message → Tool 호출 결정                  │
│                                                                              │
│  [4. Tool 실행]                                                              │
│  Agent → Gateway → Lambda → DynamoDB/Knowledge Base                         │
│  └─ Observability: tool span 기록                                           │
│                                                                              │
│  [5. LLM 추론 (최종)]                                                        │
│  Agent → Bedrock                                                             │
│  └─ Tool 결과 포함하여 최종 응답 생성                                         │
│                                                                              │
│  [6. 히스토리 저장]                                                          │
│  Agent → Memory                                                              │
│  └─ 새 메시지(user + assistant)를 대화 히스토리에 저장                        │
│                                                                              │
│  [7. 응답 반환]                                                              │
│  Agent → Client (Identity 경유)                                              │
│  └─ Observability: trace 종료, 메트릭 기록                                   │
│                                                                              │
│  [8. 비동기 평가 (샘플링)]                                                    │
│  Evaluation 서비스                                                           │
│  └─ 10% 샘플에 대해 자동 품질 평가 실행                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 7.8.3 System Prompt 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           System Prompt                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 1. 역할 및 정체성                                                       │ │
│  │    당신은 Vroom&Dash의 AI 고객 지원 전문가입니다.                        │ │
│  │    Vroom&Dash는 어린이용 장난감 자동차 전문 쇼핑몰입니다.                 │ │
│  │    RC카, 미니카, 조립키트, 트랙세트 등을 판매합니다.                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 2. 응답 지침                                                           │ │
│  │    - 한국어로만 응답합니다.                                             │ │
│  │    - 친근하고 밝은 톤을 유지합니다.                                      │ │
│  │    - 어린이와 부모 모두 이해하기 쉽게 설명합니다.                         │ │
│  │    - 전문 용어는 쉬운 말로 풀어서 설명합니다.                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 3. Tool 사용 가이드                                                     │ │
│  │    - 주문 조회: lookup_order → 주문번호가 필요합니다                     │ │
│  │    - 배송 추적: track_delivery → 주문번호로 배송 상태 확인               │ │
│  │    - 반품 요청: request_return → 주문번호와 사유 필요                    │ │
│  │    - 상품 검색: search_products → 키워드, 연령, 가격대 등 필터           │ │
│  │    - 상품 상세: get_product_detail → 상품ID로 상세 정보 조회             │ │
│  │    - 상품 추천: recommend_products → 고객 선호도 기반 추천               │ │
│  │    - 기술 지원: get_tech_guide → 자연어 질문으로 KB 벡터 검색 (RAG)     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 4. 제한 사항                                                           │ │
│  │    - 실제 결제나 환불 처리는 불가합니다 (안내만 가능)                     │ │
│  │    - 경쟁사 제품은 언급하지 않습니다                                     │ │
│  │    - 개인정보(주민번호, 카드번호 등)를 요청하지 않습니다                  │ │
│  │    - 확실하지 않은 정보는 추측하지 않고 확인 후 안내합니다               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.9 프론트엔드-AgentCore Runtime 연동

#### 7.9.1 API 연동 흐름

```
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│  React UI    │      │ AgentCore        │      │ AgentCore    │
│              │      │ Identity         │      │ Runtime      │
└──────┬───────┘      └────────┬─────────┘      └──────┬───────┘
       │                        │                       │
       │ 1. POST /invoke        │                       │
       │ + Authorization:       │                       │
       │   Bearer <Cognito JWT> │                       │
       │───────────────────────>│                       │
       │                        │                       │
       │                        │ 2. JWT 토큰 검증      │
       │                        │    (Cognito 서명 확인)│
       │                        │                       │
       │                        │ 3. Agent 호출         │
       │                        │──────────────────────>│
       │                        │                       │
       │                        │    4. Memory 로드     │
       │                        │    5. LLM 추론        │
       │                        │    6. Gateway→Tool    │
       │                        │    7. Memory 저장     │
       │                        │                       │
       │                        │ 8. Response           │
       │                        │<──────────────────────│
       │ 9. JSON Response       │                       │
       │ (+ trace_id)           │                       │
       │<───────────────────────│                       │
       │                        │                       │
```

> **참고**: AgentCore Identity는 OAuth 2.0 기반 인증을 사용합니다. 클라이언트는 Cognito User Pool에서 발급받은 JWT 토큰을 `Authorization: Bearer <token>` 헤더로 전달합니다. API Key 방식은 사용하지 않습니다.

#### 7.9.2 Runtime API 엔드포인트

클라이언트는 AgentCore Runtime을 직접 호출합니다 (Identity를 통해 인증됨).

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/agents/{agentId}/invoke` | POST | 동기 호출 (전체 응답 대기) |
| `/agents/{agentId}/invoke-stream` | POST | 스트리밍 호출 (SSE) |
| `/agents/{agentId}/sessions/{id}` | GET | 세션 정보 조회 |
| `/agents/{agentId}/sessions/{id}` | DELETE | 세션 삭제 |
| `/feedback` | POST | 사용자 피드백 제출 |

#### 7.9.3 요청/응답 형식

**요청 (Request)**
```json
{
  "session_id": "sess_abc123",
  "message": "주문번호 ORD-001 조회해줘",
  "context": {
    "user_id": "user_123",
    "channel": "web"
  },
  "options": {
    "stream": false,
    "include_trace": true
  }
}
```

**응답 (Response)**
```json
{
  "session_id": "sess_abc123",
  "message_id": "msg_xyz789",
  "response": "주문번호 ORD-001을 확인했습니다. 현재 배송중이며...",
  "tools_used": [
    {
      "name": "lookup_order",
      "input": {"order_id": "ORD-001"},
      "duration_ms": 140
    }
  ],
  "rich_content": {
    "type": "order_status",
    "data": {
      "order_id": "ORD-001",
      "status": "배송중",
      "eta": "2024-01-16"
    }
  },
  "trace_id": "abc-123-xyz",
  "latency_ms": 1830
}
```

#### 7.9.4 스트리밍 응답 (SSE)

```
[클라이언트]                              [AgentCore Runtime]
    │                                            │
    │  POST /invoke-stream                       │
    │  Accept: text/event-stream                 │
    │───────────────────────────────────────────>│
    │                                            │
    │  event: message_start                      │
    │  data: {"session_id": "sess_abc123"}       │
    │<───────────────────────────────────────────│
    │                                            │
    │  event: content_delta                      │
    │  data: {"text": "주문번호 ORD-001을 "}      │
    │<───────────────────────────────────────────│
    │                                            │
    │  event: tool_use                           │
    │  data: {"tool": "lookup_order", ...}       │
    │<───────────────────────────────────────────│
    │                                            │
    │  event: content_delta                      │
    │  data: {"text": "확인했습니다. 현재 "}      │
    │<───────────────────────────────────────────│
    │                                            │
    │  event: message_end                        │
    │  data: {"trace_id": "abc-123-xyz"}         │
    │<───────────────────────────────────────────│
```

#### 7.9.5 피드백 API

```json
// POST /feedback
{
  "session_id": "sess_abc123",
  "message_id": "msg_xyz789",
  "rating": "positive",  // "positive" | "negative"
  "reason": "helpful",   // optional: "helpful" | "accurate" | "fast" | "other"
  "comment": ""          // optional: 자유 코멘트
}
```

### 7.10 필요한 AWS 리소스 목록

#### 7.10.1 AgentCore 서비스 (관리형)

| 서비스 | 리소스 | 용도 | 비고 |
|--------|--------|------|------|
| **AgentCore Runtime** | Agent 인스턴스 | Strands Agent 호스팅/실행 | 서버리스 관리형 (15분 타임아웃) |
| **AgentCore Identity** | 인증 설정 | OAuth 2.0 클라이언트 인증/인가 | Cognito 연동, Token Vault 포함 |
| **AgentCore Memory** | Memory 인스턴스 | 단기(세션)/장기 메모리 관리 | Strands SDK: `AgentCoreMemorySessionManager` |
| **AgentCore Gateway** | Gateway 인스턴스 | MCP 프로토콜 기반 Tool 라우팅 | Lambda/OpenAPI/Smithy 연동 |
| **AgentCore Observability** | - | 트레이싱, 메트릭, 로깅 | CloudWatch + X-Ray 연동, ADOT SDK |
| **AgentCore Evaluation** | Evaluation 인스턴스 | 품질 평가, 테스트 | 자체 관리형 |

#### 7.10.2 직접 프로비저닝 필요 리소스

| 서비스 | 리소스 | 용도 | 예상 비용 (월) |
|--------|--------|------|---------------|
| **Amazon Bedrock** | Claude Haiku 4.5 모델 액세스 | LLM 추론 | 사용량 기반 (~$10-50) |
| **AWS Lambda** | Tool Handler 함수 3개 | Tool 실행 (DynamoDB/KB 조회) | ~$1-5 |
| **Amazon DynamoDB** | 비즈니스 데이터 테이블 3개 | 상품/주문/고객 목업 데이터 | ~$5-10 |
| **Bedrock Knowledge Base** | 기술 가이드 KB | RAG 검색 (get_tech_guide) | ~$5-15 |
| **Amazon Cognito** | User Pool | OAuth 2.0 사용자 인증/JWT 발급 | ~$0 (MAU 50K 무료) |
| **Amazon S3** | 기술 가이드 원본 버킷 | Knowledge Base 데이터 소스 | ~$1 |
| **Amazon S3 Vectors** | 벡터 저장소 | KB 벡터 임베딩 저장 | ~$1-5 |
| **Amazon CloudWatch** | 로그/메트릭 | Observability 데이터 저장 | ~$5-10 |
| **IAM** | 역할, 정책 | 권한 관리 | 무료 |
| **S3** (선택) | 정적 웹사이트 버킷 | React 앱 호스팅 | ~$1 |
| **CloudFront** (선택) | 배포 | CDN, HTTPS | ~$1-5 |

#### 7.10.3 DynamoDB 테이블 설계 (목업 비즈니스 데이터)

Tool Handler(Lambda)가 조회할 목업 비즈니스 데이터를 저장하는 DynamoDB 테이블입니다.
(참고: AgentCore Memory는 자체 관리형이므로 별도 테이블이 필요하지 않습니다)

| 테이블 | 파티션 키 | GSI | 용도 | 데이터 |
|--------|-----------|-----|------|--------|
| `vroom-dash-products` | `product_id` | `category-index` | 상품 카탈로그 | 30개 |
| `vroom-dash-orders` | `order_id` | `customer_id-index` | 주문 데이터 | 15건 (3명x5건) |
| `vroom-dash-customers` | `customer_id` | - | 고객 정보 | 3명 |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DynamoDB 테이블: vroom-dash-products                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Partition Key: product_id (String)                                         │
│                                                                             │
│  Attributes:                                                                │
│  - name: 상품명                                                              │
│  - category: "RC카" | "미니카" | "조립키트" | "트랙세트"                     │
│  - brand: 브랜드명                                                          │
│  - price: 가격                                                              │
│  - discount_rate: 할인율                                                    │
│  - stock: 재고 수량                                                         │
│  - recommended_age: 권장 연령                                               │
│  - specs: {size, material, battery_type, ...}                              │
│  - description: 상품 설명                                                   │
│  - image_url: 이미지 URL                                                    │
│                                                                             │
│  GSI: category-index (category로 조회)                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    DynamoDB 테이블: vroom-dash-orders                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Partition Key: order_id (String)                                           │
│                                                                             │
│  Attributes:                                                                │
│  - customer_id: 고객 ID                                                     │
│  - customer_name: 고객명                                                    │
│  - items: [{product_id, quantity, price}, ...]                             │
│  - total_amount: 결제 금액                                                  │
│  - order_date: 주문 일시                                                    │
│  - order_status: "주문접수" | "결제완료" | "배송준비" | "배송중" | "배송완료" │
│  - shipping: {carrier, tracking_number, status, location, eta}             │
│                                                                             │
│  GSI: customer_id-index (customer_id로 조회)                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    DynamoDB 테이블: vroom-dash-customers                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Partition Key: customer_id (String)                                        │
│                                                                             │
│  Attributes:                                                                │
│  - name: 고객명                                                             │
│  - email: 이메일                                                            │
│  - phone: 연락처                                                            │
│  - address: 배송 주소                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.10.4 비용 예상 (월간)

| 항목 | 단가 | 예상 사용량 | 월 비용 |
|------|------|------------|--------|
| **Bedrock Claude Haiku** | $0.25/1M input, $1.25/1M output | 10M tokens | ~$15 |
| **AgentCore Runtime** | $0.001/요청 | 10,000 요청 | ~$10 |
| **AWS Lambda** | $0.20/1M 요청 | 30K 호출 | ~$1 |
| **DynamoDB** | $0.25/GB + R/W | 1GB, 50K ops | ~$7 |
| **Knowledge Base** | 쿼리당 + 스토리지 | 5K 쿼리 | ~$10 |
| **S3 Vectors** | 벡터 저장/쿼리 | 1GB | ~$3 |
| **Cognito** | MAU 기반 | 50K 이하 | ~$0 (무료) |
| **CloudWatch** | $0.50/GB 수집 | 5GB | ~$3 |
| **S3** | $0.023/GB | 1GB | ~$0.03 |
| **합계** | | | **~$50-60** |

#### 7.10.5 IAM 권한 구성

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IAM Role: VroomDashAgentRole                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 신뢰 관계 (Trust Policy):                                                    │
│   - bedrock.amazonaws.com                                                   │
│   - bedrock-agentcore.amazonaws.com                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 권한 정책 (Permissions):                                                     │
│                                                                             │
│ AgentCore Runtime 권한:                                                      │
│   - bedrock-agentcore:InvokeAgent                                          │
│   - bedrock-agentcore:GetSession / CreateSession / DeleteSession           │
│                                                                             │
│ AgentCore Memory 권한:                                                       │
│   - bedrock-agentcore:CreateMemory / GetMemory / DeleteMemory              │
│   - bedrock-agentcore:PutEvent / GetEvent / ListEvents                     │
│   - bedrock-agentcore:ListSessions / ListMemoryRecords                     │
│   - bedrock-agentcore:RetrieveMemoryRecords                                │
│                                                                             │
│ AgentCore Gateway 권한:                                                      │
│   - bedrock-agentcore:InvokeTool / ListTools                               │
│                                                                             │
│ Bedrock 권한:                                                                │
│   - bedrock:InvokeModel (리소스: Claude Haiku ARN)                          │
│   - bedrock:Retrieve (리소스: Knowledge Base ARN)                           │
│                                                                             │
│ Lambda 권한:                                                                 │
│   - lambda:InvokeFunction (리소스: vroom-dash-* Lambda 함수들)              │
│                                                                             │
│ CloudWatch 권한 (Observability):                                             │
│   - logs:CreateLogGroup / CreateLogStream / PutLogEvents                   │
│   - cloudwatch:PutMetricData                                               │
│   - xray:PutTraceSegments / PutTelemetryRecords                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    IAM Role: VroomDashLambdaRole                            │
│                    (Tool Handler Lambda용)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 신뢰 관계 (Trust Policy):                                                    │
│   - lambda.amazonaws.com                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 권한 정책 (Permissions):                                                     │
│                                                                             │
│ DynamoDB 권한:                                                               │
│   - dynamodb:GetItem / Query / Scan                                        │
│   - 리소스: vroom-dash-products, vroom-dash-orders, vroom-dash-customers   │
│                                                                             │
│ Bedrock 권한 (tech-guide Lambda만):                                         │
│   - bedrock:Retrieve (리소스: Knowledge Base ARN)                           │
│                                                                             │
│ CloudWatch 권한:                                                             │
│   - logs:CreateLogStream / PutLogEvents                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.11 배포 환경 구성

#### 7.11.1 환경별 설정

| 환경 | 용도 | AgentCore 설정 |
|------|------|---------------|
| **dev** | 개발/테스트 | Memory TTL: 1시간, Trace 100%, Eval 100% |
| **staging** | 통합 테스트 | Memory TTL: 12시간, Trace 50%, Eval 50% |
| **prod** | 프로덕션 | Memory TTL: 24시간, Trace 10%, Eval 10% |

#### 7.11.2 AgentCore 리소스 설정 (환경별)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        환경별 리소스 설정                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [dev]                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Runtime:       vroom-dash-agent-dev                                  │   │
│  │ Identity:      OAuth 인증 (Cognito User Pool - dev)                   │   │
│  │ Memory:        vroom-dash-memory-dev                                 │   │
│  │                (SessionManager: batch_size=1, 장기메모리 전략 3종)   │   │
│  │ Gateway:       vroom-dash-gateway-dev     (MCP 프로토콜, Lambda 연동)│   │
│  │ Observability: CloudWatch (X-Ray Trace: 100%, Log: DEBUG)           │   │
│  │ Evaluation:    vroom-dash-eval-dev        (Sample: 100%)            │   │
│  │ Lambda:        vroom-dash-*-dev           (Tool Handler 3개)        │   │
│  │ DynamoDB:      vroom-dash-products/orders/customers-dev             │   │
│  │ Knowledge Base: vroom-dash-tech-kb-dev                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [prod]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Runtime:       vroom-dash-agent-prod                                 │   │
│  │ Identity:      OAuth 인증 (Cognito User Pool - prod)                  │   │
│  │ Memory:        vroom-dash-memory-prod                                │   │
│  │                (SessionManager: batch_size=10, 장기메모리 전략 3종)  │   │
│  │ Gateway:       vroom-dash-gateway-prod    (MCP 프로토콜, Lambda 연동)│   │
│  │ Observability: CloudWatch (X-Ray Trace: 10%, Log: INFO)             │   │
│  │ Evaluation:    vroom-dash-eval-prod       (Sample: 10%)             │   │
│  │ Lambda:        vroom-dash-*-prod          (Tool Handler 3개)        │   │
│  │ DynamoDB:      vroom-dash-products/orders/customers-prod            │   │
│  │ Knowledge Base: vroom-dash-tech-kb-prod                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.11.3 환경 변수

| 변수 | 설명 | dev | prod |
|------|------|-----|------|
| `AWS_REGION` | AWS 리전 | `us-east-1` | `us-east-1` |
| `AGENTCORE_RUNTIME_ID` | Runtime 식별자 | `vroom-dash-agent-dev` | `vroom-dash-agent-prod` |
| `AGENTCORE_MEMORY_ID` | Memory 식별자 | `vroom-dash-memory-dev` | `vroom-dash-memory-prod` |
| `AGENTCORE_GATEWAY_ENDPOINT` | Gateway 엔드포인트 URL | Gateway MCP 엔드포인트 (dev) | Gateway MCP 엔드포인트 (prod) |
| `MODEL_ID` | Bedrock 모델 ID | `anthropic.claude-3-5-haiku-*` | `anthropic.claude-3-5-haiku-*` |
| `COGNITO_USER_POOL_ID` | Cognito User Pool ID | `us-east-1_xxxDev` | `us-east-1_xxxProd` |
| `COGNITO_APP_CLIENT_ID` | Cognito App Client ID | `dev-client-xxx` | `prod-client-xxx` |
| `KNOWLEDGE_BASE_ID` | Knowledge Base ID | `kb-dev-xxx` | `kb-prod-xxx` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTEL 수집 엔드포인트 | CloudWatch OTLP 엔드포인트 | CloudWatch OTLP 엔드포인트 |

**Lambda 환경 변수**

| 변수 | 설명 | dev | prod |
|------|------|-----|------|
| `PRODUCTS_TABLE` | 상품 테이블명 | `vroom-dash-products-dev` | `vroom-dash-products-prod` |
| `ORDERS_TABLE` | 주문 테이블명 | `vroom-dash-orders-dev` | `vroom-dash-orders-prod` |
| `CUSTOMERS_TABLE` | 고객 테이블명 | `vroom-dash-customers-dev` | `vroom-dash-customers-prod` |
| `KNOWLEDGE_BASE_ID` | Knowledge Base ID | `kb-dev-xxx` | `kb-prod-xxx` |

#### 7.11.4 배포 체크리스트

```
[x] 1. IAM 역할 생성 및 권한 설정 (Agent용, Lambda용, KB용)
[x] 2. DynamoDB 테이블 생성 (products, orders, customers)
[x] 3. DynamoDB에 목업 데이터 적재
[x] 4. S3 버킷 생성 및 기술 가이드 문서 업로드
[x] 5. Bedrock Knowledge Base 생성 및 데이터 동기화 (S3 Vectors)
[x] 6. Bedrock Claude Haiku 모델 액세스 활성화
[x] 7. Lambda 함수 배포 (order-tools, product-tools, tech-guide)
[x] 8. Cognito User Pool 생성 및 앱 클라이언트 설정
[ ] 9. AgentCore Identity 설정 (OAuth/Cognito 연동) — Runtime에 직접 연동 필요
[x] 10. AgentCore Memory 생성 (agentcore deploy)
        - 장기 메모리 전략: SEMANTIC, SUMMARIZATION, USER_PREFERENCE
[x] 11. AgentCore Gateway 생성 + Tool-Lambda 매핑 (3 targets, 7 tools)
[x] 12. CloudWatch Transaction Search 활성화 (agentcore deploy 시 자동)
[x] 13. AgentCore Evaluation 인스턴스 생성 + 테스트 세트 등록 (agentcore.json + agentcore deploy)
[x] 14. AgentCore Runtime 배포 (Strands Agent + Gateway MCP 연동)
[x] 15. Runtime 엔드포인트 테스트
[x] 16. Lambda → DynamoDB 연동 테스트 (lookup_order, search_products 등 확인)
[x] 17. Lambda → Knowledge Base 연동 테스트 (get_tech_guide RAG 벡터 검색 확인)
[ ] 18. 프론트엔드 배포 및 연동 테스트 — 추후
[x] 19. Evaluation 골든 테스트 실행 (scripts/08-run-evaluation.sh, agentcore/eval/golden-test-set.json)
```

## 8. 구현 순서

1. **목업 데이터 생성** - 상품, 주문, 기술가이드 JSON 데이터
2. **에이전트 Tool 구현** - Strands SDK로 각 Tool 함수 작성
3. **에이전트 코어 로직** - 시스템 프롬프트, Tool 연결, 대화 흐름
4. **로컬 테스트** - CLI에서 에이전트 동작 확인
5. **AgentCore 배포** - Bedrock AgentCore에 에이전트 배포
6. **API 엔드포인트 구성** - 프론트엔드 연동용 API
7. **React 채팅 UI 구현** - 전용 채팅 페이지 개발
8. **통합 테스트** - 프론트엔드 ↔ 에이전트 연동 테스트

## 9. 배포 완료 리소스 (dev 환경)

### 9.1 AgentCore 리소스

| 리소스 | 이름/ID | ARN |
|--------|---------|-----|
| **Runtime** | VroomDash | `arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:runtime/VroomDash_VroomDash-<RUNTIME_SUFFIX>` |
| **Memory** | VroomDashMemory (SEMANTIC, USER_PREFERENCE, SUMMARIZATION) | `arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:memory/VroomDash_VroomDashMemory-<MEMORY_SUFFIX>` |
| **Gateway** | VroomDashGateway (3 targets) | `arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:gateway/vroomdash-vroomdashgateway-<GATEWAY_SUFFIX>` |
| **Gateway URL** | | `https://vroomdash-vroomdashgateway-<GATEWAY_SUFFIX>.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp` |

### 9.2 AWS 리소스

| 리소스 | 이름/ID |
|--------|---------|
| **DynamoDB** | `vroom-dash-products-dev` (30건), `vroom-dash-orders-dev` (15건), `vroom-dash-customers-dev` (3건) |
| **Lambda** | `vroom-dash-order-tools-dev`, `vroom-dash-product-tools-dev`, `vroom-dash-tech-guide-dev` |
| **S3 (데이터)** | `vroom-dash-tech-guides-dev-<ACCOUNT_ID>` (12 마크다운 문서) |
| **S3 Vectors** | 버킷: `vroom-dash-vectors-dev`, 인덱스: `vroom-dash-tech-index-dev` (dimension: 1024, cosine, non-filterable: `AMAZON_BEDROCK_TEXT`, `AMAZON_BEDROCK_METADATA`) |
| **Knowledge Base** | `<KNOWLEDGE_BASE_ID>` (`vroom-dash-tech-kb-dev`, S3_VECTORS 스토리지, `cohere.embed-multilingual-v3`) |
| **Cognito** | User Pool: `us-east-1_XXXXXXXXX`, App Client: (확인 필요) |
| **IAM** | `VroomDashAgentRole-dev`, `VroomDashLambdaRole-dev`, `VroomDashKBRole-dev` |
| **CloudFormation** | `AgentCore-VroomDash-dev` |

### 9.3 Gateway Tool-Lambda 매핑

| Gateway Target | Lambda 함수 | Tools |
|---------------|------------|-------|
| OrderTools | `vroom-dash-order-tools-dev` | `lookup_order`, `track_delivery`, `request_return` |
| ProductTools | `vroom-dash-product-tools-dev` | `search_products`, `get_product_detail`, `recommend_products` |
| TechGuideTools | `vroom-dash-tech-guide-dev` | `get_tech_guide` (KB RAG 벡터 검색) |

### 9.4 프로젝트 디렉토리 구조

```
toycar-shop-agent/
├── agentcore/                   # AgentCore CLI 설정 + CDK
│   ├── agentcore.json           # 프로젝트 설정 (Runtime, Memory, Gateway)
│   ├── aws-targets.json         # 배포 대상 (dev: us-east-1)
│   ├── cdk/                     # CDK 인프라 코드 (자동 관리)
│   └── tool-schemas/            # Gateway Tool 스키마
│       ├── order-tools-schema.json
│       ├── product-tools-schema.json
│       └── tech-guide-schema.json
├── backend/                     # Strands Agent 코드
│   ├── main.py                  # AgentCore 엔트리포인트 (Gateway MCP 연동)
│   ├── system_prompt.py         # 한국어 시스템 프롬프트
│   ├── pyproject.toml           # Python 의존성
│   ├── tools/                   # @tool 정의 (로컬 폴백용)
│   │   ├── order_tools.py       # lookup_order, track_delivery, request_return
│   │   ├── product_tools.py     # search_products, get_product_detail, recommend_products
│   │   └── tech_guide_tool.py   # get_tech_guide (KB 벡터 검색)
│   ├── data/                    # 목업 데이터 (DynamoDB 시딩 소스)
│   │   ├── products.py          # 30개 상품
│   │   ├── orders.py            # 15건 주문
│   │   ├── customers.py         # 3명 고객
│   │   └── tech_guides.py       # 참조용 기술 가이드 데이터
│   └── tech_guides/             # KB 원본 문서 (S3 업로드 → 벡터 임베딩)
│       ├── assembly/            # 조립 가이드 (3건)
│       ├── troubleshooting/     # 고장 해결 (3건)
│       ├── battery/             # 배터리 가이드 (3건)
│       └── pairing/             # 페어링 가이드 (3건)
├── lambda/                      # Lambda Tool Handler (DynamoDB/KB 조회)
│   ├── order-tools/handler.py
│   ├── product-tools/handler.py
│   └── tech-guide/handler.py
├── frontend/                    # React 채팅 UI
│   ├── public/index.html
│   └── src/
│       ├── App.js
│       ├── components/          # ChatPage, MessageBubble, OrderTimeline 등
│       └── services/api.js
└── scripts/                     # 인프라 프로비저닝 스크립트
    ├── config.sh                # 공통 설정
    ├── 01-setup-dynamodb.sh     # DynamoDB 테이블 생성
    ├── 02-seed-data.py          # 목업 데이터 적재
    ├── 03-setup-iam.sh          # IAM 역할 생성
    ├── 04-setup-s3-kb.sh        # S3 + S3 Vectors + Knowledge Base
    ├── 05-deploy-lambda.sh      # Lambda 배포
    ├── 06-setup-cognito.sh      # Cognito User Pool
    ├── 07-setup-agentcore.sh    # AgentCore 배포
    └── deploy-all.sh            # 전체 배포 마스터 스크립트
```
