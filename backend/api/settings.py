from fastapi import APIRouter, Depends
from typing import List
import aiosqlite

from db.database import get_db
from db.models import Settings, SettingsUpdate, SystemStatus

router = APIRouter(prefix="/api", tags=["settings"])

# Available models with descriptions
AVAILABLE_MODELS = [
    {
        "id": "yolo26m.pt",
        "name": "YOLO26m (Person Detection)",
        "description": "General person detection, good for normal scenes",
        "type": "person",
    },
    {
        "id": "models/yolov8-crowdhuman.pt",
        "name": "YOLOv8 CrowdHuman (Head Detection)",
        "description": "Best for dense crowds, trained on CrowdHuman dataset",
        "type": "head",
    },
    {
        "id": "models/yolov8-head-medium.pt",
        "name": "YOLOv8 SCUT-HEAD Medium",
        "description": "Head detection, balanced accuracy/speed",
        "type": "head",
    },
    {
        "id": "models/yolov8-head-nano.pt",
        "name": "YOLOv8 SCUT-HEAD Nano",
        "description": "Fast head detection, lower accuracy",
        "type": "head",
    },
]

# Reference to detection manager (set from main.py)
_detection_manager = None


def set_detection_manager(manager):
    global _detection_manager
    _detection_manager = manager


@router.get("/models")
async def get_available_models() -> List[dict]:
    """Get list of available detection models."""
    return AVAILABLE_MODELS


@router.get("/settings", response_model=Settings)
async def get_settings(db: aiosqlite.Connection = Depends(get_db)):
    """Get current detection settings."""
    cursor = await db.execute("SELECT key, value FROM settings")
    rows = await cursor.fetchall()

    settings_dict = {row["key"]: row["value"] for row in rows}

    return Settings(
        model=settings_dict.get("model", "yolo26m.pt"),
        confidence_threshold=float(settings_dict.get("confidence_threshold", 0.20)),
        detection_interval=int(settings_dict.get("detection_interval", 15)),
        smoothing_alpha=float(settings_dict.get("smoothing_alpha", 0.3)),
        imgsz=int(settings_dict.get("imgsz", 1280)),
    )


@router.put("/settings", response_model=Settings)
async def update_settings(
    settings: SettingsUpdate,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Update detection settings."""
    update_dict = {}

    if settings.model is not None:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("model", settings.model)
        )
        update_dict["model"] = settings.model

    if settings.confidence_threshold is not None:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("confidence_threshold", str(settings.confidence_threshold))
        )
        update_dict["confidence_threshold"] = settings.confidence_threshold

    if settings.detection_interval is not None:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("detection_interval", str(settings.detection_interval))
        )
        update_dict["detection_interval"] = settings.detection_interval

    if settings.smoothing_alpha is not None:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("smoothing_alpha", str(settings.smoothing_alpha))
        )
        update_dict["smoothing_alpha"] = settings.smoothing_alpha

    if settings.imgsz is not None:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("imgsz", str(settings.imgsz))
        )
        update_dict["imgsz"] = settings.imgsz

    await db.commit()

    # Update detection manager settings
    if _detection_manager and update_dict:
        await _detection_manager.update_settings(update_dict)

    return await get_settings(db)


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status."""
    if not _detection_manager:
        return SystemStatus(
            device="cpu",
            model="not loaded",
            model_loaded=False,
            cameras_connected=0,
            cameras_total=0,
            uptime_seconds=0,
            avg_inference_ms=0,
        )

    return SystemStatus(
        device=_detection_manager.engine.device,
        model=_detection_manager.settings["model"],
        model_loaded=_detection_manager.model_loaded,
        cameras_connected=_detection_manager.connected_cameras,
        cameras_total=_detection_manager.total_cameras,
        uptime_seconds=_detection_manager.uptime_seconds,
        avg_inference_ms=round(_detection_manager.avg_inference_ms, 2),
    )
