import math
import time
from typing import Any, Dict, List, Optional, Tuple
from handsfree.config import config
from handsfree.core.filter import PointFilter2D
from handsfree.core.mouse import MouseController


def distance_3d(p1: Any, p2: Any) -> float:
    """Euclidean distance between two landmarks with x, y, (and optional z)."""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = getattr(p1, 'z', 0.0) - getattr(p2, 'z', 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def distance_2d(p1: Any, p2: Any) -> float:
    """Euclidean 2D distance between two landmarks."""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return math.hypot(dx, dy)


class GestureEngine:
    """
    Recognizes hand gestures modeled after Meta Quest controller-free tracking:
    - Index finger pointing & navigation
    - Pinch thumb & index for click / click-and-drag
    - Two-finger (index + middle) together vertical swipe for scrolling
    - Thumb & middle pinch for secondary / right-click
    """

    def __init__(self, mouse: Optional[MouseController] = None) -> None:
        self.mouse = mouse or MouseController()
        self.screen_w, self.screen_h = self.mouse.get_screen_size()
        self.filter = PointFilter2D(
            min_cutoff=config.get("smoothing_min_cutoff", 1.2),
            beta=config.get("smoothing_beta", 0.04),
            d_cutoff=config.get("smoothing_d_cutoff", 1.0)
        )

        # Pinch tracking state
        self.is_pinching: bool = False
        self.is_dragging: bool = False
        self.pinch_start_time: float = 0.0
        self.last_pinch_distance: float = 1.0

        # Scroll tracking state
        self.is_scrolling: bool = False
        self.last_scroll_y: Optional[float] = None

        # Right click pinch tracking
        self.is_right_pinching: bool = False

        # Previous frame timestamp
        self.last_frame_time: float = time.perf_counter()

    def update_screen_size(self) -> None:
        self.screen_w, self.screen_h = self.mouse.get_screen_size()

    def reset_filters(self) -> None:
        self.filter.reset()
        self.is_pinching = False
        self.is_dragging = False
        self.is_scrolling = False
        self.is_right_pinching = False
        self.last_scroll_y = None
        self.mouse.release_all()

    def process_hand(
        self,
        landmarks: List[Any],
        handedness: str = "Right"
    ) -> Dict[str, Any]:
        """
        Processes 21 landmarks of an active hand.
        MediaPipe landmark reference:
          0: WRIST
          4: THUMB_TIP
          5: INDEX_FINGER_MCP
          8: INDEX_FINGER_TIP
          9: MIDDLE_FINGER_MCP
          12: MIDDLE_FINGER_TIP
          16: RING_FINGER_TIP
          20: PINKY_TIP
        """
        now = time.perf_counter()
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        index_mcp = landmarks[5]
        index_tip = landmarks[8]
        middle_mcp = landmarks[9]
        middle_tip = landmarks[12]

        # Palm scale (distance from wrist to middle MCP) for scale invariance
        palm_scale = distance_2d(wrist, middle_mcp)
        if palm_scale < 1e-4:
            palm_scale = 0.2

        # 1. Normalized pinch distances
        dist_thumb_index = distance_2d(thumb_tip, index_tip) / palm_scale
        dist_thumb_middle = distance_2d(thumb_tip, middle_tip) / palm_scale
        dist_index_middle = distance_2d(index_tip, middle_tip) / palm_scale

        self.last_pinch_distance = dist_thumb_index
        pinch_thresh = config.get("pinch_threshold", 0.065)
        release_thresh = config.get("pinch_release_threshold", 0.09)
        scroll_dist_thresh = config.get("scroll_activation_distance", 0.065)
        drag_hold_ms = config.get("click_hold_drag_ms", 320)

        # 2. Check Two-Finger Scroll Mode (Index + Middle extended together)
        # Distance between index tip and middle tip is small, and thumb is not pinching
        is_two_finger_together = (dist_index_middle < scroll_dist_thresh) and (dist_thumb_index > release_thresh)

        # Mode determination
        current_mode = "MOVE"
        scroll_delta = 0.0

        # Map index tip coordinates through reach calibration bounding box
        reach_l = config.get("reach_left", 0.18)
        reach_t = config.get("reach_top", 0.18)
        reach_r = config.get("reach_right", 0.82)
        reach_b = config.get("reach_bottom", 0.82)

        # Clamp normalized coordinates to reach box
        norm_x = (index_tip.x - reach_l) / max(0.01, (reach_r - reach_l))
        norm_y = (index_tip.y - reach_t) / max(0.01, (reach_b - reach_t))

        # Clamp to 0..1
        clamped_x = max(0.0, min(1.0, norm_x))
        clamped_y = max(0.0, min(1.0, norm_y))

        # Map to screen pixels
        raw_screen_x = clamped_x * self.screen_w
        raw_screen_y = clamped_y * self.screen_h

        # Apply 1-Euro Filter for silky smooth, jitter-free cursor position
        smooth_x, smooth_y = self.filter.filter(raw_screen_x, raw_screen_y, now)
        target_x = int(round(smooth_x))
        target_y = int(round(smooth_y))

        # Clamp to screen dimensions
        target_x = max(0, min(self.screen_w - 1, target_x))
        target_y = max(0, min(self.screen_h - 1, target_y))

        # --- SCROLL GESTURE PROCESSING ---
        if is_two_finger_together:
            current_mode = "SCROLL"
            self.is_scrolling = True
            two_finger_mid_y = (index_tip.y + middle_tip.y) * 0.5

            if self.last_scroll_y is not None:
                dy = two_finger_mid_y - self.last_scroll_y
                # Sensitivity threshold for scroll to prevent accidental micro-jitter
                if abs(dy) > 0.004:
                    # Swipe up (negative dy) scrolls up; swipe down scrolls down
                    scroll_speed = config.get("scroll_speed", 1.4)
                    scroll_delta = -dy * scroll_speed * 12.0
                    self.mouse.scroll(scroll_delta)
                    self.last_scroll_y = two_finger_mid_y
            else:
                self.last_scroll_y = two_finger_mid_y
        else:
            self.is_scrolling = False
            self.last_scroll_y = None

        # --- PINCH (CLICK & DRAG) GESTURE PROCESSING ---
        if not self.is_scrolling:
            # Check left click pinch (Thumb + Index)
            if not self.is_pinching:
                if dist_thumb_index < pinch_thresh:
                    self.is_pinching = True
                    self.pinch_start_time = now
                    current_mode = "PINCH"
            else:
                # Currently pinching
                pinch_duration = (now - self.pinch_start_time) * 1000.0
                if dist_thumb_index > release_thresh:
                    # Released pinch!
                    self.is_pinching = False
                    if self.is_dragging:
                        self.mouse.mouse_up("left")
                        self.is_dragging = False
                        current_mode = "MOVE"
                    else:
                        # Quick pinch click
                        self.mouse.click("left")
                        current_mode = "CLICKED"
                else:
                    # Still pinched
                    if pinch_duration >= drag_hold_ms:
                        if not self.is_dragging:
                            self.mouse.mouse_down("left")
                            self.is_dragging = True
                        current_mode = "DRAGGING"
                    else:
                        current_mode = "PINCH"

            # Check right click pinch (Thumb + Middle)
            if not self.is_pinching and not self.is_dragging:
                if not self.is_right_pinching:
                    if dist_thumb_middle < pinch_thresh:
                        self.is_right_pinching = True
                else:
                    if dist_thumb_middle > release_thresh:
                        self.is_right_pinching = False
                        self.mouse.click("right")
                        current_mode = "RIGHT_CLICK"

        # Update physical cursor position
        self.mouse.move_to(target_x, target_y)

        # Pinch depth factor (0.0 = completely wide, 1.0 = fully pinched together)
        pinch_factor = max(0.0, min(1.0, 1.0 - (dist_thumb_index / max(0.01, release_thresh * 1.8))))

        return {
            "mode": current_mode,
            "cursor_x": target_x,
            "cursor_y": target_y,
            "pinch_distance": dist_thumb_index,
            "pinch_factor": pinch_factor,
            "is_dragging": self.is_dragging,
            "is_scrolling": self.is_scrolling,
            "scroll_delta": scroll_delta,
            "handedness": handedness,
            "palm_scale": palm_scale,
            "index_tip_raw": (index_tip.x, index_tip.y)
        }
