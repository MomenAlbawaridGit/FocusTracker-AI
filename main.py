"""
FocusTracker-AI — Main Entry Point
Real-time webcam phone detection with strict media intervention.

Usage:
    python main.py                          # Run with defaults from config.py
    python main.py --mode DEMO              # Show live feed with bounding boxes
    python main.py --mode BACKGROUND        # Silent monitoring (no window)
    python main.py --no-pomodoro            # Disable Pomodoro timer
    python main.py --summary                # Print today's focus summary and exit

Author : github.com/MomenAlbawaridGit
License: Unlicense (Public Domain)
"""

import argparse
import sys
import time
import cv2

import config
from analytics import log_event, print_summary
from detector import PhoneDetector
from intervention import InterventionPlayer
from pomodoro import PomodoroTimer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FocusTracker-AI")
    parser.add_argument(
        "--mode",
        choices=["DEMO", "BACKGROUND"],
        default=config.MODE,
        help="DEMO shows the webcam feed; BACKGROUND runs silently.",
    )
    parser.add_argument(
        "--no-pomodoro",
        action="store_true",
        help="Disable the Pomodoro timer.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print today's focus summary and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── Summary-only mode ─────────────────────────────────────
    if args.summary:
        print_summary()
        return

    # ── Initialise components ─────────────────────────────────
    detector = PhoneDetector()
    intervention = InterventionPlayer()
    pomodoro = PomodoroTimer() if (config.USE_POMODORO and not args.no_pomodoro) else None

    demo_mode = args.mode == "DEMO"

    # ── Detection persistence state ───────────────────────────
    raw_phone_visible = False       # Raw per-frame detection result
    last_seen_time = 0.0            # Timestamp when phone was last detected
    intervention_active = False     # Is intervention currently triggered?

    # ── FPS counter state ─────────────────────────────────────
    fps_time = time.time()
    fps_count = 0
    fps_display = 0.0

    # ── Open webcam ───────────────────────────────────────────
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

    if not cap.isOpened():
        print("[Error] Could not open webcam. Check CAMERA_INDEX in config.py.")
        sys.exit(1)

    print(f"\n[FocusTracker] Running in {args.mode} mode.")
    if pomodoro:
        print(f"[FocusTracker] Pomodoro enabled: {config.WORK_MINUTES}m work / {config.BREAK_MINUTES}m break")
    print(f"[FocusTracker] Detection cooldown: {config.COOLDOWN_SECONDS}s")
    print(f"[FocusTracker] Frame skip: every {config.SKIP_FRAMES} frame(s)")
    print("[FocusTracker] Press 'q' to quit.\n")

    # ── Main loop ─────────────────────────────────────────────
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Error] Failed to read from webcam.")
                break

            now = time.time()

            # ── FPS calculation ───────────────────────────────
            fps_count += 1
            if now - fps_time >= 1.0:
                fps_display = fps_count / (now - fps_time)
                fps_count = 0
                fps_time = now

            # ── Pomodoro break check ──────────────────────────
            if pomodoro and pomodoro.is_break:
                if demo_mode:
                    frame = pomodoro.draw_overlay(frame)
                    cv2.imshow("FocusTracker-AI", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    time.sleep(0.05)
                continue

            # ── Run detection ─────────────────────────────────
            detections = detector.detect(frame)
            raw_phone_visible = len(detections) > 0

            # ── Persistence / cooldown logic ──────────────────
            # If phone is detected in this frame, update last_seen_time
            if raw_phone_visible:
                last_seen_time = now

            # Phone is "logically visible" if seen within the cooldown window
            phone_visible = (now - last_seen_time) < config.COOLDOWN_SECONDS if last_seen_time > 0 else False

            # ── Sync with actual intervention state ──────────
            # If the VLC thread crashed or finished, reset our local flag
            if intervention_active and not intervention.is_active:
                intervention_active = False

            # ── State transitions ─────────────────────────────
            if phone_visible and not intervention_active:
                # Phone appeared — trigger intervention
                log_event("phone_detected")
                print("[Detection] Phone detected — triggering intervention!")
                intervention.trigger()
                intervention_active = True

            elif not phone_visible and intervention_active:
                # Phone gone for longer than cooldown — safe to dismiss
                log_event("phone_removed")
                print("[Detection] Phone removed — dismissing intervention.")
                intervention.dismiss()
                intervention_active = False

            # ── DEMO mode: draw overlays ──────────────────────
            if demo_mode:
                for det in detections:
                    x1, y1, x2, y2 = det["bbox"]
                    conf = det["confidence"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    label = f"Phone {conf:.0%}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                # Pomodoro overlay
                if pomodoro:
                    frame = pomodoro.draw_overlay(frame)

                # Status indicator
                if intervention_active:
                    status = "PHONE DETECTED"
                    color = (0, 0, 255)
                elif last_seen_time > 0 and (now - last_seen_time) < config.COOLDOWN_SECONDS:
                    # In cooldown — phone just disappeared, waiting to confirm
                    remaining = config.COOLDOWN_SECONDS - (now - last_seen_time)
                    status = f"Cooldown... {remaining:.1f}s"
                    color = (0, 165, 255)  # Orange
                else:
                    status = "Monitoring..."
                    color = (0, 200, 0)

                cv2.putText(frame, status, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                # FPS counter (top-right)
                cv2.putText(frame, f"FPS: {fps_display:.1f}", (frame.shape[1] - 140, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

                # Smoothed confidence bar
                smooth_conf = detector.smoothed_confidence
                if smooth_conf > 0:
                    bar_w = int(smooth_conf * 150)
                    cv2.rectangle(frame, (10, 40), (10 + bar_w, 55), (0, 0, 255), -1)
                    cv2.putText(frame, f"Avg: {smooth_conf:.0%}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

                cv2.imshow("FocusTracker-AI", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                # BACKGROUND mode — no window, just a small delay
                time.sleep(0.03)

    except KeyboardInterrupt:
        print("\n[FocusTracker] Interrupted by user.")

    # ── Cleanup ───────────────────────────────────────────────
    if pomodoro:
        pomodoro.stop()
    intervention.dismiss()
    cap.release()
    cv2.destroyAllWindows()

    # Show end-of-session summary
    print_summary()


if __name__ == "__main__":
    main()
