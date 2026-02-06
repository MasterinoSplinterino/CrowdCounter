#!/usr/bin/env python3
"""
Test YOLO detection with webcam.
Usage: python test_webcam.py
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import cv2
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Test YOLO detection with webcam")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    parser.add_argument("--model", default="yolo11n.pt", help="YOLO model path")
    parser.add_argument("--confidence", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--interval", type=float, default=0.5, help="Detection interval (seconds)")
    args = parser.parse_args()

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    print(f"Opening camera: {args.camera}")
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print(f"Error: Could not open camera: {args.camera}")
        sys.exit(1)

    print("\nControls:")
    print("  q - quit")
    print("  + - increase confidence")
    print("  - - decrease confidence")
    print(f"\nStarting detection (interval: {args.interval}s)...\n")

    last_detection = 0
    last_count = 0
    last_annotated = None
    confidence = args.confidence
    inference_times = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame")
                break

            current_time = time.time()

            # Run detection at interval
            if current_time - last_detection >= args.interval:
                start_time = time.time()
                results = model.predict(
                    frame,
                    classes=[0],
                    conf=confidence,
                    verbose=False
                )
                inference_time = (time.time() - start_time) * 1000
                inference_times.append(inference_time)
                if len(inference_times) > 100:
                    inference_times.pop(0)

                result = results[0]
                last_count = len(result.boxes)
                last_annotated = result.plot()
                last_detection = current_time

            # Display
            display = last_annotated if last_annotated is not None else frame

            # Add overlay
            cv2.putText(
                display,
                f"People: {last_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                display,
                f"Conf: {confidence:.2f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1
            )
            if inference_times:
                avg_time = sum(inference_times) / len(inference_times)
                cv2.putText(
                    display,
                    f"Avg: {avg_time:.0f}ms",
                    (10, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )

            cv2.imshow("Webcam Detection", display)

            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('+') or key == ord('='):
                confidence = min(0.95, confidence + 0.05)
                print(f"Confidence: {confidence:.2f}")
            elif key == ord('-'):
                confidence = max(0.05, confidence - 0.05)
                print(f"Confidence: {confidence:.2f}")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    # Statistics
    if inference_times:
        print(f"\n{'='*40}")
        print(f"Total detections: {len(inference_times)}")
        print(f"Avg inference time: {sum(inference_times)/len(inference_times):.1f}ms")
        print(f"{'='*40}")


if __name__ == "__main__":
    main()
