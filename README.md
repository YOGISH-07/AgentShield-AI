# CineGuard AI - Computer Vision Cinema Security Intelligence Prototype

CineGuard AI is a modular, privacy-focused computer-vision prototype built using **Ultralytics YOLOv8**, **OpenCV**, **SQLite**, **FastAPI**, and **React + TypeScript + Vite**. It detects and tracks people and mobile phones, evaluates spatial alignment relative to a configurable cinema screen region, extracts behavioral duration signals, calculates explainable risk scores, and manages human-in-the-loop alert lifecycles and verified incidents.

---

## 📁 Project Structure

```text
CineGuard-AI/
├── backend/
│   ├── detector.py                # Phase 1: YOLO object detection module
│   ├── video_processor.py         # Phase 1: Video stream reader & annotator
│   ├── main.py                    # Phase 1: CLI runner (outputs videos/output_detection.mp4)
│   ├── tracker.py                 # Phase 2: Multi-Object Tracker with anonymous Track IDs
│   ├── behavior_analyzer.py       # Phase 2: Spatial, Screen Region & Duration feature analyzer
│   ├── video_processor_phase2.py    # Phase 2: Behavioral HUD visualization & video writer
│   ├── main_phase2.py             # Phase 2: CLI runner (outputs videos/output_tracking.mp4)
│   ├── risk_engine.py             # Phase 3: Explainable Risk Engine & Hysteresis Alerting
│   ├── video_processor_phase3.py    # Phase 3: Risk Score HUD visualization & video writer
│   ├── main_phase3.py             # Phase 3: CLI runner (outputs videos/output_risk.mp4)
│   ├── test_risk_engine.py        # Phase 3: Unit test suite
│   ├── database.py                # Phase 4: SQLite Database Manager (data/cineguard.db)
│   ├── incident_manager.py        # Phase 4: Logged Incident Manager
│   ├── alert_manager.py           # Phase 4: Alert Lifecycle & Deduplication Manager
│   ├── alert_api.py               # Phase 4: FastAPI REST API endpoints
│   ├── main_phase4.py             # Phase 4: Full integration runner
│   ├── test_alert_system.py       # Phase 4: Unit test suite
│   ├── test_api_endpoints.py      # API Endpoint integration tests
│   ├── reset_demo_data.py         # Clean demo baseline database reset utility
│   ├── Dockerfile                 # Backend container definition
│   └── requirements.txt           # Python dependencies
├── frontend/                      # React + TypeScript + Vite Command Dashboard
│   ├── src/                       # Components, Services, and Types
│   ├── .env.example               # Frontend environment template
│   ├── .env.production            # Frontend production environment default
│   ├── vercel.json                # Vercel SPA routing manifest
│   ├── Dockerfile                 # Frontend container definition
│   └── nginx.conf                 # Production Nginx SPA fallback config
├── data/                          # SQLite Database directory
│   └── cineguard.db               # SQLite database file
├── models/                        # Holds YOLO model weights (e.g., yolov8n.pt)
├── videos/                        # Input & output video files
│   ├── demo_output_risk_h264.mp4  # H.264 browser-compatible presentation video
│   └── output_risk.mp4            # Raw risk HUD video
├── docker-compose.yml             # Full-stack container orchestration
├── render.yaml                    # Render 1-click cloud deployment blueprint
├── Procfile                       # Production web process declaration
└── README.md                      # Documentation and deployment quickstart
```

---

## 🌐 Public Cloud Deployment Guide

CineGuard AI is designed for seamless public cloud deployment. The React frontend connects to the FastAPI backend using environment variables (`VITE_API_BASE_URL`).

### Option 1: Render (Recommended 1-Click Blueprint)

1. Push your repository to GitHub / GitLab.
2. In [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Blueprints**.
3. Connect your repository. Render will automatically detect `render.yaml` and configure:
   - **Backend Web Service**: Python FastAPI on `https://cineguard-backend.onrender.com`
   - **Frontend Static Site**: React Vite SPA on `https://cineguard-frontend.onrender.com`
4. Click **Apply**. Once built, open your public frontend URL!

---

### Option 2: Frontend on Vercel + Backend on Render / Railway

#### Step 1: Deploy Backend (Render / Railway / Docker host)
- **Environment Variables**:
  - `PORT`: `8000` (or dynamically supplied by host)
  - `ALLOWED_ORIGINS`: `https://your-app.vercel.app` (or `*` for broad access)
- **Start Command**:
  ```bash
  uvicorn backend.alert_api:app --host 0.0.0.0 --port $PORT
  ```

#### Step 2: Deploy Frontend on Vercel
1. Import `frontend/` project into [Vercel](https://vercel.com).
2. Set Framework Preset: **Vite**.
3. Build Command: `npm run build`.
4. Output Directory: `dist`.
5. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend-service.onrender.com`
6. Deploy!

---

### Option 3: Docker & Docker Compose Container Deployment

Run the complete production-configured stack using Docker:

```bash
# Build and run backend and frontend containers
docker-compose up --build -d
```

- Frontend accessible at `http://localhost:5173` (or server IP)
- Backend API accessible at `http://localhost:8000`

---

## ⚡ Instant Live Public Demo (Public Tunnels)

To instantly share a live presentation link from your local machine:

1. **Start Backend Server**:
   ```bash
   python -m uvicorn backend.alert_api:app --port 8000
   ```
2. **Start Frontend Dev Server**:
   ```bash
   cd frontend && npm run dev
   ```
3. **Expose Ports Publicly**:
   - Using LocalTunnel: `npx localtunnel --port 8000`
   - Using Cloudflare Tunnel: `cloudflared tunnel --url http://localhost:8000`
   - Using SSH (localhost.run / pinggy): `ssh -R 80:localhost:8000 nokey@localhost.run`
4. Update `VITE_API_BASE_URL` in `frontend/.env` with your public backend URL and run `npm run dev` / `npm run build`.

---

## 🧪 Verification & Testing Commands

### Backend Automated Unit Tests (31 Test Cases)
```bash
python -m unittest backend/test_risk_engine.py backend/test_alert_system.py backend/test_api_endpoints.py
```

### Frontend Build Audit
```bash
cd frontend
npm run build
```

---

## 📡 REST API Public Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | API Health status, mode, and verification flags |
| `/api/stats` | `GET` | Operational metrics computed directly from SQLite |
| `/api/alerts` | `GET` | List all alerts (optional `?status=NEW\|UNDER_REVIEW\|CONFIRMED\|DISMISSED`) |
| `/api/alerts/{id}` | `GET` | Retrieve alert evidence details |
| `/api/alerts/{id}/review` | `POST` | Transition alert status: `NEW` $\rightarrow$ `UNDER_REVIEW` |
| `/api/alerts/{id}/confirm` | `POST` | Transition alert status: `UNDER_REVIEW` $\rightarrow$ `CONFIRMED` & create Incident |
| `/api/alerts/{id}/dismiss` | `POST` | Transition alert status: `NEW`/`UNDER_REVIEW` $\rightarrow$ `DISMISSED` |
| `/api/incidents` | `GET` | List all confirmed incident records |
| `/api/video/risk` | `GET` | Stream H.264 video (`demo_output_risk_h264.mp4`) with `Accept-Ranges` |
| `/api/demo/reset` | `POST` | Reset SQLite database to clean presentation baseline |

---

## 🛡️ Privacy & Safety Standards

1. **Human-in-the-Loop Verification**: All alert and incident structures strictly enforce `human_verification_required: true`. Staff confirmation represents workflow verification, **NOT** proof of illegal activity.
2. **Anonymous Track IDs Only**: Tracked objects use temporary anonymous IDs (`Person #4`, `Phone #1`).
3. **Zero Biometrics / Facial Images**: No facial recognition, biometric extraction, or demographic inference is performed or stored.
4. **Explainable Language**: Uses terms like `"Suspected Recording Behavior"` and `"Behavioral Risk"`. Strictly avoids accusatory terms (`"GUILTY"`, `"PIRATE"`, `"CRIMINAL"`).
