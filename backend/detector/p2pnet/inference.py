"""P2PNet inference wrapper for crowd counting."""
import torch
import torchvision.transforms as transforms
import numpy as np
import cv2
from PIL import Image
from typing import Tuple, List
import time
import logging
import sys
import os

# Optimize PyTorch for CPU inference
num_threads = os.cpu_count() or 4
torch.set_num_threads(num_threads)
torch.set_num_interop_threads(num_threads)

# Add p2pnet modules to path
sys.path.insert(0, os.path.dirname(__file__))

from .models import build_model

logger = logging.getLogger(__name__)


class Args:
    """Arguments for P2PNet model building."""
    def __init__(self):
        self.backbone = 'vgg16_bn'
        self.row = 2
        self.line = 2


class P2PNetEngine:
    """P2PNet model wrapper for inference."""

    def __init__(self, weight_path: str = "models/p2pnet.pth", device: str = "cpu"):
        self.weight_path = weight_path
        self.device = device
        self.model = None
        self.loaded = False
        self._inference_times: List[float] = []
        self._max_times = 100

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def load_model(self) -> None:
        """Load P2PNet model (synchronous)."""
        logger.info(f"Loading P2PNet model from {self.weight_path} on {self.device}")
        logger.info(f"[P2PNet] Using {num_threads} CPU threads for inference")

        args = Args()
        self.model = build_model(args, training=False)

        # Load checkpoint
        checkpoint = torch.load(self.weight_path, map_location='cpu', weights_only=False)
        self.model.load_state_dict(checkpoint['model'])

        self.model.to(self.device)
        self.model.eval()

        # Note: torch.compile requires C++ compiler (g++) which may not be in Docker
        # Using standard eager mode for compatibility
        logger.info("[P2PNet] Using eager mode (torch.compile disabled for Docker compatibility)")

        self.loaded = True
        logger.info("P2PNet model loaded successfully (point-based crowd counting)")

    def detect(
        self,
        frame: np.ndarray,
        confidence: float = 0.5,
        imgsz: int = 1280  # Not used for P2PNet, kept for API compatibility
    ) -> Tuple[int, np.ndarray, List[dict]]:
        """
        Detect people in frame using P2PNet.

        Returns:
            count: number of detected people
            annotated_frame: frame with point markers
            detections: list of detection dicts with center coords
        """
        if not self.loaded or self.model is None:
            logger.error("[P2PNet] Model not loaded!")
            raise RuntimeError("P2PNet model not loaded")

        start_time = time.time()
        logger.info(f"[P2PNet] Starting detection on frame {frame.shape[1]}x{frame.shape[0]}")

        # Convert BGR to RGB
        logger.debug("[P2PNet] Converting BGR to RGB...")
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        # Store original dimensions for scaling back
        orig_width, orig_height = img_pil.size

        # Limit max size for CPU performance (P2PNet is memory-intensive)
        width, height = orig_width, orig_height
        max_size = imgsz  # Use imgsz parameter as max dimension
        if width > max_size or height > max_size:
            scale = max_size / max(width, height)
            width = int(width * scale)
            height = int(height * scale)
            img_pil = img_pil.resize((width, height), Image.LANCZOS)
            logger.info(f"[P2PNet] Downscaled large image to {width}x{height} (max: {max_size})")

        # Resize to multiple of 128 (P2PNet requirement)
        new_width = (width // 128) * 128
        new_height = (height // 128) * 128

        if new_width == 0:
            new_width = 128
        if new_height == 0:
            new_height = 128

        logger.info(f"[P2PNet] Final size: {new_width}x{new_height} (aligned to 128)")
        img_resized = img_pil.resize((new_width, new_height), Image.LANCZOS)

        # Scale factors for mapping back to ORIGINAL size
        scale_x = orig_width / new_width
        scale_y = orig_height / new_height

        # Preprocess
        logger.debug("[P2PNet] Preprocessing image tensor...")
        img_tensor = self.transform(img_resized)
        samples = img_tensor.unsqueeze(0).to(self.device)

        # Inference
        logger.info(f"[P2PNet] Running inference on {self.device}...")
        inference_start = time.time()
        with torch.no_grad():
            outputs = self.model(samples)
        inference_only = (time.time() - inference_start) * 1000
        logger.info(f"[P2PNet] Model inference complete in {inference_only:.1f}ms")

        # Get predictions
        logger.debug("[P2PNet] Processing model outputs...")
        outputs_scores = torch.nn.functional.softmax(outputs['pred_logits'], -1)[:, :, 1][0]
        outputs_points = outputs['pred_points'][0]

        # Filter by confidence threshold
        mask = outputs_scores > confidence
        points = outputs_points[mask].detach().cpu().numpy()
        scores = outputs_scores[mask].detach().cpu().numpy()

        inference_time = (time.time() - start_time) * 1000
        self._inference_times.append(inference_time)
        if len(self._inference_times) > self._max_times:
            self._inference_times.pop(0)

        count = len(points)
        logger.info(f"[P2PNet] Found {count} points with confidence > {confidence}")

        # Draw circles on original frame
        annotated_frame = frame.copy()
        detections = []

        for i, (point, score) in enumerate(zip(points, scores)):
            # Scale point back to original image size
            cx = int(point[0] * scale_x)
            cy = int(point[1] * scale_y)

            # Clamp to original image bounds
            cx = max(0, min(cx, orig_width - 1))
            cy = max(0, min(cy, orig_height - 1))

            # Draw filled circle with outline
            radius = 8
            cv2.circle(annotated_frame, (cx, cy), radius, (0, 255, 0), -1)  # Green fill
            cv2.circle(annotated_frame, (cx, cy), radius, (0, 0, 0), 2)  # Black outline

            detections.append({
                "bbox": [float(cx - 10), float(cy - 10), float(cx + 10), float(cy + 10)],  # Fake bbox for API compat
                "confidence": float(score),
                "center": [cx, cy]
            })

        return count, annotated_frame, detections

    @property
    def avg_inference_ms(self) -> float:
        if not self._inference_times:
            return 0.0
        return sum(self._inference_times) / len(self._inference_times)

    def reload_model(self, weight_path: str) -> None:
        """Reload model with new weights."""
        self.weight_path = weight_path

        args = Args()
        self.model = build_model(args, training=False)

        checkpoint = torch.load(weight_path, map_location='cpu', weights_only=False)
        self.model.load_state_dict(checkpoint['model'])

        self.model.to(self.device)
        self.model.eval()

        # Note: torch.compile disabled for Docker compatibility (requires g++)
        logger.info("[P2PNet] Using eager mode")

        self._inference_times.clear()
        logger.info(f"P2PNet model reloaded: {weight_path}")
