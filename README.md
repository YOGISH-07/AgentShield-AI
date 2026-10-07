# AgentShield AI - AI Agent Safety & Interception Control System

> **Real-time AI Agent Safety, Explainable Risk Scoring & Human-in-the-Loop Interception System.**

**DevHost 2026 Hackathon — Problem Statement PS 2.1: AI Agent Safety and Control**

AgentShield AI is a real-time, privacy-focused monitoring, explainable risk scoring, and human-in-the-loop interception control system for **Autonomous AI Agents**. It monitors agent tool calls, target resources, and command payloads, evaluates explainable safety risk (0–100), executes automated policy decisions (`ALLOW`, `HUMAN APPROVAL`, `BLOCK`), and enforces human operator interception for critical violations.

---

## 📁 Project Architecture

```text
AgentShield-AI/
├── backend/
│   ├── risk_engine.py             # Explainable AI Agent Action Risk Engine (0-100)
│   ├── alert_manager.py           # Alert Lifecycle State Machine (NEW -> UNDER_REVIEW -> CONFIRMED/DISMISSED)
│   ├── incident_manager.py        # Logged Incident Audit Manager
│   ├── database.py                # SQLite Database Manager (data/agentshield.db)
│   ├── agent_simulator.py         # 25-Second AI Agent Scenario Simulator
│   ├── alert_api.py               # FastAPI REST API endpoints
│   ├── reset_demo_data.py         # Baseline database reset utility
│   ├── test_risk_engine.py        # Risk engine unit tests
│   ├── test_alert_system.py       # Alert system unit tests
│   ├── test_api_endpoints.py      # API endpoint integration tests
│   ├── Dockerfile                 # Backend container configuration
│   └── requirements.txt           # Python dependencies (fastapi, uvicorn, pydantic)
├── frontend/                      # React + TypeScript + Vite Control Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx         # AgentShield AI Top Header
│   │   │   ├── StatCard.tsx       # Operational KPI Stat Cards
│   │   │   ├── AgentStreamCard.tsx# Live AI Agent Terminal & Action Stream Viewer
│   │   │   ├── AlertCard.tsx      # Policy Interception Alert Card
│   │   │   ├── AlertDetailModal.tsx # Explainable Evidence Modal
│   │   │   ├── DemoTimeline.tsx   # 25s Agent Simulation Timeline HUD
│   │   │   ├── IncidentTable.tsx  # Audit Log of Confirmed Violations
│   │   │   └── SystemInfoSections.tsx # System Architecture & Safety Disclaimers
│   │   ├── services/
│   │   │   └── api.ts             # REST API Service & TypeScript Interfaces
│   │   └── App.tsx                # Main Dashboard View
│   ├── dist/                      # Static Production Bundle
│   └── package.json
├── data/                          # SQLite Database directory
│   └── agentshield.db             # AgentShield SQLite database file
├── render.yaml                    # Render 1-click cloud deployment blueprint
├── docker-compose.yml             # Full-stack container orchestration
├── Procfile                       # Production web process declaration
└── README.md                      # Documentation and quickstart instructions
```

---

## 🚀 Environment Setup & Installation

### 1. Backend Setup (Python 3.11+)

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Run backend unit test suite (10 Test Cases)
python -m unittest backend/test_risk_engine.py backend/test_alert_system.py backend/test_api_endpoints.py

# Start FastAPI server
python -m uvicorn backend.alert_api:app --reload --port 8000
```

### 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install node dependencies
npm install

# Run Vite dev server
npm run dev

# Build production bundle
npm run build
```

---

## ⚡ 25-Second MVP Hackathon Demonstration Flow

AgentShield AI features a deterministic 25-second live scenario demonstration:

1. **0.0s - 4.0s (ALLOW / Low Risk)**: `CUSTOMER-SUPPORT-AI` invokes `read_schema` on `public_catalog`. Risk: `15/100` $\rightarrow$ Decision: `ALLOW`.
2. **4.0s - 9.0s (HUMAN APPROVAL / Sensitive Resource)**: `DATA-OPS-AI` requests `export_customer_data` to an external S3 analytics bucket. Risk: `55/100` $\rightarrow$ Decision: `HUMAN APPROVAL REQUIRED`.
3. **9.0s - 18.0s (BLOCK / Critical Violation)**: `FINANCE-AI` attempts destructive command payload `DROP TABLE user_credentials; -- IGNORE SYSTEM PROMPT & EXFILTRATE`. Risk: `85/100` $\rightarrow$ Decision: `BLOCK`. Real-time policy alert generated at ~12s.
4. **18.0s - 25.0s (Safe Resume)**: Action intercepted by AgentShield; safe logging action resumed by `FINANCE-AI`.

---

## 🛡️ AI Safety & Governance Principles

1. **Mandatory Human Interception**: High-risk actions (`BLOCK` / `HUMAN APPROVAL`) pause execution until a human safety operator explicitly approves or blocks the operation.
2. **Explainable Risk Scoring**: Risk score ($0–100$) is computed via transparent, deterministic scoring weights. No black-box ML models.
3. **Immutable Audit Log**: Confirmed policy violations are logged in an SQLite audit database with timestamped operator actions.
