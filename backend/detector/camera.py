import cv2
import numpy as np
from typing import Optional
import logging
import threading
import time

logger = logging.getLogger(__name__)


class CameraCapture:
    def __init__(self, source: str, room_id: str):
        """
        Initialize camera capture.

        Args:
            source: RTSP URL, webcam index (0, 1, ...), or video file path
        """
        self.source = source
        self.room_id = room_id
        self._cap: Optional[cv2.VideoCapture] = None
        self._connected = False
        self._last_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5

    def connect(self) -> bool:
        try:
            # Try to parse as int for webcam index
            if self.source.isdigit():
                source = int(self.source)
            else:
                source = self.source

            self._cap = cv2.VideoCapture(source)

            if isinstance(source, str) and source.startswith("rtsp://"):
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if self._cap.isOpened():
                self._connected = True
                self._reconnect_attempts = 0
                logger.info(f"Camera {self.room_id} connected: {self.source}")
                return True
            else:
                logger.error(f"Failed to open camera {self.room_id}: {self.source}")
                return False
        except Exception as e:
            logger.error(f"Camera {self.room_id} connection error: {e}")
            return False

    def grab_frame(self) -> Optional[np.ndarray]:
        if not self._connected or self._cap is None:
            return None

        with self._lock:
            ret, frame = self._cap.read()

            if not ret:
                self._handle_disconnect()
                return self._last_frame

            self._last_frame = frame
            return frame

    def _handle_disconnect(self) -> None:
        self._connected = False
        self._reconnect_attempts += 1

        if self._reconnect_attempts <= self._max_reconnect_attempts:
            logger.warning(
                f"Camera {self.room_id} disconnected, "
                f"attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}"
            )
            time.sleep(2)
            self.connect()
        else:
            logger.error(f"Camera {self.room_id} max reconnect attempts reached")

    def disconnect(self) -> None:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._connected = False
            logger.info(f"Camera {self.room_id} disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def last_frame(self) -> Optional[np.ndarray]:
        return self._last_frame
