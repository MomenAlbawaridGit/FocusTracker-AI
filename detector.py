"""
FocusTracker-AI — YOLOv8 Phone Detector
Handles model loading, GPU/CPU selection, per-frame inference,
frame skipping, resize optimisation, and confidence smoothing.
"""

import collections

import cv2
import torch
from ultralytics import YOLO

import config


class PhoneDetector:
    """
    Wraps a YOLOv8 model to detect cell phones.
    Automatically uses CUDA if available, otherwise falls back to CPU.

    Optimisations:
      - Resizes frames to `config.INFERENCE_SIZE` before inference.
      - Skips frames (`config.SKIP_FRAMES`) to reduce CPU load.
      - Smooths confidence over a rolling window to avoid flicker.
    """

    def __init__(self) -> None:
        # ── Device selection ──────────────────────────────────
        if torch.cuda.is_available():
            self.device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[Detector] CUDA available — using GPU: {gpu_name}")
        else:
            self.device = "cpu"
            print("[Detector] CUDA not available — falling back to CPU")

        # ── Load YOLOv8 ──────────────────────────────────────
        print(f"[Detector] Loading {config.YOLO_MODEL} ...")
        self.model = YOLO(config.YOLO_MODEL)
        self.model.to(self.device)
        print("[Detector] Model ready.")

        # ── Frame skipping state ─────────────────────────────
        self._frame_count = 0
        self._last_detections: list[dict] = []

        # ── Confidence smoothing ─────────────────────────────
        self._confidence_history: collections.deque = collections.deque(
            maxlen=config.SMOOTHING_WINDOW
        )

    @property
    def smoothed_confidence(self) -> float:
        """Return the rolling average confidence over recent frames."""
        if not self._confidence_history:
            return 0.0
        return sum(self._confidence_history) / len(self._confidence_history)

    def detect(self, frame) -> list[dict]:
        """
        Run inference on a single frame (with skip & resize optimisation).
        Returns a list of detections, each being:
            {"bbox": (x1, y1, x2, y2), "confidence": float}
        Only includes detections for class 67 (cell phone) above threshold.
        """
        self._frame_count += 1

        # ── Frame skipping: reuse last result on skipped frames ──
        if self._frame_count % config.SKIP_FRAMES != 0:
            return self._last_detections

        # ── Resize for faster inference ──────────────────────
        h, w = frame.shape[:2]
        scale = config.INFERENCE_SIZE / w
        small = cv2.resize(frame, (config.INFERENCE_SIZE, int(h * scale)))

        results = self.model.predict(
            small,
            conf=config.CONFIDENCE_THRESHOLD,
            device=self.device,
            classes=[config.PHONE_CLASS_ID],
            verbose=False,
        )

        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id == config.PHONE_CLASS_ID:
                    # Scale bounding box back to original frame size
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    detections.append({
                        "bbox": (
                            int(x1 / scale),
                            int(y1 / scale),
                            int(x2 / scale),
                            int(y2 / scale),
                        ),
                        "confidence": conf,
                    })

        # ── Update confidence history ────────────────────────
        if detections:
            best_conf = max(d["confidence"] for d in detections)
            self._confidence_history.append(best_conf)
        else:
            self._confidence_history.append(0.0)

        self._last_detections = detections
        return detections
