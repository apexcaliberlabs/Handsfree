import ctypes
from ctypes import wintypes
import sys
from typing import Tuple

user32 = ctypes.windll.user32

# Set DPI awareness for exact pixel coordinates on modern Windows displays
try:
    # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

# Win32 Mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77


class MouseController:
    """High-performance Windows mouse controller via direct user32 API calls."""

    def __init__(self) -> None:
        self.is_left_down: bool = False
        self.is_right_down: bool = False
        self.scroll_accumulator: float = 0.0

    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """Returns primary display resolution (width, height) in pixels."""
        w = user32.GetSystemMetrics(SM_CXSCREEN)
        h = user32.GetSystemMetrics(SM_CYSCREEN)
        return max(1, w), max(1, h)

    @staticmethod
    def get_virtual_screen_bounds() -> Tuple[int, int, int, int]:
        """Returns (left, top, width, height) of total virtual multi-monitor workspace."""
        left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if width <= 0 or height <= 0:
            width, height = MouseController.get_screen_size()
            left, top = 0, 0
        return left, top, width, height

    @staticmethod
    def get_cursor_pos() -> Tuple[int, int]:
        """Get current Windows OS cursor coordinates."""
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_to(self, x: int, y: int) -> None:
        """Moves cursor directly to integer pixel coordinates (x, y)."""
        user32.SetCursorPos(int(x), int(y))

    def mouse_down(self, button: str = "left") -> None:
        """Presses and holds mouse button down."""
        if button == "left" and not self.is_left_down:
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            self.is_left_down = True
        elif button == "right" and not self.is_right_down:
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            self.is_right_down = True

    def mouse_up(self, button: str = "left") -> None:
        """Releases pressed mouse button."""
        if button == "left" and self.is_left_down:
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.is_left_down = False
        elif button == "right" and self.is_right_down:
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            self.is_right_down = False

    def click(self, button: str = "left") -> None:
        """Fires an atomic click down and up."""
        if button == "left":
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.is_left_down = False
        elif button == "right":
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            self.is_right_down = False

    def scroll(self, delta_amount: float) -> None:
        """
        Scroll wheel action.
        delta_amount > 0 scrolls up, delta_amount < 0 scrolls down.
        Accumulates small movements for silky-smooth response.
        """
        self.scroll_accumulator += delta_amount * WHEEL_DELTA
        steps = int(self.scroll_accumulator / WHEEL_DELTA)
        if steps != 0:
            user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, steps * WHEEL_DELTA, 0)
            self.scroll_accumulator -= steps * WHEEL_DELTA

    def release_all(self) -> None:
        """Failsafe release of any held mouse buttons."""
        if self.is_left_down:
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.is_left_down = False
        if self.is_right_down:
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            self.is_right_down = False
        self.scroll_accumulator = 0.0
