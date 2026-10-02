import os
import sys
import threading
from pathlib import Path
from typing import Callable, Optional
from PIL import Image
import pystray

from handsfree.config import config
from handsfree.utils.autostart import is_run_at_startup_enabled, set_run_at_startup


class SystemTrayApp:
    """
    Windows 11 System Tray icon and context menu controller for Handsfree.
    """

    def __init__(
        self,
        on_toggle_active: Callable[[bool], None],
        on_open_calibration: Callable[[], None],
        on_toggle_hud: Callable[[bool], None],
        on_exit: Callable[[], None]
    ) -> None:
        self.on_toggle_active = on_toggle_active
        self.on_open_calibration = on_open_calibration
        self.on_toggle_hud = on_toggle_hud
        self.on_exit = on_exit

        self.is_active: bool = True
        self.is_hud_open: bool = False
        self.icon: Optional[pystray.Icon] = None
        self.thread: Optional[threading.Thread] = None

    def _get_icon_image(self) -> Image.Image:
        candidates = [
            getattr(sys, "_MEIPASS", "") and Path(getattr(sys, "_MEIPASS")) / "handsfree" / "ui" / "assets" / "handsfree.png",
            getattr(sys, "frozen", False) and Path(sys.executable).parent / "_internal" / "handsfree" / "ui" / "assets" / "handsfree.png",
            getattr(sys, "frozen", False) and Path(sys.executable).parent / "handsfree" / "ui" / "assets" / "handsfree.png",
            Path(__file__).resolve().parent / "assets" / "handsfree.png",
            Path.cwd() / "handsfree" / "ui" / "assets" / "handsfree.png"
        ]
        for c in candidates:
            if c and os.path.exists(str(c)):
                return Image.open(str(c))
        # Fallback 32x32 colored circle
        return Image.new("RGBA", (32, 32), (16, 20, 32, 255))

    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                "Handsfree: Active",
                self._handle_toggle_active,
                checked=lambda item: self.is_active
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Calibration Wizard...",
                self._handle_calibration
            ),
            pystray.MenuItem(
                "Live Camera HUD",
                self._handle_toggle_hud,
                checked=lambda item: self.is_hud_open
            ),
            pystray.MenuItem(
                "Run at Windows Startup",
                self._handle_toggle_startup,
                checked=lambda item: is_run_at_startup_enabled()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "About Handsfree",
                self._handle_about
            ),
            pystray.MenuItem(
                "Exit Handsfree",
                self._handle_exit
            )
        )

    def _handle_toggle_active(self, icon, item) -> None:
        self.is_active = not self.is_active
        self.on_toggle_active(self.is_active)
        if self.icon:
            self.icon.title = f"Handsfree ({'Active' if self.is_active else 'Paused'})"
            self.icon.update_menu()

    def _handle_calibration(self, icon, item) -> None:
        self.on_open_calibration()

    def _handle_toggle_hud(self, icon, item) -> None:
        self.is_hud_open = not self.is_hud_open
        self.on_toggle_hud(self.is_hud_open)
        if self.icon:
            self.icon.update_menu()

    def _handle_toggle_startup(self, icon, item) -> None:
        current = is_run_at_startup_enabled()
        new_state = not current
        set_run_at_startup(new_state)
        config.set("run_at_startup", new_state)
        config.save()
        if self.icon:
            self.icon.update_menu()

    def _handle_about(self, icon, item) -> None:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            "Handsfree v1.0.0\nCreated by Apex Caliber Labs\n\n"
            "Touchless computer vision mouse control.\n"
            "Controls:\n"
            " - Move pointer: Index finger\n"
            " - Click / Drag: Pinch thumb and index\n"
            " - Scroll: Index & middle finger together + vertical swipe",
            "About Handsfree",
            0x40 | 0x10000 # MB_ICONINFORMATION | MB_SETFOREGROUND
        )

    def _handle_exit(self, icon, item) -> None:
        if self.icon:
            self.icon.stop()
        self.on_exit()

    def start(self) -> None:
        """Runs the tray icon event loop in a background thread."""
        img = self._get_icon_image()
        self.icon = pystray.Icon(
            name="Handsfree",
            icon=img,
            title="Handsfree by Apex Caliber Labs (Active)",
            menu=self._create_menu()
        )
        self.thread = threading.Thread(target=self.icon.run, daemon=True, name="HandsfreeTrayThread")
        self.thread.start()

    def stop(self) -> None:
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
