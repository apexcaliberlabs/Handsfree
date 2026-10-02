import argparse
import os
import sys
import threading
import time
from pathlib import Path

# Ensure package root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from handsfree import __app_name__, __version__
from handsfree.config import config
from handsfree.core.camera import CameraFeed
from handsfree.core.gestures import GestureEngine
from handsfree.core.mouse import MouseController
from handsfree.core.tracker import HandTracker
from handsfree.ui.calibration import CalibrationWizard
from handsfree.ui.glowing_cursor import GlowingCursorOverlay
from handsfree.ui.preview import CameraPreviewHUD
from handsfree.ui.tray import SystemTrayApp


class HandsfreeApp:
    """Main application lifecycle controller for Handsfree."""

    def __init__(self) -> None:
        self.is_active: bool = True
        self.is_running: bool = False

        print(f"[{__app_name__}] Initializing v{__version__} by Apex Caliber Labs...")

        # Initialize core services
        self.mouse = MouseController()
        self.camera = CameraFeed()
        self.tracker: Optional[HandTracker] = None

        try:
            self.tracker = HandTracker()
        except Exception as e:
            print(f"[{__app_name__}] Error loading HandTracker: {e}")

        self.gesture_engine = GestureEngine(self.mouse)
        self.overlay = GlowingCursorOverlay()
        self.preview_hud = CameraPreviewHUD(self.camera, self.gesture_engine)

        # System tray controller
        self.tray = SystemTrayApp(
            on_toggle_active=self.toggle_active,
            on_open_calibration=self.open_calibration,
            on_toggle_hud=self.toggle_hud,
            on_exit=self.shutdown
        )

        self.worker_thread: Optional[threading.Thread] = None

    def toggle_active(self, active: bool) -> None:
        """Pauses or resumes hand tracking and overlay."""
        self.is_active = active
        self.overlay.set_visible(active)
        if not active:
            self.gesture_engine.reset_filters()
        print(f"[{__app_name__}] Tracking {'Resumed' if active else 'Paused'}")

    def open_calibration(self) -> None:
        """Opens setup and calibration wizard."""
        wizard = CalibrationWizard(self.camera, on_complete=self._on_calibration_complete)
        wizard.launch()

    def _on_calibration_complete(self) -> None:
        self.gesture_engine.reset_filters()
        print(f"[{__app_name__}] Calibration applied.")

    def toggle_hud(self, open_hud: bool) -> None:
        if open_hud:
            self.preview_hud.show()
        else:
            self.preview_hud.hide()

    def start(self) -> None:
        """Starts background tracking, overlay, and system tray."""
        self.is_running = True

        # Start camera capture thread
        if not self.camera.start():
            print(f"[{__app_name__}] Warning: Could not open camera. Retrying in background...")

        # Start glowing cursor overlay
        self.overlay.start()

        # Start system tray
        self.tray.start()

        # Launch calibration wizard if initial setup was never run
        if not config.get("initial_setup_completed", False):
            print(f"[{__app_name__}] First run detected - launching Setup Wizard...")
            self.open_calibration()

        # Start main tracking loop thread
        self.worker_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True,
            name="HandsfreeTrackingWorker"
        )
        self.worker_thread.start()

        print(f"[{__app_name__}] Running in background system tray.")

    def _tracking_loop(self) -> None:
        """High-frequency vision processing loop."""
        last_frame_ts = 0.0

        while self.is_running:
            if not self.is_active:
                time.sleep(0.05)
                continue

            frame, frame_ts = self.camera.get_latest_frame()
            if frame is None or frame_ts == last_frame_ts:
                time.sleep(0.005)
                continue

            last_frame_ts = frame_ts

            if self.tracker is None:
                time.sleep(0.05)
                continue

            try:
                hands, handedness = self.tracker.process_frame(frame)
                if hands:
                    # Track dominant/active hand
                    landmarks = hands[0]
                    hand_label = handedness[0] if handedness else "Right"
                    result = self.gesture_engine.process_hand(landmarks, hand_label)

                    # Update floating glowing cursor
                    self.overlay.update_position(
                        result["cursor_x"],
                        result["cursor_y"],
                        mode=result["mode"],
                        pinch_factor=result["pinch_factor"]
                    )
                else:
                    # Hand not in view: smooth release
                    if self.gesture_engine.is_pinching or self.gesture_engine.is_dragging:
                        self.gesture_engine.reset_filters()
            except Exception as e:
                # Prevent any frame glitch from breaking the loop
                time.sleep(0.01)

    def shutdown(self) -> None:
        """Stops all background processes cleanly."""
        print(f"[{__app_name__}] Shutting down...")
        self.is_running = False
        self.is_active = False

        if self.gesture_engine:
            self.gesture_engine.reset_filters()

        if self.preview_hud:
            self.preview_hud.hide()

        if self.overlay:
            self.overlay.stop()

        if self.camera:
            self.camera.stop()

        if self.tray:
            self.tray.stop()

        sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Handsfree by Apex Caliber Labs")
    parser.add_argument("--background", action="store_true", help="Start directly in system tray")
    parser.add_argument("--calibrate", action="store_true", help="Launch calibration wizard immediately")
    args = parser.parse_args()

    app = HandsfreeApp()
    if args.calibrate:
        app.open_calibration()
    app.start()

    # Keep main process alive while background threads execute
    try:
        while app.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        app.shutdown()


if __name__ == "__main__":
    main()
