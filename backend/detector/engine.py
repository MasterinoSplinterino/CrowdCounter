from ultralytics import YOLO
import cv2
import numpy as np
from typing import Tuple, List
import time
import logging

logger = logging.getLogger(__name__)

# Models that are trained specifically for head detection (no class filter needed)
HEAD_DETECTION_MODELS = [
    "yolov8-head-medium.pt",
    "yolov8-head-nano.pt",
    "yolov8-crowdhuman.pt",
    "models/yolov8-head-medium.pt",
    "models/yolov8-head-nano.pt",
    "models/yolov8-crowdhuman.pt",
]


class DetectionEngine:
    def __init__(self, model_path: str = "yolo26m.pt", device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model: YOLO = None
        self.loaded = False
        self._inference_times: List[float] = []
        self._max_times = 100

    def _is_head_model(self) -> bool:
        """Check if current model is a head detection model."""
        return any(name in self.model_path for name in HEAD_DETECTION_MODELS)

    async def load_model(self) -> None:
        logger.info(f"Loading model {self.model_path} on {self.device}")
        self.model = YOLO(self.model_path)
        self.model.to(self.device)
        self.loaded = True
        model_type = "head detection" if self._is_head_model() else "person detection"
        logger.info(f"Model loaded successfully ({model_type})")

    def detect(
        self,
        frame: np.ndarray,
        confidence: float = 0.35,
        imgsz: int = 640
    ) -> Tuple[int, np.ndarray, List[dict]]:
        """
        Detect people in frame.

        Returns:
            count: number of detected people
            annotated_frame: frame with bounding boxes
            detections: list of detection dicts with bbox coords
        """
        if not self.loaded or self.model is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Head detection models detect only heads, no class filter needed
        # COCO-based models need class=0 (person) filter
        predict_kwargs = {
            "conf": confidence,
            "imgsz": imgsz,
            "verbose": False,
        }
        if not self._is_head_model():
            predict_kwargs["classes"] = [0]  # class 0 = person in COCO

        results = self.model.predict(frame, **predict_kwargs)

        inference_time = (time.time() - start_time) * 1000
        self._inference_times.append(inference_time)
        if len(self._inference_times) > self._max_times:
            self._inference_times.pop(0)

        result = results[0]
        count = len(result.boxes)

        # Draw circles at center of each detection instead of boxes
        annotated_frame = frame.copy()
        detections = []

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())

            # Calculate center point
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Draw filled circle with outline
            radius = 8
            cv2.circle(annotated_frame, (cx, cy), radius, (0, 255, 0), -1)  # Green fill
            cv2.circle(annotated_frame, (cx, cy), radius, (0, 0, 0), 2)  # Black outline

            detections.append({
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": conf,
                "center": [cx, cy]
            })

        return count, annotated_frame, detections

    @property
    def avg_inference_ms(self) -> float:
        if not self._inference_times:
            return 0.0
        return sum(self._inference_times) / len(self._inference_times)

    def reload_model(self, model_path: str) -> None:
        self.model_path = model_path
        self.model = YOLO(model_path)
        self.model.to(self.device)
        self._inference_times.clear()
        logger.info(f"Model reloaded: {model_path}")
