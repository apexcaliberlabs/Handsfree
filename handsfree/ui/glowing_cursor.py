import ctypes
from ctypes import wintypes
import math
import threading
import time
import tkinter as tk
from typing import Optional, Tuple
from handsfree.config import config

# Win32 Window Styles
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

user32 = ctypes.windll.user32


class GlowingCursorOverlay:
    """
    Meta Quest controller-free style glowing cursor overlay.
    Renders a luminous, pulsing glowing neon dot that floats at the cursor location.
    The window is completely click-through, transparent, topmost, and non-activating.
    """

    def __init__(self) -> None:
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.hwnd: Optional[int] = None

        self.running: bool = False
        self.thread: Optional[threading.Thread] = None

        # Cursor state
        self.target_x: int = 100
        self.target_y: int = 100
        self.current_x: float = 100.0
        self.current_y: float = 100.0
        self.mode: str = "MOVE"
        self.pinch_factor: float = 0.0
        self.visible: bool = True

        # Dimensions of overlay badge centered on cursor
        self.size = 120
        self.half_size = self.size // 2

    def start(self) -> None:
        """Starts the overlay UI loop in a background thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_ui, daemon=True, name="HandsfreeCursorOverlay")
        self.thread.start()

    def _run_ui(self) -> None:
        self.root = tk.Tk()
        self.root.title("Handsfree_Cursor_Overlay")
        self.root.overrideredirect(True)

        # Transparent background key color
        trans_key = "#000001"
        self.root.configure(bg=trans_key)
        self.root.wm_attributes("-transparentcolor", trans_key)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.95)

        self.canvas = tk.Canvas(
            self.root,
            width=self.size,
            height=self.size,
            bg=trans_key,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Retrieve HWND and apply Win32 click-through styles
        self.root.update_idletasks()
        try:
            self.hwnd = user32.GetParent(self.root.winfo_id())
            if not self.hwnd:
                self.hwnd = self.root.winfo_id()

            ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
            ex_style |= (WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST)
            user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style)

            # Ensure stays strictly on top without taking focus
            user32.SetWindowPos(
                self.hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
        except Exception as e:
            print(f"[Handsfree Overlay] Window styling error: {e}")

        # Start animation render loop
        self._render_loop()
        self.root.mainloop()

    def update_position(self, x: int, y: int, mode: str = "MOVE", pinch_factor: float = 0.0) -> None:
        """Called by tracker thread to update target position and gesture mode."""
        self.target_x = x
        self.target_y = y
        self.mode = mode
        self.pinch_factor = max(0.0, min(1.0, pinch_factor))

    def set_visible(self, visible: bool) -> None:
        self.visible = visible

    def _render_loop(self) -> None:
        if not self.running or not self.root:
            return

        if self.visible:
            # Smooth follow toward target
            self.current_x += (self.target_x - self.current_x) * 0.75
            self.current_y += (self.target_y - self.current_y) * 0.75

            # Center overlay window at current coordinate
            win_x = int(self.current_x - self.half_size)
            win_y = int(self.current_y - self.half_size)
            self.root.geometry(f"{self.size}x{self.size}+{win_x}+{win_y}")

            self._draw_glowing_dot()
        else:
            if self.canvas:
                self.canvas.delete("all")

        # ~60 FPS update interval
        self.root.after(16, self._render_loop)

    def _draw_glowing_dot(self) -> None:
        if not self.canvas:
            return
        self.canvas.delete("all")

        cx = self.half_size
        cy = self.half_size

        # Colors based on gesture mode (Meta Quest styling)
        base_color = config.get("cursor_color", "#00e5ff")        # Cyan
        click_color = config.get("cursor_click_color", "#00ffaa")  # Emerald
        scroll_color = config.get("cursor_scroll_color", "#ffaa00") # Amber/Orange

        if self.mode in ("PINCH", "CLICKED", "DRAGGING"):
            theme_color = click_color
        elif self.mode == "SCROLL":
            theme_color = scroll_color
        else:
            theme_color = base_color

        # Radii with pinch contraction effect
        # When user pinches, outer aura contracts inward, giving physical tactile feedback
        pinch_squeeze = 1.0 - (self.pinch_factor * 0.45)
        core_r = max(4, int(config.get("cursor_radius", 9) * (0.85 if self.mode == "DRAGGING" else 1.0)))
        glow_r = max(core_r + 4, int(config.get("cursor_glow_radius", 24) * pinch_squeeze))

        # 1. Outer soft glow ring
        self.canvas.create_oval(
            cx - glow_r, cy - glow_r,
            cx + glow_r, cy + glow_r,
            outline=theme_color,
            width=2
        )

        # 2. Mid glow ring
        mid_r = int((glow_r + core_r) * 0.5)
        self.canvas.create_oval(
            cx - mid_r, cy - mid_r,
            cx + mid_r, cy + mid_r,
            outline=theme_color,
            width=3
        )

        # 3. Solid center orb
        self.canvas.create_oval(
            cx - core_r, cy - core_r,
            cx + core_r, cy + core_r,
            fill=theme_color,
            outline="#ffffff",
            width=1
        )

        # 4. Tiny luminous center highlight dot
        self.canvas.create_oval(
            cx - 2, cy - 2,
            cx + 2, cy + 2,
            fill="#ffffff",
            outline="#ffffff"
        )

        # Mode-specific visual indicators
        if self.mode == "SCROLL":
            # Draw vertical scroll arrows
            arrow_offset = glow_r + 6
            # Up arrow
            self.canvas.create_line(cx, cy - arrow_offset, cx, cy - arrow_offset + 5, fill=theme_color, width=2)
            self.canvas.create_line(cx - 3, cy - arrow_offset + 3, cx, cy - arrow_offset, fill=theme_color, width=2)
            self.canvas.create_line(cx + 3, cy - arrow_offset + 3, cx, cy - arrow_offset, fill=theme_color, width=2)
            # Down arrow
            self.canvas.create_line(cx, cy + arrow_offset, cx, cy + arrow_offset - 5, fill=theme_color, width=2)
            self.canvas.create_line(cx - 3, cy + arrow_offset - 3, cx, cy + arrow_offset, fill=theme_color, width=2)
            self.canvas.create_line(cx + 3, cy + arrow_offset - 3, cx, cy + arrow_offset, fill=theme_color, width=2)
        elif self.mode == "DRAGGING":
            # Expanding pulse ring to show held state
            drag_r = glow_r + 4
            self.canvas.create_oval(
                cx - drag_r, cy - drag_r,
                cx + drag_r, cy + drag_r,
                outline=theme_color,
                dash=(2, 2),
                width=1
            )

    def stop(self) -> None:
        self.running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass
            self.root = None
