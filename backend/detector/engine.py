from ultralytics import YOLO
import numpy as np
from typing import Tuple, List
import time
import logging

logger = logging.getLogger(__name__)


class DetectionEngine:
    def __init__(self, model_path: str = "yolo26m.pt", device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model: YOLO = None
        self.loaded = False
        self._inference_times: List[float] = []
        self._max_times = 100

    async def load_model(self) -> None:
        logger.info(f"Loading model {self.model_path} on {self.device}")
        self.model = YOLO(self.model_path)
        self.model.to(self.device)
        self.loaded = True
        logger.info("Model loaded successfully")

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

        results = self.model.predict(
            frame,
            classes=[0],  # class 0 = person in COCO
            conf=confidence,
            imgsz=imgsz,
            verbose=False
        )

        inference_time = (time.time() - start_time) * 1000
        self._inference_times.append(inference_time)
        if len(self._inference_times) > self._max_times:
            self._inference_times.pop(0)

        result = results[0]
        count = len(result.boxes)
        annotated_frame = result.plot()

        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            detections.append({
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": conf
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
