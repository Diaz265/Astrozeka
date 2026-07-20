"""
train.py — Fine-tune a YOLOv8 model to detect debris/satellites in imagery.

Fixes vs. the original train_detector.py:
  * The original called `model.train(...)` but never created `model` —
    it would raise `NameError: name 'model' is not defined` immediately.
  * The original config was literally `...` (an ellipsis placeholder) with
    no dataset path, epochs, image size, etc. — not runnable as-is.
  * Device selection only checked for Apple Silicon (mps); added a CUDA
    check too, with a CPU fallback, so this also runs on non-Mac hardware.

IMPORTANT — before running this for real:
  This repo currently ships `vision/dataset.yaml` but no labeled images.
  YOLO needs a populated `data/cv/dataset/images/` (+ matching YOLO-format
  `labels/`) split into train/val to learn anything. Right now this script
  will run and fail with a "no images found" error from ultralytics until
  you add labeled data — that's expected, not a bug in this script.
"""

from __future__ import annotations

import argparse

import torch
from ultralytics import YOLO


def pick_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def run(data_yaml: str, base_model: str, epochs: int, imgsz: int) -> None:
    device = pick_device()
    print(f"Training on device: {device}")

    model = YOLO(base_model)  # e.g. "yolov8n.pt" as a starting checkpoint
    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        device=device,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a YOLOv8 debris detector")
    parser.add_argument("--data", default="vision/dataset.yaml", help="Path to dataset yaml")
    parser.add_argument("--base-model", default="yolov8n.pt", help="Starting checkpoint to fine-tune")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    run(args.data, args.base_model, args.epochs, args.imgsz)
