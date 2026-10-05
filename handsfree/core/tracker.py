import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode
)

# Landmark connections for hand skeleton visualization
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (0, 9), (9, 10), (10, 11), (11, 12),
    # Ring finger
    (0, 13), (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm knuckles
    (5, 9), (9, 13), (13, 17)
]


class HandTracker:
    """MediaPipe Tasks HandLandmarker wrapper for real-time tracking."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        if model_path is None:
            candidates = [
                # Frozen PyInstaller onefile temp dir
                getattr(sys, "_MEIPASS", "") and Path(getattr(sys, "_MEIPASS")) / "handsfree" / "models" / "hand_landmarker.task",
                # Frozen PyInstaller onedir internal folder
                getattr(sys, "frozen", False) and Path(sys.executable).parent / "_internal" / "handsfree" / "models" / "hand_landmarker.task",
                getattr(sys, "frozen", False) and Path(sys.executable).parent / "handsfree" / "models" / "hand_landmarker.task",
                # Normal source development tree
                Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task",
                Path.cwd() / "handsfree" / "models" / "hand_landmarker.task",
            ]
            for c in candidates:
                if c and os.path.exists(str(c)):
                    model_path = str(c)
                    break

        self.model_path = model_path or ""
        if not self.model_path or not os.path.exists(self.model_path):
            raise FileNotFoundError(f"MediaPipe model file missing: {self.model_path}")

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: np.ndarray) -> Tuple[List[Any], List[str]]:
        """
        Processes BGR image frame.
        Returns:
            multi_hand_landmarks: List of landmark lists (each with 21 points)
            multi_handedness: List of strings ("Left" or "Right")
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        result = self.landmarker.detect(mp_image)

        hands_landmarks = []
        handedness_list = []

        if result.hand_landmarks:
            for i, hand in enumerate(result.hand_landmarks):
                hands_landmarks.append(hand)
                h_name = "Right"
                if result.handedness and i < len(result.handedness) and result.handedness[i]:
                    h_name = result.handedness[i][0].category_name
                handedness_list.append(h_name)

        return hands_landmarks, handedness_list

    @staticmethod
    def draw_skeleton(
        frame: np.ndarray,
        landmarks: List[Any],
        is_pinching: bool = False,
        is_scrolling: bool = False
    ) -> np.ndarray:
        """
        Draws high-tech luminous cyberpunk skeleton & landmarks on image.
        """
        h, w, _ = frame.shape
        coords = [(int(pt.x * w), int(pt.y * h)) for pt in landmarks]

        # Neon line colors: Cyan normally, Orange if scrolling, Green if pinching
        line_color = (255, 230, 0) # BGR: Cyan-ish
        if is_pinching:
            line_color = (100, 255, 100) # Bright green
        elif is_scrolling:
            line_color = (0, 180, 255) # Bright orange/gold

        # Draw bones
        for start_idx, end_idx in HAND_CONNECTIONS:
            pt1 = coords[start_idx]
            pt2 = coords[end_idx]
            cv2.line(frame, pt1, pt2, line_color, 2, cv2.LINE_AA)

        # Draw joints
        for idx, (x, y) in enumerate(coords):
            # Special highlighting for fingertips: Thumb (4), Index (8), Middle (12)
            if idx in (4, 8):
                cv2.circle(frame, (x, y), 7, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (x, y), 9, line_color, 2, cv2.LINE_AA)
            elif idx == 12:
                cv2.circle(frame, (x, y), 6, (0, 255, 255) if is_scrolling else (200, 200, 200), -1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (x, y), 3, (180, 180, 180), -1, cv2.LINE_AA)

        return frame
