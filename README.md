<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="YOLOv8">
  <img src="https://img.shields.io/badge/OpenCV-4.9+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
</p>

<h1 align="center">FocusTracker-AI</h1>

<p align="center">
  <strong>An AI-powered desktop app that detects when you pick up your phone and forces you to put it down.</strong>
</p>

<p align="center">
  Zero willpower required. Your webcam watches for your phone using real-time object detection.<br>
  The moment it appears — a full-screen, unclosable motivational video takes over your screen<br>
  until the phone is gone.
</p>

---

## The Problem

You sit down to do deep work. Twenty minutes later, you're scrolling Instagram. It wasn't a conscious decision — your hand just *reached* for the phone. Productivity apps, screen-time limits, and "Do Not Disturb" modes all fail because they rely on the one thing that's already compromised: **your willpower.**

## The Solution

**FocusTracker-AI** removes willpower from the equation entirely. It uses your webcam and a YOLOv8 object detection model to monitor your desk in real time. The instant a phone appears in the frame, an unmissable full-screen video intervention takes over your display — and it **cannot be closed, minimized, or Alt-Tabbed away** until the phone is physically removed from the camera's view.

It's not an app you can dismiss. It's a consequence you can't ignore.

---

## Features

| Feature | Description |
|---|---|
| **Zero-Tolerance Detection** | YOLOv8 nano model detects phones instantly — no grace period, no second chances. |
| **Smart Cooldown Logic** | Won't flicker off from dropped frames. The phone must be absent for 1.5s before the intervention dismisses. |
| **Unclosable Video Intervention** | A random `.mp4` from your `/media` folder launches full-screen, always-on-top. You cannot escape it. |
| **Pomodoro Timer** | Built-in 25/5 work-break cycle. Detection pauses during breaks — phone is allowed. |
| **Focus Analytics** | Logs every distraction with timestamps. Prints a daily summary: total distractions, longest focus streak, most distracted hour. |
| **Dual Mode** | `DEMO` mode shows live bounding boxes + FPS for recording demos. `BACKGROUND` runs silently. |
| **GPU + CPU Support** | Auto-detects CUDA for NVIDIA GPUs. Falls back to CPU seamlessly — YOLOv8n runs great on both. |

---

## How It Works

```
Webcam Feed ──> YOLOv8 Detection ──> Phone Found?
                                         │
                                    YES  │  NO
                                         │
                          ┌──────────────┴──────────────┐
                          ▼                             ▼
                  Trigger Intervention          Cooldown Timer
                  (full-screen video,           (1.5s must pass
                   always-on-top,               before dismissal
                   unclosable)                  to handle dropped
                          │                     frames)
                          │                             │
                          └──────────┬──────────────────┘
                                     ▼
                              Log to CSV
                         (analytics tracker)
```

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **VLC Media Player** (64-bit) — [Download here](https://www.videolan.org/vlc/)
- A **webcam** (built-in or USB)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/FocusTracker-AI.git
cd FocusTracker-AI

# 2. Install PyTorch (CPU — works great with YOLOv8 nano)
pip install torch torchvision torchaudio

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your intervention videos
#    Place one or more .mp4 files into the /media folder.
#    Motivational speeches, focus reminders, anything you want.
```

> **NVIDIA GPU?** Replace step 2 with:
> ```bash
> pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```

### Usage

```bash
# Demo mode — shows live webcam feed with bounding boxes (great for testing)
python main.py --mode DEMO

# Background mode — runs silently, no window
python main.py --mode BACKGROUND

# Disable the Pomodoro timer
python main.py --no-pomodoro

# View today's focus summary
python main.py --summary
```

---

## Project Structure

```
FocusTracker-AI/
├── main.py              # Entry point — main detection loop
├── detector.py          # YOLOv8 wrapper with frame skip + confidence smoothing
├── intervention.py      # Full-screen VLC player with Win32 always-on-top
├── analytics.py         # CSV logger + daily focus summary
├── pomodoro.py          # 25/5 Pomodoro timer with overlay
├── config.py            # All configurable settings in one place
├── requirements.txt     # Python dependencies
├── media/               # Your .mp4 intervention videos go here
└── logs/                # Auto-generated focus analytics (CSV)
```

---

## Configuration

All settings live in [`config.py`](config.py) — no environment variables, no YAML, just Python:

```python
# Detection
CONFIDENCE_THRESHOLD = 0.40    # Lower = more sensitive
INFERENCE_SIZE = 320           # Resize frame before YOLO (smaller = faster)
SKIP_FRAMES = 2                # Run YOLO every Nth frame

# Smart cooldown (prevents flicker from dropped detections)
COOLDOWN_SECONDS = 1.5         # Phone must be gone this long to dismiss

# Pomodoro
USE_POMODORO = True
WORK_MINUTES = 25
BREAK_MINUTES = 5

# Webcam
CAMERA_INDEX = 0               # Change if you have multiple cameras
```

---

## Focus Analytics

Every session logs `phone_detected` and `phone_removed` events with timestamps to `logs/focus_log.csv`. Run the summary anytime:

```bash
python main.py --summary
```

```
==================================================
       FOCUSTRACKER-AI  —  Daily Summary
==================================================
  Total Distractions      : 7
  Longest Focus Streak    : 1h 12m
  Most Distracted Hour    : 14:00 – 14:59
==================================================
```

---

## Roadmap

- [x] Real-time phone detection with YOLOv8
- [x] Full-screen, always-on-top video intervention (Win32)
- [x] Pomodoro timer with break detection pause
- [x] Focus analytics with daily summary
- [x] Smart cooldown to prevent detection flicker
- [x] Frame skipping + resize for CPU optimisation
- [x] Confidence smoothing across frames
- [ ] **Cross-platform support** — macOS / Linux window management
- [ ] **Web dashboard** — visualise focus trends over days/weeks
- [ ] **Custom detection targets** — block other distractions (tablets, game controllers)
- [ ] **Audio intervention mode** — alarm sound instead of video
- [ ] **Team mode** — shared leaderboard for accountability groups
- [ ] **Notification integration** — Slack/Discord alerts when focus streaks break
- [ ] **Auto-start on boot** — system tray integration

---

## Contributing

Contributions are welcome! This project is intentionally modular — each feature lives in its own file. Here's how to get started:

1. **Fork** the repository
2. **Create a branch** (`git checkout -b feature/your-feature`)
3. **Make your changes** — follow the existing code style
4. **Test** with both `DEMO` and `BACKGROUND` modes
5. **Submit a Pull Request**

Good first issues:
- Add macOS/Linux support to `intervention.py`
- Add an audio-only intervention mode
- Build a simple web dashboard for `logs/focus_log.csv`

---

## Tech Stack

| Component | Technology |
|---|---|
| Object Detection | [YOLOv8](https://github.com/ultralytics/ultralytics) (Nano) |
| Computer Vision | [OpenCV](https://opencv.org/) |
| Deep Learning | [PyTorch](https://pytorch.org/) |
| Video Playback | [VLC](https://www.videolan.org/) via `python-vlc` |
| Window Management | Win32 API (`ctypes`) |
| Analytics | CSV + Python stdlib |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>Stop scrolling. Start focusing.</strong><br>
  If this helped you, give it a star and share it with someone who needs it.
</p>
