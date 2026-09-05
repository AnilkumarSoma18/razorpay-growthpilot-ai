# P0 / P1 / P2 Task List — Razorpay GrowthPilot AI

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

## P0 — Must work (end-to-end acceptance test depends on all of these)

### Foundation
- [x] Project structure (`backend/`, `frontend/`, `data/`, `ml/`, `docs/`, `tests/`, ...)
- [ ] `docker-compose.yml` (postgres, redis, backend, frontend) — file written, not yet verified with `docker compose up` in this environment
- [x] `.env.example` with all required variables
- [x] `backend/requirements.txt`
- [ ] `frontend` Vite + TS + Tailwind + shadcn/ui scaffold

### Database
- [x] SQLAlchemy models for all tables in spec §13 (22 tables, verified created in Postgres)
- [x] Alembic migration setup + initial migration (verified: `alembic upgrade head` applied cleanly)
- [x] DB session/engine wiring (`app/database`)

### Synthetic Data
- [x] Generator: 560 products, 2,200 customers, 10,500 orders (verified via seed run)
- [x] Payments incl. failures/refunds (9,641 paid / 589 failed / 270 refunded), abandoned carts,
      customer segments (new/returning/high_value/price_sensitive/inactive), temporal spread (0-365 days)
- [x] Deliberate product-affinity correlations (laptop → bag/mouse/keyboard/headphones, camera → accessories, etc.)
- [x] Seed script (`scripts/seed_database.py`) + verified idempotent re-run behavior + `--reset` flag
- [x] Dataset labeled SYNTHETIC DEMO DATA (`Merchant.is_demo_data`, `is_synthetic_demo_data` in every analytics response)

### Analytics
- [x] `get_revenue_metrics`, `get_conversion_metrics`, `get_aov_metrics`, `get_retention_metrics`,
      `get_dashboard_summary` — implemented as `app/services/analytics_service.py`, all real SQL aggregates
- [ ] `get_product_metrics`, `get_customer_metrics`, `get_abandoned_carts` (detail-level), `get_failed_payments`,
      `get_product_affinity`, `get_customer_segments` — not yet implemented (next slice)

### FastAPI Foundation
- [x] `app/main.py` with CORS, root endpoint, router wiring
- [x] `GET /health` — verified returns `database: "connected"` against live Postgres
- [x] `GET /api/analytics/{revenue,conversion,aov,retention}` and `GET /api/dashboard/summary` —
      verified via curl against seeded demo merchant and via pytest against hand-computed expected values
- [x] Config via `app/config.py` (pydantic-settings, reads `.env`)
- [x] DB session dependency (`app/database/session.py::get_db`)

### Tests (22 passing)
- [x] `tests/database/test_models.py` — schema completeness, FK constraints, unique constraints
- [x] `tests/api/test_health.py` — health + root endpoint
- [x] `tests/api/test_analytics.py` — service-layer and HTTP-layer analytics tests against hand-computed values
- [x] `tests/data/test_synthetic_data_generator.py` — generator correctness (categories, products, affinity, customers, order volume)
- [x] `tests/integration/test_seed_pipeline.py` — small-scale end-to-end seed pipeline test
- [ ] Tests for `get_product_metrics` etc. once those services exist



### ML — Recommendation (P0 slice)
- [ ] Item-item / co-purchase recommendation model, trained on synthetic data
- [ ] Precision@K / Recall@K reported honestly (or limitation noted if data insufficient)

### Opportunity Engine
- [ ] Deterministic opportunity types (CROSS_SELL, UPSELL, BUNDLE, CART_RECOVERY,
      REPEAT_PURCHASE, RETENTION, FAILED_PAYMENT, LOW_CONVERSION, HIGH_VALUE_CUSTOMER)
- [ ] Scoring: Revenue Potential × Confidence × Customer Relevance × Actionability → 0–100
- [ ] `growth_opportunities` persistence + API

### Merchant Growth Agent
- [ ] LangGraph workflow (OBSERVE → ... → AUDIT), all nodes implemented
- [ ] LLM provider abstraction (Gemini default, swappable)
- [ ] Tool layer with input/output validation for every tool in spec §6

### Growth Simulator
- [ ] Simulation endpoint comparing ≥2 options with predicted conversion/revenue/profit
- [ ] All values explicitly labeled PREDICTIONS in API responses

### Approval Gate
- [ ] `approval_requests` table + API (create/approve/reject/expire)
- [ ] Hard-coded server-side enforcement: no execute path bypasses an unapproved request

### Audit Trail
- [ ] `audit_logs` table + write path from every tool execution
- [ ] `GET /api/audit` + Audit Trail page (frontend)

### AI Shopping Agent
- [ ] Intent understanding → catalog search → recommend → cart → order (chat-driven)
- [ ] Catalog APIs (`search`, `products/{id}`, `similar`, `frequently-bought`)
- [ ] Agent never invents product data — every claim backed by a DB read

### Cart / Order / Payments
- [ ] Cart CRUD, order creation
- [ ] Razorpay TEST MODE order creation
- [ ] Payment verification (signature check)
- [ ] Webhook endpoint + signature verification
- [ ] Demo webhook mode, clearly labeled SIMULATED

### End-to-End Tests
- [ ] Full acceptance flow (spec §36) scripted and passing

## P1 — Differentiators

- [ ] Revenue forecasting model (MAE/RMSE reported)
- [ ] Purchase probability model (classification metrics reported)
- [ ] Conversion prediction model
- [ ] A/B experimentation (control vs variant, uplift + confidence where valid)
- [ ] Cart recovery action + tracking
- [ ] Agent Trace page (decision summaries, not raw chain-of-thought)
- [ ] Advanced guardrails (prompt-injection test suite, rate limiting)
- [ ] Failure recovery (timeout, duplicate order/payment, webhook failure, DB failure,
      LLM unavailable, malformed tool call, low-confidence, insufficient data)
- [ ] 30+ agent evaluation scenarios with INPUT/EXPECTED/ACTUAL/PASS-FAIL
- [ ] Observability screen (latency, tool errors, agent steps, token usage)
- [ ] Revenue attribution methodology (documented + measured, not asserted)

## P2 — Polish

- [ ] Advanced animations / motion design
- [ ] Additional charts
- [ ] Deeper personalization
- [ ] Extra integrations
- [ ] Additional AI features

**Do not start P2 until P0 is fully working and tested.**

---

## Dependencies (initial pass)

**Backend:** fastapi, uvicorn, pydantic v2, sqlalchemy 2.x, alembic, psycopg2-binary
(or asyncpg), redis, langgraph, langchain-core, google-generativeai (Gemini default),
razorpay (official Python SDK), python-jose or authlib (auth), passlib (hashing),
pandas, numpy, scikit-learn, xgboost, pytest, pytest-asyncio, httpx (test client).

**Frontend:** react, typescript, vite, tailwindcss, shadcn/ui (radix primitives),
react-query or tanstack-query, react-router, recharts (real-data charts only), zod.

## Environment Variables (initial pass — finalized in `.env.example`)

```
DATABASE_URL=
REDIS_URL=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
LLM_PROVIDER=gemini          # gemini | openai | anthropic
LLM_API_KEY=
JWT_SECRET=
APP_ENV=development
DISCOUNT_LIMIT_PERCENT=20    # example configured policy ceiling
TRANSACTION_LIMIT_INR=
DEMO_WEBHOOK_MODE=true
```

## Razorpay API Requirements (initial pass)

- Orders API (`orders.create`) — TEST MODE keys only
- Payments API (verification via signature: `razorpay.utility.verify_payment_signature`)
- Webhooks (`payment.captured`, `payment.failed`, signature header `X-Razorpay-Signature`)
- No live-mode key ever accepted — validated at startup (`rzp_test_` prefix check)

## Security Risks Identified (initial pass — expanded in `docs/security.md`)

- LLM prompt injection attempting to bypass approval or discount limits
- LLM hallucinating product data not present in catalog
- Missing/incorrect webhook signature verification → forged payment events
- Duplicate order/payment on client retry without idempotency keys
- Unbounded discount/refund tool calls without server-side limit checks
- Secrets committed to source or logged in plaintext
- Confusing TEST MODE output with real payment confirmation in UI copy

## Failure Cases Identified (initial pass — expanded in `docs/security.md` / tests)

Razorpay timeout, invalid product id, duplicate order, duplicate payment, payment
verification failure, webhook delivery failure, database failure, LLM provider
unavailable, malformed tool call from LLM, low-confidence prediction, insufficient
data for a model/opportunity.

## Next Immediate Steps

1. `docker-compose.yml`, `.env.example`, `.gitignore`, `backend/requirements.txt`
2. SQLAlchemy models + Alembic init (spec §13)
3. Synthetic data generator (spec §14)
4. First vertical slice: analytics service → opportunity engine → one working
   opportunity type end-to-end, tested
