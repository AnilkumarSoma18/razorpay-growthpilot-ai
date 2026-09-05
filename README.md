# Razorpay GrowthPilot AI

> An autonomous AI growth employee for ecommerce merchants — plus a conversational
> AI shopping agent that turns customer intent into a completed Razorpay **TEST MODE**
> payment.

**Status: early scaffold.** This README will be expanded as P0 lands. It intentionally
does not yet claim features that aren't implemented (see `docs/tasklist.md` for what's
done vs. planned) — nothing here is a finished product yet.

## What this is

Two connected loops:

- **Merchant loop:** payment data → AI analysis → ML prediction → revenue opportunity
  → simulation → human approval → safe execution → measurement → audit.
- **Customer loop:** intent → catalog discovery → recommendation → cart → Razorpay
  TEST MODE payment.

See `docs/architecture.md` for the full system design and `docs/product.md` for the
product rationale (once written).

## Project layout

```
razorpay-growthpilot-ai/
├── frontend/     React + TypeScript + Vite + Tailwind + shadcn/ui
├── backend/      FastAPI + LangGraph + SQLAlchemy
├── data/         Synthetic data generation
├── ml/           Model training scripts/artifacts
├── evaluation/   Agent evaluation scenarios
├── docs/         Architecture, product, security, decisions
├── scripts/      Dev/setup scripts
└── tests/        pytest suite
```

## Known limitations

This is the P0 foundation slice. Implemented and verified: database schema,
migrations, synthetic data generation/seeding, health check, and analytics
APIs (revenue, conversion, AOV, retention, dashboard summary). Not yet
implemented: ML models, the opportunity engine, LangGraph agents, the AI
shopping agent, cart/order/checkout flows, and Razorpay integration — these
land in later P0/P1 slices per `docs/tasklist.md`.

## Getting started (P0 foundation)

These are the exact commands used to build and verify this slice.

### 1. Install PostgreSQL and create the database

```bash
sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib
sudo service postgresql start

sudo -u postgres psql -c "CREATE USER growthpilot WITH PASSWORD 'growthpilot';"
sudo -u postgres psql -c "CREATE DATABASE growthpilot OWNER growthpilot;"
sudo -u postgres psql -c "ALTER USER growthpilot CREATEDB;"   # needed so the
                                                                # test suite can
                                                                # create growthpilot_test
```

(If you use `docker compose up postgres` instead, the `docker-compose.yml`
already creates the `growthpilot` user/db from `.env` — skip the manual
steps above.)

### 2. Configure environment variables

```bash
cp .env.example .env
# DATABASE_URL in .env.example already points at the local Postgres above;
# edit only if your credentials differ. Razorpay/LLM keys are not required
# for this slice.
```

### 3. Install backend dependencies

```bash
cd backend
pip install --break-system-packages -r requirements.txt
```

### 4. Run database migrations

```bash
# from backend/
export PYTHONPATH=$(pwd)
python3 -m alembic upgrade head
```

Verify tables were created:

```bash
PGPASSWORD=growthpilot psql -h localhost -U growthpilot -d growthpilot -c "\dt"
```

You should see 22 tables (merchants, users, customers, products, orders,
payments, growth_opportunities, audit_logs, ... — the full schema in
`docs/architecture.md` §13) plus `alembic_version`.

### 5. Seed synthetic demo data

```bash
# from the repo root
python3 scripts/seed_database.py
```

This creates 1 demo merchant, 560+ products, 2,200 customers, 10,500+ orders
with payments (paid/failed/refunded), 58,000+ cart events (converted +
abandoned), and 15,000+ customer behavioral events — all clearly marked as
synthetic demo data (`Merchant.is_demo_data = True`).

Re-running the script without flags is a no-op if data already exists; to
wipe and regenerate:

```bash
python3 scripts/seed_database.py --reset
```

### 6. Start the backend

```bash
cd backend
export PYTHONPATH=$(pwd)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's up:

```bash
curl http://localhost:8000/health
# {"status":"ok","app_env":"development","database":"connected",...}
```

OpenAPI docs: http://localhost:8000/docs

### 7. Try the analytics endpoints

```bash
MERCHANT_ID=$(PGPASSWORD=growthpilot psql -h localhost -U growthpilot -d growthpilot \
  -t -c "SELECT id FROM merchants WHERE business_email='growth@growthpilot-demo.test';" | tr -d ' ')

curl "http://localhost:8000/api/dashboard/summary?merchant_id=$MERCHANT_ID"
curl "http://localhost:8000/api/analytics/revenue?merchant_id=$MERCHANT_ID"
curl "http://localhost:8000/api/analytics/conversion?merchant_id=$MERCHANT_ID"
curl "http://localhost:8000/api/analytics/aov?merchant_id=$MERCHANT_ID"
curl "http://localhost:8000/api/analytics/retention?merchant_id=$MERCHANT_ID"
```

### 8. Run the test suite

Tests run against an isolated `growthpilot_test` database (never the demo
database), created once:

```bash
sudo -u postgres psql -c "CREATE DATABASE growthpilot_test OWNER growthpilot;"
```

Then from the repo root:

```bash
pip install --break-system-packages -r backend/requirements.txt
python3 -m pytest tests/ -v
```

All 22 tests should pass: schema/model integrity, health endpoint, analytics
services and API endpoints (against hand-computed expected values), synthetic
data generator behavior, and a small-scale seed-pipeline integration test.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design
- [`docs/tasklist.md`](docs/tasklist.md) — P0/P1/P2 breakdown and current status
- `docs/product.md`, `docs/ai-agents.md`, `docs/security.md`, `docs/evaluation.md`,
  `docs/decisions.md` — to be written as those parts land

## License

TBD.

