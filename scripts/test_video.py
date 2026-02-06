#!/usr/bin/env python3
"""
Test YOLO detection on a video file.
Usage: python test_video.py --video video.mp4
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import cv2
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Test YOLO detection on video")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--model", default="yolo11n.pt", help="YOLO model path")
    parser.add_argument("--confidence", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--output", default=None, help="Output video path (optional)")
    parser.add_argument("--skip", type=int, default=1, help="Process every N frames")
    args = parser.parse_args()

    if not Path(args.video).exists():
        print(f"Error: Video not found: {args.video}")
        sys.exit(1)

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    print(f"Processing video: {args.video}")
    cap = cv2.VideoCapture(args.video)

    if not cap.isOpened():
        print(f"Error: Could not open video: {args.video}")
        sys.exit(1)

    # Video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames")

    # Output video writer
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, fps / args.skip, (width, height))

    frame_count = 0
    inference_times = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % args.skip != 0:
                continue

            start_time = time.time()
            results = model.predict(
                frame,
                classes=[0],
                conf=args.confidence,
                verbose=False
            )
            inference_time = (time.time() - start_time) * 1000
            inference_times.append(inference_time)

            result = results[0]
            count = len(result.boxes)
            annotated = result.plot()

            # Add count overlay
            cv2.putText(
                annotated,
                f"People: {count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            if writer:
                writer.write(annotated)

            # Show progress
            progress = frame_count / total_frames * 100
            avg_time = sum(inference_times[-10:]) / min(len(inference_times), 10)
            print(f"\rProgress: {progress:.1f}% | Frame: {frame_count}/{total_frames} | "
                  f"People: {count} | Inference: {avg_time:.1f}ms", end="")

            # Try to display
            try:
                cv2.imshow("Detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception:
                pass

    finally:
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

    # Statistics
    print(f"\n\n{'='*40}")
    print(f"Processed frames: {len(inference_times)}")
    print(f"Avg inference time: {sum(inference_times)/len(inference_times):.1f}ms")
    print(f"Min inference time: {min(inference_times):.1f}ms")
    print(f"Max inference time: {max(inference_times):.1f}ms")
    if args.output:
        print(f"Output saved to: {args.output}")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()
