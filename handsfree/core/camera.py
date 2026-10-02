import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np
from handsfree.config import config


class CameraFeed:
    """
    High-performance webcam capture thread using OpenCV with DirectShow backend.
    Ensures zero-latency frame delivery by always maintaining the freshest frame.
    """

    def __init__(self, camera_index: Optional[int] = None) -> None:
        self.camera_index = camera_index if camera_index is not None else config.get("camera_index", 0)
        self.width = config.get("camera_width", 640)
        self.height = config.get("camera_height", 480)
        self.fps = config.get("camera_fps", 30)
        self.flip_horizontal = config.get("flip_horizontal", True)

        self.cap: Optional[cv2.VideoCapture] = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        self.latest_frame: Optional[np.ndarray] = None
        self.frame_time: float = 0.0
        self.is_connected: bool = False

    def open_camera(self) -> bool:
        """Opens camera using DirectShow on Windows with fallback."""
        try:
            # Try DirectShow first on Windows for instant initialization
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                print(f"[Handsfree Camera] Failed to open camera index {self.camera_index}")
                self.is_connected = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer for zero latency

            self.is_connected = True
            return True
        except Exception as e:
            print(f"[Handsfree Camera] Error initializing camera: {e}")
            self.is_connected = False
            return False

    def start(self) -> bool:
        """Starts the capture worker thread."""
        if self.running:
            return True

        if not self.open_camera():
            return False

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True, name="HandsfreeCameraThread")
        self.thread.start()
        return True

    def _capture_loop(self) -> None:
        """Dedicated background capture loop."""
        while self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Mirror frame horizontally so user movement naturally matches screen
            if self.flip_horizontal:
                frame = cv2.flip(frame, 1)

            with self.lock:
                self.latest_frame = frame
                self.frame_time = time.perf_counter()

        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_connected = False

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], float]:
        """Returns the latest captured frame and its timestamp."""
        with self.lock:
            if self.latest_frame is None:
                return None, 0.0
            return self.latest_frame.copy(), self.frame_time

    def stop(self) -> None:
        """Stops the camera thread safely."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        self.thread = None
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.is_connected = False
