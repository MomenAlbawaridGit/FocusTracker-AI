"""
FocusTracker-AI — Pomodoro Timer
25-min work / 5-min break cycle running on its own thread.
During breaks, detection is paused and a subtle overlay is shown.
"""

import threading
import time
from enum import Enum, auto

import cv2
import numpy as np

import config


class Phase(Enum):
    WORK = auto()
    BREAK = auto()


class PomodoroTimer:
    """
    Non-blocking Pomodoro timer.
    Query `is_break` to know whether detection should be paused.
    """

    def __init__(self) -> None:
        self.phase: Phase = Phase.WORK
        self.phase_end: float = time.time() + config.WORK_MINUTES * 60
        self.cycle_count: int = 0
        self._lock = threading.Lock()
        self._running = True

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ── Public API ────────────────────────────────────────────

    @property
    def is_break(self) -> bool:
        with self._lock:
            return self.phase == Phase.BREAK

    @property
    def remaining_seconds(self) -> float:
        with self._lock:
            return max(0.0, self.phase_end - time.time())

    def stop(self) -> None:
        self._running = False

    # ── Internal ──────────────────────────────────────────────

    def _run(self) -> None:
        """Background loop that toggles phases when the timer expires."""
        while self._running:
            time.sleep(0.5)
            with self._lock:
                if time.time() >= self.phase_end:
                    if self.phase == Phase.WORK:
                        self.phase = Phase.BREAK
                        self.phase_end = time.time() + config.BREAK_MINUTES * 60
                        print(f"[Pomodoro] Break started — {config.BREAK_MINUTES} min")
                    else:
                        self.phase = Phase.WORK
                        self.phase_end = time.time() + config.WORK_MINUTES * 60
                        self.cycle_count += 1
                        print(f"[Pomodoro] Work cycle #{self.cycle_count + 1} started — {config.WORK_MINUTES} min")

    # ── Overlay ───────────────────────────────────────────────

    def draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw a subtle Pomodoro status bar on the frame.
        During breaks, show a relaxing green banner.
        During work, show a minimal timer in the corner.
        """
        h, w = frame.shape[:2]
        remaining = self.remaining_seconds
        mins, secs = divmod(int(remaining), 60)

        with self._lock:
            phase = self.phase

        if phase == Phase.BREAK:
            # Green banner across the top
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 48), (0, 160, 0), -1)
            frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
            text = f"BREAK  {mins:02d}:{secs:02d}  —  Phone allowed"
            cv2.putText(frame, text, (w // 2 - 220, 33),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            # Small timer in top-right corner
            text = f"WORK {mins:02d}:{secs:02d}"
            cv2.putText(frame, text, (w - 185, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        return frame
