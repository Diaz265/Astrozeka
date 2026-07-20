"""
detect_batch.py — Run a trained detector over a folder of images and save
(not just display) the annotated results.

Fixes vs. the original detect_cv.py:
  * No check that the model checkpoint or image folder actually exist —
    the original would crash deep inside ultralytics/cv2 with a confusing
    error instead of a clear message.
  * `cv2.imshow` + `cv2.waitKey(0)` requires an interactive display; in any
    headless/server/CI context (including this one) it silently does
    nothing useful. We now always save annotated images to an output
    folder, and only pop up a window if --show is passed.
  * Iterated only *.jpg; now also picks up *.png and *.jpeg.
  * Boxes were drawn manually with cv2.rectangle from raw xyxy tensors,
    duplicating what result.plot() already does correctly (including
    class labels and confidence) — simplified to use result.plot().
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")


def run(model_path: str, image_folder: str, output_folder: str, show: bool = False) -> None:
    model_file = Path(model_path)
    if not model_file.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found at {model_file}. "
            "Train a model first with train.py, or point --model at yolov8n.pt "
            "for a stock (non-debris-specific) smoke test."
        )

    image_dir = Path(image_folder)
    images = sorted(p for ext in IMAGE_EXTENSIONS for p in image_dir.glob(ext))
    if not images:
        raise FileNotFoundError(f"No images found in {image_dir} (looked for {IMAGE_EXTENSIONS})")

    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_file))

    for img_path in images:
        print(f"Processing {img_path}...")
        results = model(str(img_path), verbose=False)
        annotated = results[0].plot()

        out_path = out_dir / img_path.name
        cv2.imwrite(str(out_path), annotated)

        if show:
            cv2.imshow("Debris & Satellite Detection", annotated)
            cv2.waitKey(0)

    if show:
        cv2.destroyAllWindows()

    print(f"Done. Annotated images saved to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch debris/satellite detection over a folder of images")
    parser.add_argument("--model", default="runs/train/weights/best.pt",
                         help="Path to trained YOLO checkpoint")
    parser.add_argument("--images", default="data/cv/dataset/images",
                         help="Folder of input images")
    parser.add_argument("--output", default="outputs/detections",
                         help="Folder to save annotated images")
    parser.add_argument("--show", action="store_true", help="Also pop up a display window")
    args = parser.parse_args()
    run(args.model, args.images, args.output, args.show)
