import asyncio
import base64
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Callable, Awaitable
import logging

from .engine import DetectionEngine
from .camera import CameraCapture
from .counter import PeopleCounter

logger = logging.getLogger(__name__)


class RoomProcessor:
    def __init__(
        self,
        room_id: str,
        camera_url: str,
        capacity: int,
        engine: DetectionEngine,
        on_count_update: Callable,
    ):
        self.room_id = room_id
        self.capacity = capacity
        self.camera = CameraCapture(camera_url, room_id)
        self.counter = PeopleCounter(room_id)
        self.engine = engine
        self.on_count_update = on_count_update

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_frame: Optional[str] = None  # base64
        self._last_detections: int = 0
        self._last_timestamp: Optional[datetime] = None

    async def start(self, interval: int, confidence: float, imgsz: int, alpha: float):
        if self._running:
            return

        self.counter.set_alpha(alpha)

        if not self.camera.connect():
            logger.error(f"Failed to start room {self.room_id}: camera not connected")
            return

        self._running = True
        self._task = asyncio.create_task(
            self._process_loop(interval, confidence, imgsz)
        )
        logger.info(f"Room {self.room_id} processing started")

    async def _process_loop(self, interval: int, confidence: float, imgsz: int):
        while self._running:
            try:
                frame = self.camera.grab_frame()

                if frame is not None:
                    raw_count, annotated, _ = self.engine.detect(
                        frame, confidence, imgsz
                    )

                    smoothed_count = self.counter.update(raw_count)
                    occupancy = (smoothed_count / self.capacity * 100) if self.capacity > 0 else 0

                    # Encode frame to base64
                    _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    self._last_frame = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
                    self._last_detections = raw_count
                    self._last_timestamp = datetime.utcnow()

                    # Callback to save count and broadcast
                    await self.on_count_update(
                        room_id=self.room_id,
                        count=smoothed_count,
                        raw_count=raw_count,
                        occupancy=occupancy,
                        frame_base64=self._last_frame
                    )

            except Exception as e:
                logger.error(f"Room {self.room_id} processing error: {e}")

            await asyncio.sleep(interval)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.camera.disconnect()
        logger.info(f"Room {self.room_id} processing stopped")

    def update_settings(self, alpha: float):
        self.counter.set_alpha(alpha)

    @property
    def last_frame(self) -> Optional[str]:
        return self._last_frame

    @property
    def is_running(self) -> bool:
        return self._running


class DetectionManager:
    def __init__(self, device: str = "cpu"):
        self.engine = DetectionEngine(device=device)
        self._rooms: Dict[str, RoomProcessor] = {}
        self._settings = {
            "model": "yolo11n.pt",
            "confidence_threshold": 0.35,
            "detection_interval": 15,
            "smoothing_alpha": 0.3,
            "imgsz": 640,
        }
        self._on_count_update: Optional[Callable] = None
        self._started = False
        self._start_time: Optional[datetime] = None

    async def initialize(self, model_path: str = "yolo11n.pt"):
        self._settings["model"] = model_path
        self.engine.model_path = model_path
        await self.engine.load_model()
        self._start_time = datetime.utcnow()
        self._started = True

    def set_count_callback(self, callback: Callable):
        self._on_count_update = callback

    async def add_room(
        self,
        room_id: str,
        camera_url: str,
        capacity: int,
        is_active: bool = True
    ):
        if room_id in self._rooms:
            await self.remove_room(room_id)

        processor = RoomProcessor(
            room_id=room_id,
            camera_url=camera_url,
            capacity=capacity,
            engine=self.engine,
            on_count_update=self._on_count_update,
        )

        self._rooms[room_id] = processor

        if is_active:
            await processor.start(
                interval=self._settings["detection_interval"],
                confidence=self._settings["confidence_threshold"],
                imgsz=self._settings["imgsz"],
                alpha=self._settings["smoothing_alpha"],
            )

    async def remove_room(self, room_id: str):
        if room_id in self._rooms:
            await self._rooms[room_id].stop()
            del self._rooms[room_id]

    async def update_settings(self, settings: dict):
        reload_model = False

        if "model" in settings and settings["model"] != self._settings["model"]:
            self._settings["model"] = settings["model"]
            reload_model = True

        for key in ["confidence_threshold", "detection_interval", "smoothing_alpha", "imgsz"]:
            if key in settings:
                self._settings[key] = settings[key]

        if reload_model:
            self.engine.reload_model(self._settings["model"])

        # Update smoothing for all rooms
        for processor in self._rooms.values():
            processor.update_settings(self._settings["smoothing_alpha"])

    def get_preview(self, room_id: str) -> Optional[str]:
        if room_id in self._rooms:
            return self._rooms[room_id].last_frame
        return None

    @property
    def settings(self) -> dict:
        return self._settings.copy()

    @property
    def connected_cameras(self) -> int:
        return sum(1 for r in self._rooms.values() if r.camera.is_connected)

    @property
    def total_cameras(self) -> int:
        return len(self._rooms)

    @property
    def uptime_seconds(self) -> float:
        if self._start_time:
            return (datetime.utcnow() - self._start_time).total_seconds()
        return 0.0

    @property
    def avg_inference_ms(self) -> float:
        return self.engine.avg_inference_ms

    @property
    def model_loaded(self) -> bool:
        return self.engine.loaded

    async def shutdown(self):
        for room_id in list(self._rooms.keys()):
            await self.remove_room(room_id)
        logger.info("Detection manager shutdown complete")
