"""
FocusTracker-AI — Focus Analytics Tracker
Logs every phone-detection event and produces end-of-day summaries.
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

import config


def _ensure_log_file() -> Path:
    """Create the CSV log file with headers if it doesn't exist."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not config.ANALYTICS_FILE.exists():
        with open(config.ANALYTICS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "event"])
    return config.ANALYTICS_FILE


def log_event(event: str) -> None:
    """
    Append a timestamped event to the CSV log.
    Events: "phone_detected", "phone_removed"
    """
    path = _ensure_log_file()
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), event])


def print_summary() -> None:
    """
    Parse the log and print an end-of-day focus summary:
      • Total Distractions
      • Longest Focus Streak
      • Most Distracted Hour
    """
    path = _ensure_log_file()
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("\n📊  No data recorded yet.\n")
        return

    # ── Parse events ──────────────────────────────────────────
    detections: list[datetime] = []
    removals: list[datetime] = []
    for row in rows:
        ts = datetime.fromisoformat(row["timestamp"])
        if row["event"] == "phone_detected":
            detections.append(ts)
        elif row["event"] == "phone_removed":
            removals.append(ts)

    total_distractions = len(detections)

    # ── Longest focus streak ──────────────────────────────────
    # A "focus streak" is the gap between consecutive detection events,
    # or from start-of-log to first detection, or last removal to now.
    all_times = sorted(detections + removals)
    longest_focus = timedelta(0)
    if removals:
        # Gaps between a removal and the next detection
        removal_set = sorted(removals)
        detection_set = sorted(detections)
        for rem_time in removal_set:
            # Find the next detection after this removal
            next_det = [d for d in detection_set if d > rem_time]
            if next_det:
                gap = next_det[0] - rem_time
                longest_focus = max(longest_focus, gap)
            else:
                # From last removal to now
                gap = datetime.now() - rem_time
                longest_focus = max(longest_focus, gap)

    # If there were detections, also consider time before the first one
    if detections and rows:
        first_ts = datetime.fromisoformat(rows[0]["timestamp"])
        gap = detections[0] - first_ts
        if gap > timedelta(0):
            longest_focus = max(longest_focus, gap)

    # ── Most distracted hour ──────────────────────────────────
    hour_counts: dict[int, int] = {}
    for d in detections:
        hour_counts[d.hour] = hour_counts.get(d.hour, 0) + 1
    most_distracted_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None

    # ── Print ─────────────────────────────────────────────────
    focus_mins = int(longest_focus.total_seconds() // 60)
    focus_hrs = focus_mins // 60
    focus_remaining = focus_mins % 60

    print("\n" + "=" * 50)
    print("       FOCUSTRACKER-AI  —  Daily Summary")
    print("=" * 50)
    print(f"  Total Distractions      : {total_distractions}")
    if focus_hrs > 0:
        print(f"  Longest Focus Streak    : {focus_hrs}h {focus_remaining}m")
    else:
        print(f"  Longest Focus Streak    : {focus_mins}m")
    if most_distracted_hour is not None:
        print(f"  Most Distracted Hour    : {most_distracted_hour:02d}:00 – {most_distracted_hour:02d}:59")
    else:
        print(f"  Most Distracted Hour    : N/A")
    print("=" * 50 + "\n")
