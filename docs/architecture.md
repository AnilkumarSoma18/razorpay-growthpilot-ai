# Architecture — Razorpay GrowthPilot AI

## 1. System Overview

GrowthPilot AI is two connected products sharing one backend and one data model:

1. **Merchant Growth Agent** — a LangGraph-orchestrated agent that observes merchant
   commerce data, detects revenue opportunities, predicts their impact with real ML
   models, simulates outcomes, requests human approval for money-affecting actions,
   executes only through validated tools, and writes a full audit trail.
2. **AI Shopping Agent** — a conversational commerce agent for customers that searches
   a real product catalog, builds a cart, creates an order, and completes a Razorpay
   **TEST MODE** payment, verified server-side.

Both agents are thin reasoning layers on top of a strict service/tool boundary. The
LLM never touches the database or Razorpay directly.

## 2. Request Flow

```
USER
 │
 ▼
FRONTEND (React + TS + Vite)
 │  REST / JSON
 ▼
FASTAPI (backend/app/api)
 │
 ▼
LANGGRAPH ORCHESTRATOR (backend/app/workflows)
 │  emits tool calls only, never raw SQL/HTTP
 ▼
VALIDATED TOOLS (backend/app/tools)
 │  pydantic-validated inputs/outputs, auth + limit checks
 ▼
SERVICE LAYER (backend/app/services)
 │  business logic, idempotency, transactions
 ▼
DATABASE (PostgreSQL via SQLAlchemy) / RAZORPAY (TEST MODE)
 │
 ▼
RESULT ──► AUDIT LOG (backend/app/observability + audit_logs table)
```

Why this shape: an LLM that can freely call arbitrary internal functions or write SQL
is a standing risk for a payments product. Routing every effect through a narrow,
independently-testable tool layer means the worst a prompt-injected or hallucinating
agent can do is call a *valid* tool with *rejected* inputs — never touch the DB or
Razorpay directly. This is elaborated in `docs/security.md`.

## 3. Backend Module Responsibilities

| Module | Responsibility |
|---|---|
| `app/api` | FastAPI routers; request/response schemas only, no business logic |
| `app/agents` | LangGraph agent definitions (Merchant Growth Agent, Shopping Agent) |
| `app/workflows` | The explicit LangGraph state graphs (OBSERVE → ... → AUDIT) |
| `app/ai` | LLM provider abstraction (Gemini default, OpenAI/Anthropic swappable), prompt templates, structured-output parsing |
| `app/tools` | Tool functions the agent may call — each is pydantic-validated in and out |
| `app/services` | Business logic: analytics, opportunity engine, cart/order, payments, approvals |
| `app/ml` | Purchase probability, recommendation engine, conversion prediction, revenue forecasting |
| `app/models` | SQLAlchemy ORM models |
| `app/schemas` | Pydantic schemas (API + tool I/O contracts) |
| `app/database` | Session/engine setup, Alembic wiring |
| `app/security` | Auth, role checks, transaction/discount limits, prompt-injection defenses, rate limiting |
| `app/observability` | Structured logging, latency tracking, agent trace recording |

## 4. Agent Architecture (LangGraph)

Explicit graph per spec §6, not a single "agent loop":

```
OBSERVE → ANALYZE → IDENTIFY_OPPORTUNITY → PREDICT_IMPACT → GENERATE_STRATEGY
   → SIMULATE → REQUEST_APPROVAL → EXECUTE → MEASURE → AUDIT
```

Each node is a plain Python function with a typed state object in/out. The LLM is
invoked only inside `ANALYZE`, `GENERATE_STRATEGY`, and the shopping agent's
`UNDERSTAND_INTENT` equivalent — the rest is deterministic code (retrieval, ML
inference, validation, persistence). This keeps the ML metrics and financial
calculations honest: they come from `app/ml` and `app/services`, not from asking
the LLM to "predict revenue."

`REQUEST_APPROVAL` is a hard gate: any node downstream of it (`EXECUTE`) checks a
persisted `approval_requests.status == 'approved'` before running. There is no
code path where the agent can execute a money-affecting tool without that row
existing and being approved.

## 5. Money-Safety Pipeline

Every tool that touches money or discounts runs:

```
VALIDATE INPUT (pydantic + business rules)
 → AUTHORIZE (role check)
 → CHECK LIMITS (discount %, transaction size vs configured policy)
 → CHECK APPROVAL (approval_requests row, if required for this action type)
 → CREATE IDEMPOTENCY KEY
 → EXECUTE (service layer, DB transaction)
 → VERIFY (re-read state / Razorpay verification)
 → RECORD AUDIT (audit_logs row, always — success or failure)
```

If any step fails, the tool returns a structured rejection (`{status: "rejected",
reason, safer_alternative}`) rather than raising an opaque error the LLM might
paraphrase incorrectly.

## 6. Data Flow: Shopping Agent → Payment

```
customer message → intent extraction → catalog search (real DB query)
 → recommendation (ML re-rank, not LLM invention) → cart tool → order tool
 → create_razorpay_order (TEST MODE) → client-side checkout
 → webhook OR manual verify → verify_payment tool (Razorpay signature check)
 → order confirmed → analytics/audit updated
```

Payment status is never inferred from client-side callbacks alone — always
confirmed against Razorpay's verification (signature check) or a backend
poll, per §20 (never claim success when payment status is uncertain).

## 7. Why These Technology Choices

See `docs/decisions.md` for the full rationale (LangGraph, PostgreSQL, ML vs LLM
split, approval gates, TEST MODE, idempotency, audit logs, synthetic data).

## 8. Directory Layout

```
razorpay-growthpilot-ai/
├── frontend/                # React + TS + Vite + Tailwind + shadcn/ui
├── backend/
│   └── app/
│       ├── api/            # FastAPI routers
│       ├── agents/         # LangGraph agent definitions
│       ├── ai/             # LLM provider abstraction
│       ├── tools/          # Validated agent tools
│       ├── ml/             # Purchase prob, recs, conversion, forecasting
│       ├── services/       # Business logic
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas
│       ├── database/       # Engine/session, migrations wiring
│       ├── workflows/      # LangGraph state graphs
│       ├── security/       # Auth, limits, guardrails
│       ├── observability/  # Logging, tracing, metrics
│       └── main.py
├── data/                    # Synthetic data generation + seed scripts
├── ml/                      # Model training notebooks/scripts, saved artifacts
├── evaluation/               # Agent evaluation scenarios (30+)
├── docs/                    # architecture, product, ai-agents, security, evaluation, decisions
├── scripts/                  # dev/setup scripts
├── tests/                    # pytest suite
└── screenshots/
```

## 9. Current Status

This is the initial scaffold (structure + planning docs). No business logic,
models, or API endpoints are implemented yet — see `docs/tasklist.md` for the
P0/P1/P2 breakdown and current progress.
