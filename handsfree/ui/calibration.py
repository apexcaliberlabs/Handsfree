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

    def __init__(self, master: Optional[tk.Misc] = None, camera_feed=None, on_complete=None) -> None:
        self.master = master
        self.camera_feed = camera_feed
        self.on_complete = on_complete

        self.root: Optional[tk.Toplevel | tk.Tk] = None
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
        """Launches calibration window."""
        if self.is_running and self.root:
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                return
            except Exception:
                pass

        if self.master is not None:
            self._setup_wizard(is_toplevel=True)
        else:
            threading.Thread(target=self._run_standalone, daemon=True, name="HandsfreeCalibration").start()

    def _setup_wizard(self, is_toplevel: bool = False) -> None:
        if is_toplevel and self.master:
            self.root = tk.Toplevel(self.master)
        else:
            self.root = tk.Tk()

        self.root.title("Handsfree - Guided Setup & Calibration (Apex Caliber Labs)")
        self.root.geometry("880x660")
        self.root.minsize(800, 580)
        self.root.resizable(True, True)
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
        self._activate_webcam_ui()
        self._video_loop()

        # Bring window to front
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(lambda: self.root.attributes("-topmost", False) if self.root else None)
        self.root.focus_force()

    def _run_standalone(self) -> None:
        self._setup_wizard(is_toplevel=False)
        if self.root:
            self.root.mainloop()

    def _build_ui(self) -> None:
        # 1. Header banner (Top)
        header = tk.Frame(self.root, bg="#161622", height=55)
        header.pack(fill="x", side="top")

        lbl_app = tk.Label(
            header,
            text="HANDSFREE",
            font=("Segoe UI", 14, "bold"),
            fg="#00e5ff",
            bg="#161622"
        )
        lbl_app.pack(side="left", padx=20, pady=10)

        lbl_sub = tk.Label(
            header,
            text="by Apex Caliber Labs  |  Guided Setup & Hardware Calibration",
            font=("Segoe UI", 10),
            fg="#9090aa",
            bg="#161622"
        )
        lbl_sub.pack(side="left", pady=14)

        # 2. Footer navigation bar (Packed at BOTTOM FIRST so it is NEVER cut off)
        footer = tk.Frame(self.root, bg="#161622", height=60)
        footer.pack(fill="x", side="bottom")

        self.btn_prev = tk.Button(
            footer, text="< Back", font=("Segoe UI", 10),
            bg="#2a2a3c", fg="#ffffff", activebackground="#3a3a4c",
            command=self._prev_step, width=11, relief="flat", cursor="hand2"
        )
        self.btn_prev.pack(side="left", padx=20, pady=12)

        self.btn_next = tk.Button(
            footer, text="Next Step >", font=("Segoe UI", 10, "bold"),
            bg="#00bcd4", fg="#000000", activebackground="#00e5ff",
            command=self._next_step, width=14, relief="flat", cursor="hand2"
        )
        self.btn_next.pack(side="right", padx=20, pady=12)

        self.btn_camera = tk.Button(
            footer, text="📷 Turn On Webcam", font=("Segoe UI", 9, "bold"),
            bg="#1f2c3d", fg="#00e5ff", activebackground="#293b52", activeforeground="#ffffff",
            command=self._activate_webcam_ui, padx=14, relief="flat", cursor="hand2"
        )
        self.btn_camera.pack(side="right", padx=(0, 10), pady=12)

        # 3. Main content container (Occupies the area between header and footer)
        content = tk.Frame(self.root, bg="#0f0f14")
        content.pack(fill="both", expand=True, padx=18, pady=12)

        # Left column: live camera preview
        cam_panel = tk.Frame(content, bg="#161622", bd=1, relief="solid")
        cam_panel.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.lbl_cam = tk.Label(cam_panel, bg="#000000")
        self.lbl_cam.pack(fill="both", expand=True, padx=4, pady=4)

        # Right column: step instructions & guided interactive controls
        self.control_panel = tk.Frame(content, bg="#161622", width=340)
        self.control_panel.pack(side="right", fill="both", padx=(0, 0))
        self.control_panel.pack_propagate(False)

        self._render_step_controls()

    def _render_step_controls(self) -> None:
        for widget in self.control_panel.winfo_children():
            widget.destroy()

        p = self.control_panel

        if self.step == 1:
            # Step 1: Camera Detection & Real-time Hand Recognition
            tk.Label(p, text="Step 1 of 4", font=("Segoe UI", 9, "bold"), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=16, pady=(16, 2))
            tk.Label(p, text="Hand Recognition", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=16, pady=(0, 8))

            desc = (
                "Ensure your laptop webcam is turned on.\n\n"
                "Hold either hand up in front of the screen (1 to 2 feet away).\n\n"
                "The AI will automatically lock onto your fingers with a luminous cyber-skeleton."
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d8", bg="#161622", justify="left", wraplength=300).pack(anchor="w", padx=16, pady=4)

            # Live Hand Status Box
            self.box_hand_status = tk.Frame(p, bg="#1a1a28", bd=1, relief="ridge")
            self.box_hand_status.pack(fill="x", padx=16, pady=16)

            self.lbl_hand_status = tk.Label(
                self.box_hand_status,
                text="WAITING FOR HAND...",
                font=("Segoe UI", 10, "bold"),
                fg="#ffaa00",
                bg="#1a1a28"
            )
            self.lbl_hand_status.pack(anchor="w", padx=12, pady=(10, 2))

            self.lbl_hand_details = tk.Label(
                self.box_hand_status,
                text="Raise your hand to the camera to proceed.",
                font=("Segoe UI", 8),
                fg="#9090aa",
                bg="#1a1a28"
            )
            self.lbl_hand_details.pack(anchor="w", padx=12, pady=(0, 10))

            tips = "💡 Tip: Make sure your room has decent lighting and your palm faces the webcam."
            tk.Label(p, text=tips, font=("Segoe UI", 8, "italic"), fg="#707090", bg="#161622", justify="left", wraplength=300).pack(anchor="w", padx=16, pady=8)

        elif self.step == 2:
            # Step 2: Comfortable Reach Calibration
            tk.Label(p, text="Step 2 of 4", font=("Segoe UI", 9, "bold"), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=16, pady=(16, 2))
            tk.Label(p, text="Reach Calibration", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=16, pady=(0, 8))

            desc = (
                "Calibrate your natural workspace so you can reach the entire screen comfortably without straining.\n\n"
                "Move your index finger to each corner and click Capture, or use Smart Defaults:"
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d8", bg="#161622", justify="left", wraplength=300).pack(anchor="w", padx=16, pady=4)

            # 2x2 Corner Grid
            grid = tk.Frame(p, bg="#161622")
            grid.pack(fill="x", padx=16, pady=10)

            corners = [
                ("top_left", "Top-Left", 0, 0),
                ("top_right", "Top-Right", 0, 1),
                ("bottom_left", "Bottom-Left", 1, 0),
                ("bottom_right", "Bottom-Right", 1, 1),
            ]

            self.corner_buttons = {}
            for key, label, r, c in corners:
                captured = self.captured_corners.get(key) is not None
                btn_text = f"✓ {label}" if captured else f"Capture {label}"
                btn_bg = "#0f3d2a" if captured else "#2d2d40"
                btn_fg = "#00e676" if captured else "#00e5ff"

                b = tk.Button(
                    grid, text=btn_text, font=("Segoe UI", 8, "bold"),
                    bg=btn_bg, fg=btn_fg, relief="flat", width=16, height=2,
                    command=lambda k=key, l=label: self._capture_corner(k, l)
                )
                b.grid(row=r, column=c, padx=4, pady=4)
                self.corner_buttons[key] = b

            btn_defaults = tk.Button(
                p, text="⚡ Use Smart Defaults (Recommended)", font=("Segoe UI", 9, "bold"),
                bg="#1e2a3a", fg="#00e5ff", relief="flat",
                command=self._apply_smart_defaults
            )
            btn_defaults.pack(fill="x", padx=16, pady=12)

        elif self.step == 3:
            # Step 3: Meta Quest Pinch-to-Click Tuning
            tk.Label(p, text="Step 3 of 4", font=("Segoe UI", 9, "bold"), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=16, pady=(16, 2))
            tk.Label(p, text="Pinch-to-Click", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=16, pady=(0, 6))

            desc = (
                "Pinch your thumb and index fingertip together to click, exactly like Meta Quest controller-free mode.\n\n"
                "Pinch and hold for half a second to Drag & Drop."
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d8", bg="#161622", justify="left", wraplength=300).pack(anchor="w", padx=16, pady=4)

            # Live Pinch Status Meter
            self.lbl_pinch_meter = tk.Label(
                p, text="Pinch Status: OPEN", font=("Segoe UI", 10, "bold"),
                fg="#a0a0c0", bg="#161622"
            )
            self.lbl_pinch_meter.pack(anchor="w", padx=16, pady=(10, 2))

            self.meter_progress = ttk.Progressbar(p, length=280, mode="determinate")
            self.meter_progress.pack(fill="x", padx=16, pady=(0, 10))

            # Sensitivity Slider
            tk.Label(p, text="Pinch Trigger Distance:", font=("Segoe UI", 9), fg="#ffffff", bg="#161622").pack(anchor="w", padx=16, pady=(4, 2))
            self.scale_pinch = tk.Scale(
                p, from_=0.03, to=0.12, resolution=0.005, orient="horizontal",
                bg="#161622", fg="#00e5ff", highlightthickness=0,
                command=lambda val: config.set("pinch_threshold", float(val))
            )
            self.scale_pinch.set(config.get("pinch_threshold", 0.065))
            self.scale_pinch.pack(fill="x", padx=16)

            # Practice Target Button
            self.btn_practice = tk.Button(
                p, text="🎯 Practice Target (Pinch Here)", font=("Segoe UI", 10, "bold"),
                bg="#2a2a40", fg="#00e5ff", relief="flat", height=2,
                command=self._on_practice_clicked
            )
            self.btn_practice.pack(fill="x", padx=16, pady=16)

        elif self.step == 4:
            # Step 4: Scrolling & Dynamics Practice
            tk.Label(p, text="Step 4 of 4", font=("Segoe UI", 9, "bold"), fg="#00e5ff", bg="#161622").pack(anchor="w", padx=16, pady=(16, 2))
            tk.Label(p, text="Scroll & Pointer Dynamics", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#161622").pack(anchor="w", padx=16, pady=(0, 6))

            desc = (
                "To scroll: Place index and middle fingers side-by-side and swipe up or down.\n\n"
                "Practice scrolling on the list below:"
            )
            tk.Label(p, text=desc, font=("Segoe UI", 9), fg="#c0c0d8", bg="#161622", justify="left", wraplength=300).pack(anchor="w", padx=16, pady=4)

            # Interactive Scroll Test Box
            scroll_frame = tk.Frame(p, bg="#161622")
            scroll_frame.pack(fill="x", padx=16, pady=6)

            scrollbar = tk.Scrollbar(scroll_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(scroll_frame, yscrollcommand=scrollbar.set, height=4, bg="#101018", fg="#00e5ff", selectbackground="#1e2a3a")
            for i in range(1, 21):
                listbox.insert("end", f"  Document Page {i}  •  Scroll Test")
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            # Dynamics controls
            tk.Label(p, text="Smoothing (1-Euro Filter):", font=("Segoe UI", 9), fg="#ffffff", bg="#161622").pack(anchor="w", padx=16, pady=(8, 2))
            scale_smooth = tk.Scale(
                p, from_=0.5, to=3.0, resolution=0.1, orient="horizontal",
                bg="#161622", fg="#00e5ff", highlightthickness=0,
                command=lambda val: config.set("smoothing_min_cutoff", float(val))
            )
            scale_smooth.set(config.get("smoothing_min_cutoff", 1.2))
            scale_smooth.pack(fill="x", padx=16)

            btn_finish = tk.Button(
                p, text="✓ Complete Setup & Start Handsfree", font=("Segoe UI", 10, "bold"),
                bg="#00e676", fg="#000000", activebackground="#69f0ae",
                relief="flat", height=2, command=self._finish_calibration
            )
            btn_finish.pack(fill="x", padx=16, pady=16)

    def _on_practice_clicked(self) -> None:
        self.practice_clicks += 1
        if hasattr(self, "btn_practice"):
            self.btn_practice.configure(
                text=f"🎯 Nice Pinch! ({self.practice_clicks} registered)",
                bg="#0f3d2a",
                fg="#00e676"
            )

    def _apply_smart_defaults(self) -> None:
        self.captured_corners = {
            "top_left": (0.18, 0.18),
            "top_right": (0.82, 0.18),
            "bottom_left": (0.18, 0.82),
            "bottom_right": (0.82, 0.82)
        }
        for key, btn in self.corner_buttons.items():
            label = key.replace("_", " ").title()
            btn.configure(text=f"✓ {label}", bg="#0f3d2a", fg="#00e676")
        messagebox.showinfo("Smart Reach Applied", "Optimal ergonomic reach boundaries applied successfully!")

    def _capture_corner(self, corner_name: str, label: str = "") -> None:
        self.captured_corners[corner_name] = self.current_index_coords
        if hasattr(self, "corner_buttons") and corner_name in self.corner_buttons:
            self.corner_buttons[corner_name].configure(
                text=f"✓ {label or corner_name}",
                bg="#0f3d2a",
                fg="#00e676"
            )

    def _activate_webcam_ui(self) -> None:
        """Explicitly activates the laptop's built-in webcam hardware."""
        if not self.camera_feed:
            from handsfree.core.camera import CameraFeed
            self.camera_feed = CameraFeed()

        if self.tracker is None:
            try:
                self.tracker = HandTracker()
            except Exception as e:
                print(f"[Calibration] Tracker init: {e}")

        if hasattr(self, "btn_camera"):
            self.btn_camera.configure(text="⏳ Connecting...", state="disabled")
            self.root.update_idletasks()

        success, msg = self.camera_feed.activate_builtin_webcam()

        if hasattr(self, "btn_camera"):
            if success:
                self.btn_camera.configure(
                    text="✓ Webcam Active",
                    bg="#0f3d2a",
                    fg="#00e676",
                    state="normal"
                )
            else:
                self.btn_camera.configure(
                    text="⚠️ Turn On Webcam",
                    bg="#3d1f1f",
                    fg="#ff5252",
                    state="normal"
                )

    def _video_loop(self) -> None:
        if not self.is_running or not self.root:
            return

        has_rendered = False
        if self.camera_feed is not None:
            frame, _ = self.camera_feed.get_latest_frame()
            if frame is not None:
                has_rendered = True
                if self.tracker is None:
                    try:
                        self.tracker = HandTracker()
                    except Exception as e:
                        print(f"[Calibration] Tracker warning: {e}")

                if self.tracker is not None:
                    hands, handedness = self.tracker.process_frame(frame)
                    is_pinching = False

                    if hands:
                        self.hand_detected = True
                        hand = hands[0]
                        self.hand_label = handedness[0] if handedness else "Right"

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

                        # Draw reach boundary guidelines
                        h_f, w_f, _ = frame.shape
                        rl = int(config.get("reach_left", 0.18) * w_f)
                        rt = int(config.get("reach_top", 0.18) * h_f)
                        rr = int(config.get("reach_right", 0.82) * w_f)
                        rb = int(config.get("reach_bottom", 0.82) * h_f)
                        cv2.rectangle(frame, (rl, rt), (rr, rb), (70, 70, 90), 1, cv2.LINE_AA)

                        # Update Step 1 Status
                        if self.step == 1 and hasattr(self, "lbl_hand_status") and self.lbl_hand_status:
                            self.lbl_hand_status.configure(
                                text=f"✓ {self.hand_label.upper()} HAND RECOGNIZED",
                                fg="#00e676"
                            )
                            self.lbl_hand_details.configure(
                                text="Tracking 21 finger landmarks in real time. Click 'Next Step >'!",
                                fg="#c0c0d8"
                            )

                        # Update Step 3 Pinch Meter
                        if self.step == 3:
                            if hasattr(self, "lbl_pinch_meter") and self.lbl_pinch_meter:
                                if is_pinching:
                                    self.lbl_pinch_meter.configure(text="Pinch Status: CLICKED! (ACTUATED)", fg="#00e676")
                                else:
                                    self.lbl_pinch_meter.configure(text=f"Pinch Distance: {dist:.3f} (Open)", fg="#00e5ff")
                            if hasattr(self, "meter_progress") and self.meter_progress:
                                pinch_pct = max(0, min(100, int((1.0 - (dist / 0.15)) * 100)))
                                self.meter_progress["value"] = pinch_pct

                    else:
                        self.hand_detected = False
                        if self.step == 1 and hasattr(self, "lbl_hand_status") and self.lbl_hand_status:
                            self.lbl_hand_status.configure(
                                text="SEARCHING FOR HAND...",
                                fg="#ffaa00"
                            )
                            self.lbl_hand_details.configure(
                                text="Raise your hand in front of the camera (1-2 ft away).",
                                fg="#9090aa"
                            )

                # Resize to fit preview panel comfortably (440x330 standard 4:3)
                display_frame = cv2.resize(frame, (440, 330))
                rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self.lbl_cam.configure(image=img)
                self.lbl_cam.image = img

        if not has_rendered:
            # Standby graphic when webcam is not active or starting
            standby = np.zeros((330, 440, 3), dtype=np.uint8)
            standby[:] = (22, 22, 30)
            cv2.putText(standby, "Webcam Standby", (110, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 229, 255), 2, cv2.LINE_AA)
            cv2.putText(standby, "Click 'Turn On Webcam' below", (85, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 195), 1, cv2.LINE_AA)
            cv2.putText(standby, "to activate device hardware", (100, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 160), 1, cv2.LINE_AA)
            img = ImageTk.PhotoImage(image=Image.fromarray(standby))
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
