import threading
import time
import tkinter as tk
from typing import Optional
import cv2
import numpy as np
from PIL import Image, ImageTk

from handsfree.config import config
from handsfree.core.tracker import HandTracker


class CameraPreviewHUD:
    """
    Floating HUD window displaying live webcam feed,
    MediaPipe skeleton, and real-time gesture telemetry.
    """

    def __init__(self, camera_feed, gesture_engine) -> None:
        self.camera_feed = camera_feed
        self.gesture_engine = gesture_engine

        self.root: Optional[tk.Toplevel] = None
        self.label_video: Optional[tk.Label] = None
        self.label_status: Optional[tk.Label] = None
        self.is_open: bool = False
        self.lock = threading.Lock()

    def show(self) -> None:
        """Opens or brings the preview HUD to front."""
        with self.lock:
            if self.is_open and self.root:
                try:
                    self.root.deiconify()
                    self.root.lift()
                    return
                except Exception:
                    pass

            self.is_open = True
            threading.Thread(target=self._create_window, daemon=True, name="HandsfreeHUDThread").start()

    def _create_window(self) -> None:
        window = tk.Tk()
        self.root = window
        window.title("Handsfree - Live Camera Preview (Apex Caliber Labs)")
        window.geometry("640x530")
        window.resizable(False, False)
        window.configure(bg="#121217")
        window.protocol("WM_DELETE_WINDOW", self.hide)

        # Header bar
        header = tk.Frame(window, bg="#1a1a24", height=40)
        header.pack(fill="x", side="top")

        lbl_title = tk.Label(
            header,
            text="HANDSFREE VISION HUD",
            font=("Segoe UI", 10, "bold"),
            fg="#00e5ff",
            bg="#1a1a24"
        )
        lbl_title.pack(side="left", padx=12, pady=8)

        # Video canvas
        self.label_video = tk.Label(window, bg="#0d0d12")
        self.label_video.pack(fill="both", expand=True, padx=10, pady=6)

        # Telemetry footer
        footer = tk.Frame(window, bg="#1a1a24", height=34)
        footer.pack(fill="x", side="bottom")

        self.label_status = tk.Label(
            footer,
            text="Tracking: Initializing...",
            font=("Consolas", 9),
            fg="#a0a0b0",
            bg="#1a1a24"
        )
        self.label_status.pack(side="left", padx=12, pady=6)

        # Loop update
        self._update_feed()
        window.mainloop()

    def _update_feed(self) -> None:
        if not self.is_open or not self.root:
            return

        frame, _ = self.camera_feed.get_latest_frame()
        if frame is not None:
            # Resize for HUD display
            display_frame = cv2.resize(frame, (620, 420))
            h, w, _ = display_frame.shape

            # Draw reach bounding box overlay
            rl = int(config.get("reach_left", 0.18) * w)
            rt = int(config.get("reach_top", 0.18) * h)
            rr = int(config.get("reach_right", 0.82) * w)
            rb = int(config.get("reach_bottom", 0.82) * h)
            cv2.rectangle(display_frame, (rl, rt), (rr, rb), (70, 70, 90), 1, cv2.LINE_AA)

            # Convert to PIL and update Tkinter image
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            tk_img = ImageTk.PhotoImage(image=pil_img)

            if self.label_video:
                self.label_video.configure(image=tk_img)
                self.label_video.image = tk_img

            # Update telemetry label
            mode = getattr(self.gesture_engine, "mode", "MOVE")
            is_pinching = getattr(self.gesture_engine, "is_pinching", False)
            is_scrolling = getattr(self.gesture_engine, "is_scrolling", False)
            status_text = f"Mode: {mode} | Pinch: {'ACTIVE' if is_pinching else 'OFF'} | Scroll: {'ACTIVE' if is_scrolling else 'OFF'}"
            if self.label_status:
                self.label_status.configure(text=status_text)

        if self.root:
            self.root.after(33, self._update_feed)

    def hide(self) -> None:
        """Hides or destroys preview window."""
        with self.lock:
            self.is_open = False
            if self.root:
                try:
                    self.root.destroy()
                except Exception:
                    pass
                self.root = None
