import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

project_root = current_dir.parent

from fastapi import FastAPI, HTTPException, Query, Path as APIPath
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import DatabaseManager
from alert_manager import AlertManager

app = FastAPI(
    title="CineGuard AI - Real-Time Alert & Incident API",
    description="Human-in-the-loop security assistance API for reviewing suspected recording behavior alerts and confirmed incidents.",
    version="1.0.0",
)

# Enable CORS for React frontend (supports env variable ALLOWED_ORIGINS)
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
if raw_origins.strip() == "*":
    allowed_origins = ["*"]
    allow_credentials = False
else:
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared database & alert manager instances
data_dir = project_root / "data"
data_dir.mkdir(parents=True, exist_ok=True)
db_path = data_dir / "cineguard.db"
db_instance = DatabaseManager(db_path=str(db_path))
alert_manager_instance = AlertManager(db=db_instance)


class ReviewRequest(BaseModel):
    reviewer_action: Optional[str] = "action"


from reset_demo_data import reset_demo_database


@app.get("/api/health")
def get_health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "CineGuard AI Real-Time Alert API",
        "human_verification_required": True,
        "mode": "DEMO MODE",
    }


@app.post("/api/demo/reset")
def reset_demo():
    """Reset prototype demo database and re-seed clean demonstration alert."""
    reset_demo_database(force=True)
    alert_manager_instance.reset_cache()
    demo_alert = {
        "alert_id": "ALERT-CAM-01-D4F8232D",
        "camera_id": "CAM-01",
        "timestamp_seconds": 12.0,
        "person_track_id": 4,
        "phone_track_id": 1,
        "risk_score": 85,
        "classification": "SUSPECTED_RECORDING",
        "reasons": [
            "Mobile device detected",
            "Device associated with tracked Person #4",
            "Device located within configured screen region",
            "Behavior persisted for 5.2 seconds",
            "Device movement directed toward screen region"
        ],
        "human_verification_required": True,
    }
    alert_manager_instance.create_alert(demo_alert)
    return {
        "status": "ok",
        "message": "Demo database reset to clean baseline state.",
        "active_alerts": 1,
        "confirmed_incidents": 0
    }


@app.get("/api/video/risk")
def get_risk_video():
    """Safely stream the demonstration risk video (videos/demo_output_risk_h264.mp4)."""
    video_path = project_root / "videos" / "demo_output_risk_h264.mp4"
    if not video_path.exists():
        video_path = project_root / "videos" / "demo_output_risk.mp4"
    if not video_path.exists():
        video_path = project_root / "videos" / "output_risk.mp4"
    if not video_path.exists():
        video_path = project_root / "videos" / "output_detection.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Demonstration output video file not found.")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )


@app.get("/api/alerts")
def list_alerts(status: Optional[str] = Query(None, description="Filter by status: NEW, UNDER_REVIEW, CONFIRMED, DISMISSED")):
    """List all alert events from database."""
    return alert_manager_instance.list_alerts(status_filter=status)


@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: str = APIPath(..., description="Unique alert ID")):
    """Get alert details by alert_id."""
    alert = alert_manager_instance.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return alert


@app.post("/api/alerts/{alert_id}/review")
def start_review(alert_id: str, body: Optional[ReviewRequest] = None):
    """Transition alert status from NEW -> UNDER_REVIEW."""
    action = body.reviewer_action if body and body.reviewer_action else "review"
    try:
        updated_alert = alert_manager_instance.start_review(alert_id, reviewer_action=action)
        return updated_alert
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/alerts/{alert_id}/confirm")
def confirm_alert(alert_id: str, body: Optional[ReviewRequest] = None):
    """Transition alert status from UNDER_REVIEW -> CONFIRMED and generate Incident Record."""
    action = body.reviewer_action if body and body.reviewer_action else "confirmed"
    try:
        confirmed_alert = alert_manager_instance.confirm_alert(alert_id, reviewer_action=action)
        return confirmed_alert
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/alerts/{alert_id}/dismiss")
def dismiss_alert(alert_id: str, body: Optional[ReviewRequest] = None):
    """Transition alert status from NEW/UNDER_REVIEW -> DISMISSED."""
    action = body.reviewer_action if body and body.reviewer_action else "dismissed"
    try:
        dismissed_alert = alert_manager_instance.dismiss_alert(alert_id, reviewer_action=action)
        return dismissed_alert
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/incidents")
def list_incidents():
    """List all confirmed incident records."""
    return alert_manager_instance.incident_manager.list_incidents()


@app.get("/api/stats")
def get_operational_stats():
    """Get operational metrics calculated directly from SQLite database records."""
    return alert_manager_instance.get_operational_stats()
