#!/usr/bin/env python3
"""
Test YOLO detection on a single image.
Usage: python test_photo.py --image photo.jpg
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import cv2
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Test YOLO detection on image")
    parser.add_argument("--image", required=True, help="Path to image file")
    parser.add_argument("--model", default="yolo11n.pt", help="YOLO model path")
    parser.add_argument("--confidence", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--output", default=None, help="Output image path (optional)")
    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"Error: Image not found: {args.image}")
        sys.exit(1)

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    print(f"Processing image: {args.image}")
    frame = cv2.imread(args.image)

    if frame is None:
        print(f"Error: Could not read image: {args.image}")
        sys.exit(1)

    results = model.predict(
        frame,
        classes=[0],  # person class
        conf=args.confidence,
        verbose=False
    )

    result = results[0]
    count = len(result.boxes)
    annotated = result.plot()

    print(f"\n{'='*40}")
    print(f"Detected people: {count}")
    print(f"Confidence threshold: {args.confidence}")
    print(f"{'='*40}\n")

    # Show or save result
    output_path = args.output or f"result_{Path(args.image).name}"
    cv2.imwrite(output_path, annotated)
    print(f"Result saved to: {output_path}")

    # Try to display
    try:
        cv2.imshow("Detection Result", annotated)
        print("Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception:
        print("(GUI not available, result saved to file)")


if __name__ == "__main__":
    main()
