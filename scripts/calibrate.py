#!/usr/bin/env python3
"""
Calibration tool for finding optimal detection parameters.
Usage: python calibrate.py --source rtsp://... --known-count 50
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import cv2
from ultralytics import YOLO
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Calibrate detection parameters")
    parser.add_argument("--source", required=True, help="Video source (RTSP URL, file, or camera index)")
    parser.add_argument("--known-count", type=int, help="Known number of people in scene")
    parser.add_argument("--model", default="yolo11n.pt", help="YOLO model path")
    parser.add_argument("--samples", type=int, default=10, help="Number of samples to average")
    args = parser.parse_args()

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    # Parse source
    try:
        source = int(args.source)
    except ValueError:
        source = args.source

    print(f"Opening source: {source}")
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"Error: Could not open source: {source}")
        sys.exit(1)

    # Test different confidence levels
    confidence_levels = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    results_table = []

    print(f"\nRunning calibration with {args.samples} samples per confidence level...")
    print("Press Ctrl+C to stop early\n")

    try:
        for conf in confidence_levels:
            counts = []
            inference_times = []

            for i in range(args.samples):
                ret, frame = cap.read()
                if not ret:
                    # Restart video if needed
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        break

                start_time = time.time()
                result = model.predict(
                    frame,
                    classes=[0],
                    conf=conf,
                    verbose=False
                )[0]
                inference_time = (time.time() - start_time) * 1000

                count = len(result.boxes)
                counts.append(count)
                inference_times.append(inference_time)

                time.sleep(0.1)  # Small delay between samples

            if counts:
                avg_count = np.mean(counts)
                std_count = np.std(counts)
                avg_time = np.mean(inference_times)

                error = None
                if args.known_count:
                    error = abs(avg_count - args.known_count) / args.known_count * 100

                results_table.append({
                    'conf': conf,
                    'avg_count': avg_count,
                    'std': std_count,
                    'time_ms': avg_time,
                    'error': error
                })

                print(f"Confidence {conf:.2f}: avg={avg_count:.1f} (±{std_count:.1f}), "
                      f"time={avg_time:.0f}ms" +
                      (f", error={error:.1f}%" if error else ""))

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        cap.release()

    # Print summary
    print(f"\n{'='*60}")
    print("CALIBRATION RESULTS")
    print(f"{'='*60}")
    print(f"{'Conf':<8} {'Avg Count':<12} {'Std Dev':<10} {'Time (ms)':<10}", end="")
    if args.known_count:
        print(f"{'Error %':<10}", end="")
    print()
    print("-" * 60)

    for r in results_table:
        print(f"{r['conf']:<8.2f} {r['avg_count']:<12.1f} {r['std']:<10.1f} {r['time_ms']:<10.0f}", end="")
        if r['error'] is not None:
            print(f"{r['error']:<10.1f}", end="")
        print()

    # Recommend best confidence
    if args.known_count and results_table:
        best = min(results_table, key=lambda x: x['error'] if x['error'] else float('inf'))
        print(f"\nRecommended confidence: {best['conf']:.2f} (error: {best['error']:.1f}%)")
    elif results_table:
        # If no known count, recommend based on stability
        best = min(results_table, key=lambda x: x['std'])
        print(f"\nRecommended confidence (most stable): {best['conf']:.2f}")

    print(f"{'='*60}")


if __name__ == "__main__":
    main()
