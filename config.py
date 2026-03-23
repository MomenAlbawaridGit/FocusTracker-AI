"""
FocusTracker-AI — Configuration
All tuneable knobs live here.  Edit this file or override via CLI flags.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"
LOGS_DIR = BASE_DIR / "logs"
ANALYTICS_FILE = LOGS_DIR / "focus_log.csv"

# ── Detection ─────────────────────────────────────────────────
YOLO_MODEL = "yolov8n.pt"          # Nano model — best speed for MX330
CONFIDENCE_THRESHOLD = 0.40         # Min confidence to count as detection
PHONE_CLASS_ID = 67                 # COCO class id for "cell phone"
INFERENCE_SIZE = 320                # Resize frame to this width before YOLO
SKIP_FRAMES = 2                     # Run YOLO every Nth frame (1 = every frame)

# ── Detection Persistence ────────────────────────────────────
# Prevents intervention from flickering off due to dropped frames.
# Phone must be absent for this many seconds before dismissing.
COOLDOWN_SECONDS = 1.5
# Number of recent frames to average confidence over
SMOOTHING_WINDOW = 5

# ── Execution Mode ────────────────────────────────────────────
#   "BACKGROUND"  → no webcam window (silent monitoring)
#   "DEMO"        → live feed with bounding boxes
MODE = "DEMO"

# ── Webcam ────────────────────────────────────────────────────
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# ── Pomodoro ──────────────────────────────────────────────────
USE_POMODORO = True
WORK_MINUTES = 25
BREAK_MINUTES = 5

# ── Intervention ──────────────────────────────────────────────
# The video player will remain on-screen and always-on-top until
# the phone is no longer visible in the frame.
