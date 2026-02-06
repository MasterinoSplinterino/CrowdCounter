import base64
import cv2
import numpy as np
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["test"])

# Global reference to detection manager (set from main.py)
_detection_manager = None


def set_detection_manager(manager):
    global _detection_manager
    _detection_manager = manager


class Detection(BaseModel):
    bbox: List[float]
    confidence: float
    center: Optional[List[int]] = None


class TestResult(BaseModel):
    count: int
    detections: List[Detection]
    image_base64: str
    inference_ms: float


@router.post("/test/image", response_model=TestResult)
async def test_image(file: UploadFile = File(...)):
    """
    Test detection on uploaded image.
    Returns count, bounding boxes, and annotated image.
    File is not saved - processed in memory only.
    """
    if _detection_manager is None or not _detection_manager.model_loaded:
        raise HTTPException(status_code=503, detail="Detection engine not ready")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read file into memory
    contents = await file.read()

    # Decode image
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    # Run detection
    settings = _detection_manager.settings
    count, annotated, detections = _detection_manager.engine.detect(
        frame,
        confidence=settings["confidence_threshold"],
        imgsz=settings["imgsz"]
    )

    # Encode annotated frame to base64
    _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    image_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

    return TestResult(
        count=count,
        detections=[Detection(**d) for d in detections],
        image_base64=image_base64,
        inference_ms=_detection_manager.avg_inference_ms
    )


@router.post("/test/video", response_model=List[TestResult])
async def test_video(file: UploadFile = File(...), max_frames: int = 10):
    """
    Test detection on uploaded video.
    Processes up to max_frames frames evenly distributed through the video.
    File is saved temporarily, processed, then deleted.
    """
    if _detection_manager is None or not _detection_manager.model_loaded:
        raise HTTPException(status_code=503, detail="Detection engine not ready")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    # Save to temp file (required for cv2.VideoCapture)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_path = temp_file.name
            contents = await file.read()
            temp_file.write(contents)

        # Open video
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            raise HTTPException(status_code=400, detail="Video has no frames")

        # Calculate which frames to process
        frames_to_process = min(max_frames, total_frames)
        frame_indices = [int(i * total_frames / frames_to_process) for i in range(frames_to_process)]

        results = []
        settings = _detection_manager.settings

        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret:
                continue

            # Run detection
            count, annotated, detections = _detection_manager.engine.detect(
                frame,
                confidence=settings["confidence_threshold"],
                imgsz=settings["imgsz"]
            )

            # Encode annotated frame to base64
            _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

            results.append(TestResult(
                count=count,
                detections=[Detection(**d) for d in detections],
                image_base64=image_base64,
                inference_ms=_detection_manager.avg_inference_ms
            ))

        cap.release()
        return results

    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
