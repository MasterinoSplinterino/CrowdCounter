from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class OccupancyStatus(str, Enum):
    EMPTY = "empty"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


class RoomBase(BaseModel):
    name: str
    capacity: int
    camera_url: str
    is_active: bool = True


class RoomCreate(RoomBase):
    id: str


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    camera_url: Optional[str] = None
    is_active: Optional[bool] = None


class Room(RoomBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class RoomWithCount(Room):
    count: int = 0
    raw_count: int = 0
    occupancy_percent: float = 0.0
    status: OccupancyStatus = OccupancyStatus.EMPTY
    last_updated: Optional[datetime] = None


class Count(BaseModel):
    id: int
    room_id: str
    count: int
    raw_count: int
    occupancy: float
    timestamp: datetime

    class Config:
        from_attributes = True


class CountCreate(BaseModel):
    room_id: str
    count: int
    raw_count: int
    occupancy: float


class Settings(BaseModel):
    model: str = "yolo11n.pt"
    confidence_threshold: float = 0.35
    detection_interval: int = 15
    smoothing_alpha: float = 0.3
    imgsz: int = 640


class SettingsUpdate(BaseModel):
    model: Optional[str] = None
    confidence_threshold: Optional[float] = None
    detection_interval: Optional[int] = None
    smoothing_alpha: Optional[float] = None
    imgsz: Optional[int] = None


class SystemStatus(BaseModel):
    device: str
    model: str
    model_loaded: bool
    cameras_connected: int
    cameras_total: int
    uptime_seconds: float
    avg_inference_ms: float


class PreviewFrame(BaseModel):
    room_id: str
    frame: str  # base64
    detections: int
    timestamp: datetime


def get_occupancy_status(percent: float) -> OccupancyStatus:
    if percent == 0:
        return OccupancyStatus.EMPTY
    elif percent < 40:
        return OccupancyStatus.LOW
    elif percent < 70:
        return OccupancyStatus.MEDIUM
    elif percent < 90:
        return OccupancyStatus.HIGH
    else:
        return OccupancyStatus.FULL
