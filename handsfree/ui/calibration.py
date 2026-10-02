import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import cv2
import numpy as np
from PIL import Image, ImageTk

from handsfree.config import config
from handsfree.core.tracker import HandTracker


class CalibrationWizard:
    """
    Step-by-step Setup & Calibration Wizard for Handsfree:
    1. Camera Detection & Hand Recognition
    2. Reach & Motion Range Mapping
    3. Pinch Threshold & Click Tuning
    4. Smoothing & Cursor Speed
    """

    def __init__(self, camera_feed=None, on_complete=None) -> None:
        self.camera_feed = camera_feed
        self.on_complete = on_complete

        self.root: Optional[tk.Tk] = None
        self.tracker: Optional[HandTracker] = None
        self.is_running: bool = False
        self.step: int = 1

        # Calibration state
        self.captured_corners = {
            "top_left": None,
            "top_right": None,
            "bottom_right": None,
            "bottom_left": None
        }
        self.current_pinch_dist: float = 0.2
        self.current_index_coords = (0.5, 0.5)

    def launch(self) -> None:
        """Launches calibration window in a dedicated UI thread."""
        threading.Thread(target=self._run_wizard, daemon=True, name="HandsfreeCalibration").start()

    def _run_wizard(self) -> None:
        self.root = tk.Tk()
        self.root.title("Handsfree - Initial Setup & Calibration")
        self.root.geometry("740x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f14")

        # Initialize tracker
        try:
            self.tracker = HandTracker()
        except Exception as e:
            print(f"[Calibration] Tracker init warning: {e}")

        self.is_running = True
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Build UI layout
        self._build_ui()
        self._video_loop()
        self.root.mainloop()

    def _build_ui(self) -> None:
        # Header banner
        header = tk.Frame(self.root, bg="#161622", height=60)
        header.pack(fill="x", side="top")

        lbl_app = tk.Label(
            header,
            text="HANDSFREE",
            font=("Segoe UI", 14, "bold"),
            fg="#00e5ff",
            bg="#161622"
        )
        lbl_app.pack(side="left", padx=18, pady=12)

        lbl_sub = tk.Label(
            header,
            text="by Apex Caliber Labs  |  Calibration & Setup",
            font=("Segoe UI", 10),
            fg="#808098",
            bg="#161622"
        )
        lbl_sub.pack(side="left", pady=16)

        # Main content container
        content = tk.Frame(self.root, bg="#0f0f14")
        content.pack(fill="both", expand=True, padx=20, pady=12)

        # Left panel: live camera preview
        cam_panel = tk.Frame(content, bg="#161622", bd=1, relief="solid")
        cam_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.lbl_cam = tk.Label(cam_panel, bg="#000000")
        self.lbl_cam.pack(fill="both", expand=True, padx=4, pady=4)

        # Right panel: calibration step instructions & controls
        self.control_panel = tk.Frame(content, bg="#161622", width=300)
        self.control_panel.pack(side="right", fill="both", padx=(10, 0))
        self.control_panel.pack_propagate(False)

        self._render_step_controls()

        # Footer
        footer = tk.Frame(self.root, bg="#161622", height=50)
        footer.pack(fill="x", side="bottom")

        self.btn_prev = tk.Button(
            footer, text="< Back", font=("Segoe UI", 9),
            bg="#2a2a3c", fg="#ffffff", activebackground="#3a3a4c",
            command=self._prev_step, width=10, relief="flat"
        )
        self.btn_prev.pack(side="left", padx=16, pady=10)

        self.btn_next = tk.Button(
            footer, text="Next >", font=("Segoe UI", 9, "bold"),
            bg="#00bcd4", fg="#000000", activebackground="#00e5ff",
            command=self._next_step, width=12, relief="flat"
        )
        self.btn_next.pack(side="right", padx=16, pady=10)

    def _render_step_controls(self) -> None:
        for widget in self.control_panel.winfo_children():
            widget.destroy()

        p = self.control_panel

        if self.step == 1:
            # Step 1: Camera & Hand Presence
            tk.Label(p, text="Step 1 of 4", font=("Segoe UI", 9), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=14, pady=(16, 2))
            tk.Label(p, text="Hand Recognition", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(0, 10))
            desc = (
                "Ensure your webcam is centered.\n\n"
                "Raise your hand in front of the camera.\n"
                "You should see the glowing cyber-skeleton track your fingers in real time.\n\n"
                "Keep good lighting on your hands."
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d0", bg="#161622", justify="left", wraplength=260).pack(anchor="w", padx=14, pady=6)

        elif self.step == 2:
            # Step 2: Comfortable Reach Calibration
            tk.Label(p, text="Step 2 of 4", font=("Segoe UI", 9), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=14, pady=(16, 2))
            tk.Label(p, text="Reach Calibration", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(0, 8))
            desc = (
                "Define your natural physical workspace so you don't have to reach into extreme camera edges.\n\n"
                "Hold your index finger still and click Capture for each corner:"
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d0", bg="#161622", justify="left", wraplength=260).pack(anchor="w", padx=14, pady=4)

            btn_frame = tk.Frame(p, bg="#161622")
            btn_frame.pack(fill="x", padx=14, pady=8)

            for corner_name, label in [
                ("top_left", "Top-Left"),
                ("top_right", "Top-Right"),
                ("bottom_left", "Bottom-Left"),
                ("bottom_right", "Bottom-Right")
            ]:
                row = tk.Frame(btn_frame, bg="#161622")
                row.pack(fill="x", pady=3)
                lbl = tk.Label(row, text=f"{label}:", font=("Segoe UI", 9), fg="#ffffff", bg="#161622", width=12, anchor="w")
                lbl.pack(side="left")
                btn = tk.Button(
                    row, text="Capture", font=("Segoe UI", 8),
                    bg="#2d2d40", fg="#00e5ff", relief="flat",
                    command=lambda cn=corner_name: self._capture_corner(cn)
                )
                btn.pack(side="right")

        elif self.step == 3:
            # Step 3: Pinch Sensitivity
            tk.Label(p, text="Step 3 of 4", font=("Segoe UI", 9), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=14, pady=(16, 2))
            tk.Label(p, text="Pinch-to-Click", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(0, 8))
            desc = (
                "Pinch your thumb and index finger together to click (like Meta Quest).\n\n"
                "Adjust sensitivity below so pinch triggers comfortably:"
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d0", bg="#161622", justify="left", wraplength=260).pack(anchor="w", padx=14, pady=4)

            tk.Label(p, text="Pinch Distance Threshold:", font=("Segoe UI", 9), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(12, 2))
            self.scale_pinch = tk.Scale(
                p, from_=0.03, to=0.12, resolution=0.005, orient="horizontal",
                bg="#161622", fg="#00e5ff", highlightthickness=0,
                command=lambda val: config.set("pinch_threshold", float(val))
            )
            self.scale_pinch.set(config.get("pinch_threshold", 0.065))
            self.scale_pinch.pack(fill="x", padx=14)

            self.lbl_pinch_meter = tk.Label(p, text="Pinch Status: OPEN", font=("Segoe UI", 9, "bold"), fg="#888888", bg="#161622")
            self.lbl_pinch_meter.pack(anchor="w", padx=14, pady=12)

        elif self.step == 4:
            # Step 4: Smoothing & Speed
            tk.Label(p, text="Step 4 of 4", font=("Segoe UI", 9), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=14, pady=(16, 2))
            tk.Label(p, text="Pointer Dynamics", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(0, 8))

            tk.Label(p, text="Smoothness (Jitter Filter):", font=("Segoe UI", 9), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(8, 2))
            scale_smooth = tk.Scale(
                p, from_=0.5, to=3.0, resolution=0.1, orient="horizontal",
                bg="#161622", fg="#00e5ff", highlightthickness=0,
                command=lambda val: config.set("smoothing_min_cutoff", float(val))
            )
            scale_smooth.set(config.get("smoothing_min_cutoff", 1.2))
            scale_smooth.pack(fill="x", padx=14)

            tk.Label(p, text="Scroll Speed:", font=("Segoe UI", 9), fg="#ffffff", bg="#161622").pack(anchor="w", padx=14, pady=(10, 2))
            scale_scroll = tk.Scale(
                p, from_=0.5, to=3.0, resolution=0.1, orient="horizontal",
                bg="#161622", fg="#00e5ff", highlightthickness=0,
                command=lambda val: config.set("scroll_speed", float(val))
            )
            scale_scroll.set(config.get("scroll_speed", 1.4))
            scale_scroll.pack(fill="x", padx=14)

            btn_finish = tk.Button(
                p, text="Save & Complete Setup", font=("Segoe UI", 10, "bold"),
                bg="#00e676", fg="#000000", activebackground="#69f0ae",
                relief="flat", command=self._finish_calibration
            )
            btn_finish.pack(fill="x", padx=14, pady=24)

    def _capture_corner(self, corner_name: str) -> None:
        self.captured_corners[corner_name] = self.current_index_coords
        messagebox.showinfo("Corner Saved", f"Captured {corner_name.replace('_', ' ').title()} coordinate!")

    def _video_loop(self) -> None:
        if not self.is_running or not self.root:
            return

        if self.camera_feed is not None:
            frame, _ = self.camera_feed.get_latest_frame()
            if frame is not None and self.tracker is not None:
                hands, handedness = self.tracker.process_frame(frame)
                is_pinching = False

                if hands:
                    hand = hands[0]
                    # Index tip is landmark 8
                    idx_pt = hand[8]
                    self.current_index_coords = (idx_pt.x, idx_pt.y)

                    # Check pinch distance
                    thumb_pt = hand[4]
                    wrist = hand[0]
                    m_mcp = hand[9]
                    palm = max(0.1, np.hypot(wrist.x - m_mcp.x, wrist.y - m_mcp.y))
                    dist = np.hypot(thumb_pt.x - idx_pt.x, thumb_pt.y - idx_pt.y) / palm
                    self.current_pinch_dist = dist
                    is_pinching = dist < config.get("pinch_threshold", 0.065)

                    frame = self.tracker.draw_skeleton(frame, hand, is_pinching=is_pinching)

                    # Update step 3 meter
                    if self.step == 3 and hasattr(self, "lbl_pinch_meter") and self.lbl_pinch_meter:
                        if is_pinching:
                            self.lbl_pinch_meter.configure(text="Pinch Status: CLICKED!", fg="#00ff88")
                        else:
                            self.lbl_pinch_meter.configure(text=f"Pinch Dist: {dist:.3f}", fg="#a0a0c0")

                # Resize to fit preview panel
                display_frame = cv2.resize(frame, (380, 480))
                rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self.lbl_cam.configure(image=img)
                self.lbl_cam.image = img

        if self.root:
            self.root.after(33, self._video_loop)

    def _next_step(self) -> None:
        if self.step < 4:
            self.step += 1
            self._render_step_controls()
        else:
            self._finish_calibration()

    def _prev_step(self) -> None:
        if self.step > 1:
            self.step -= 1
            self._render_step_controls()

    def _finish_calibration(self) -> None:
        # Calculate reach bounding box if corners were captured
        c = self.captured_corners
        if all(c.values()):
            left = min(c["top_left"][0], c["bottom_left"][0])
            right = max(c["top_right"][0], c["bottom_right"][0])
            top = min(c["top_left"][1], c["top_right"][1])
            bottom = max(c["bottom_left"][1], c["bottom_right"][1])
            config.set("reach_left", max(0.05, min(0.4, left)))
            config.set("reach_right", max(0.6, min(0.95, right)))
            config.set("reach_top", max(0.05, min(0.4, top)))
            config.set("reach_bottom", max(0.6, min(0.95, bottom)))

        config.set("initial_setup_completed", True)
        config.save()
        messagebox.showinfo("Setup Complete", "Handsfree is calibrated and running in your system tray!")
        self._on_close()

    def _on_close(self) -> None:
        self.is_running = False
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
        if self.on_complete:
            self.on_complete()
