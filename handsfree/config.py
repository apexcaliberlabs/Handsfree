import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    # Camera settings
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 480,
    "camera_fps": 30,
    "flip_horizontal": True,

    # Filter & Tracking parameters (1-Euro Filter)
    "smoothing_min_cutoff": 1.2,
    "smoothing_beta": 0.04,
    "smoothing_d_cutoff": 1.0,

    # Screen reach calibration (bounding rectangle in camera coordinates)
    "reach_left": 0.18,
    "reach_top": 0.18,
    "reach_right": 0.82,
    "reach_bottom": 0.82,

    # Mouse & Gesture thresholds
    "sensitivity_x": 1.2,
    "sensitivity_y": 1.2,
    "pinch_threshold": 0.065,         # Relative to palm scale (distance thumb-index)
    "pinch_release_threshold": 0.09,   # Hysteresis release threshold
    "scroll_activation_distance": 0.065, # Index to middle fingertip distance for scroll
    "scroll_speed": 1.4,
    "click_hold_drag_ms": 320,        # Pinch held longer than this becomes drag

    # Meta Quest-style glowing cursor overlay
    "cursor_color": "#00e5ff",        # Luminous cyan / electric blue
    "cursor_click_color": "#00ffaa",  # Glowing emerald on pinch
    "cursor_scroll_color": "#ffaa00", # Glowing amber in scroll mode
    "cursor_radius": 10,
    "cursor_glow_radius": 24,
    "cursor_glow_opacity": 0.85,

    # Application preferences
    "run_at_startup": False,
    "show_camera_hud": False,
    "initial_setup_completed": False
}


class ConfigManager:
    """Manages application settings stored in AppData/Local/Handsfree."""

    def __init__(self) -> None:
        local_app_data = os.getenv("LOCALAPPDATA", str(Path.home()))
        self.config_dir = Path(local_app_data) / "Handsfree"
        self.config_file = self.config_dir / "config.json"
        self.data: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        """Load settings from config.json, merging with defaults."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self.data.update(saved)
        except Exception:
            # Fall back to defaults if corrupted
            self.data = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save settings to config.json."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[Handsfree Config] Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)
        self.save()


# Global shared instance
config = ConfigManager()
