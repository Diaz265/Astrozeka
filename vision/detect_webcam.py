"""
detect_webcam.py — Live webcam debris/satellite detection.

Fixes vs. the original detect.py:
  * The original file's content was literally:
        cat > ~/Desktop/AstroZeka/detect.py << 'EOF'
        ... python code ...
        EOF
    i.e. someone pasted a shell heredoc *around* the Python code, so the
    file itself was not valid Python and would raise a SyntaxError if run
    directly with `python detect.py`.
  * Uses the untrained stock "yolov8n.pt" checkpoint, which detects COCO
    classes (people, cars, etc.), not orbital debris. That's fine for a
    smoke test of the pipeline, but it will not find "debris" as a class
    until you train on the dataset in vision/dataset.yaml — see train.py.
  * Added try/finally so the camera and windows are always released, even
    if the loop raises.
  * Removed the duplicate `cap.waitKey(1)` call (it was called twice per
    frame in the original, wasting time and reading double key events).
"""

from __future__ import annotations

import argparse

import cv2
from ultralytics import YOLO


def run(model_path: str = "yolov8n.pt", camera_index: int = 0) -> None:
    model = YOLO(model_path)
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}")

    cv2.namedWindow("AstroZeka", cv2.WINDOW_NORMAL)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame — stopping.")
                break

            results = model(frame, verbose=False)
            annotated = results[0].plot()
            cv2.imshow("AstroZeka", annotated)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live webcam debris detection")
    parser.add_argument("--model", default="yolov8n.pt",
                         help="Path to a YOLO checkpoint (default: stock yolov8n.pt)")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    args = parser.parse_args()
    run(args.model, args.camera)
