from fastapi import APIRouter, HTTPException
from datetime import datetime

from db.models import PreviewFrame

router = APIRouter(prefix="/api/rooms", tags=["preview"])

# Reference to detection manager (set from main.py)
_detection_manager = None


def set_detection_manager(manager):
    global _detection_manager
    _detection_manager = manager


@router.get("/{room_id}/preview", response_model=PreviewFrame)
async def get_preview(room_id: str):
    """Get latest frame with bounding boxes for a room."""
    if not _detection_manager:
        raise HTTPException(status_code=503, detail="Detection service not available")

    frame = _detection_manager.get_preview(room_id)

    if frame is None:
        raise HTTPException(status_code=404, detail="No preview available for this room")

    return PreviewFrame(
        room_id=room_id,
        frame=frame,
        detections=0,  # Will be updated by processor
        timestamp=datetime.utcnow(),
    )
