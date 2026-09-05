# Razorpay GrowthPilot AI

Autonomous Merchant Growth & Agentic Commerce Engine for the Razorpay AI Buildathon.

## Project Overview

Razorpay GrowthPilot AI is a multi-agent system designed to act as an autonomous growth marketer and shopping assistant for merchants. It leverages analytical databases, LangGraph for orchestrated intelligence, and Razorpay for seamless test checkout integrations.

### BUILDATHON DEMO ENVIRONMENT
- **Synthetic Data**: The platform currently uses a strictly synthetic static DataFrame / SQL Mock for demonstrating ML matrices.
- **Razorpay TEST mode**: The application operates ONLY in RAZORPAY_MODE=test using the Razorpay standard checkout pipeline.
- **PostgreSQL requirement**: The complete relational pipeline depends on Docker and PostgreSQL. In isolated test environments, the API relies on SQLAlchemy query mocks.

## Architecture
- **Frontend**: React + Vite + Tailwind CSS + shadcn/ui.
- **Backend**: FastAPI + SQLAlchemy + Alembic.
- **AI/ML**: LangGraph orchestrates Agent Intents. A custom Item-Item Collaborative Filtering recommendation pipeline acts as the analytical brain.
- **Payments**: Razorpay Python SDK with backend signature validation (Zero-trust frontend architecture).

## Core Features
1. **Merchant Command Center**: Live aggregated metrics.
2. **Growth Opportunities**: Identifies cross-sell potential using observed data + ML Signals.
3. **Growth Simulator**: Test strategies before execution safely.
4. **Human-in-the-loop Governance**: Strict backend approval gates required before action execution.
5. **AI Shopping Assistant**: Intent-based semantic routing tied directly to Razorpay's Cart and Order checkout flows.

## Security
- Authoritative Backend Math (Strict Decimal usage, mitigating binary floating point tampering).
- Webhook Payload HMAC Verification over raw bytes.
- Isolated Agent Intents preventing generic prompt injections from triggering execution rules.
