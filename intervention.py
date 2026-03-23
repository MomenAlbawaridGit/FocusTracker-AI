"""
FocusTracker-AI — Strict Media Intervention
Launches a random .mp4 from /media in full-screen, always-on-top mode.
The video loops continuously and cannot be closed until the phone disappears.
Uses python-vlc for playback and pywin32 for window management.
"""

import ctypes
import random
import threading
import time
from pathlib import Path

import vlc

import config

# ── Win32 constants ───────────────────────────────────────────
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
SW_MAXIMIZE = 3
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080  # Hides from taskbar

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class InterventionPlayer:
    """
    Manages a full-screen, always-on-top VLC video window.
    Runs entirely on a background thread so the webcam loop is never blocked.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False          # Is video currently showing?
        self._should_play = False     # Should we be playing right now?
        self._vlc_instance: vlc.Instance | None = None
        self._player: vlc.MediaPlayer | None = None
        self._thread: threading.Thread | None = None
        self._vlc_hwnd = None

    # ── Public API ────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    def trigger(self) -> None:
        """
        Start the intervention.  If already playing, this is a no-op.
        Picks a random .mp4 and launches it full-screen.
        """
        with self._lock:
            if self._active:
                return
            self._should_play = True
            self._active = True

        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()

    def dismiss(self) -> None:
        """
        Stop the intervention (called when the phone leaves the frame).
        """
        with self._lock:
            self._should_play = False

    # ── Internals ─────────────────────────────────────────────

    def _pick_video(self) -> Path | None:
        """Return a random .mp4 from the media folder, or None."""
        videos = list(config.MEDIA_DIR.glob("*.mp4"))
        if not videos:
            print("[Intervention] WARNING: No .mp4 files found in /media — "
                  "add videos to enable the intervention.")
            return None
        return random.choice(videos)

    def _play_loop(self) -> None:
        """
        Background thread: start VLC, force the window on top,
        loop the video, and tear down when dismissed.
        """
        video = self._pick_video()
        if video is None:
            with self._lock:
                self._active = False
            return

        print(f"[Intervention] Playing: {video.name}")

        # ── Create VLC player ─────────────────────────────────
        self._vlc_instance = vlc.Instance("--no-video-title-show",
                                          "--no-osd",
                                          "--input-repeat=999999")
        self._player = self._vlc_instance.media_player_new()
        media = self._vlc_instance.media_new(str(video))
        media.add_option("input-repeat=999999")  # Loop effectively forever
        self._player.set_media(media)
        self._player.set_fullscreen(True)
        self._player.play()

        # Give VLC a moment to create its window
        time.sleep(1.5)

        # ── Force always-on-top via Win32 ─────────────────────
        self._force_topmost()

        # ── Keep enforcing topmost while phone is visible ─────
        while True:
            with self._lock:
                if not self._should_play:
                    break
            # Re-enforce topmost every 500 ms in case user tries to Alt-Tab
            self._force_topmost()
            time.sleep(0.5)

        # ── Tear down ─────────────────────────────────────────
        self._player.stop()
        self._player.release()
        self._vlc_instance.release()
        self._player = None
        self._vlc_instance = None
        self._vlc_hwnd = None
        print("[Intervention] Dismissed — phone removed from frame.")

        with self._lock:
            self._active = False

    def _force_topmost(self) -> None:
        """
        Find the VLC window and force it to be full-screen + always-on-top.
        Uses EnumWindows to locate VLC's playback window.
        """
        if self._vlc_hwnd and user32.IsWindow(self._vlc_hwnd):
            # Re-apply topmost flag
            user32.SetWindowPos(
                self._vlc_hwnd, HWND_TOPMOST,
                0, 0,
                user32.GetSystemMetrics(0),  # Screen width
                user32.GetSystemMetrics(1),  # Screen height
                SWP_SHOWWINDOW,
            )
            return

        # ── Enumerate windows to find VLC ─────────────────────
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        )
        target_hwnd = None

        def enum_callback(hwnd, _):
            nonlocal target_hwnd
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if "vlc" in title or "direct3d" in title:
                    target_hwnd = hwnd
                    return False  # Stop enumeration
            return True

        user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

        if target_hwnd:
            self._vlc_hwnd = target_hwnd
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)

            # Remove window decorations for true fullscreen
            style = WS_POPUP | WS_VISIBLE
            user32.SetWindowLongW(target_hwnd, GWL_STYLE, style)

            ex_style = WS_EX_TOPMOST | WS_EX_TOOLWINDOW
            user32.SetWindowLongW(target_hwnd, GWL_EXSTYLE, ex_style)

            # Position full-screen and topmost
            user32.SetWindowPos(
                target_hwnd, HWND_TOPMOST,
                0, 0, screen_w, screen_h,
                SWP_SHOWWINDOW,
            )

            # Force to foreground
            user32.SetForegroundWindow(target_hwnd)
