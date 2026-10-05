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
        """Opens built-in webcam using DirectShow, Media Foundation, or auto-detect with multi-index scan."""
        # Release existing capture object if open
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        candidate_indices = [self.camera_index]
        for fallback_idx in [0, 1, 2]:
            if fallback_idx not in candidate_indices:
                candidate_indices.append(fallback_idx)

        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]

        for idx in candidate_indices:
            for api in backends:
                try:
                    cap = cv2.VideoCapture(idx, api)
                    if cap.isOpened():
                        # Verify hardware is actually streaming frames
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            self.cap = cap
                            self.camera_index = idx
                            config.set("camera_index", idx)

                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                            self.is_connected = True
                            print(f"[Handsfree Camera] Successfully activated built-in webcam on index {idx} (API: {api})")
                            return True
                    cap.release()
                except Exception:
                    pass

        print(f"[Handsfree Camera] Failed to open built-in webcam across tested indices {candidate_indices}")
        self.is_connected = False
        return False

    def activate_builtin_webcam(self) -> Tuple[bool, str]:
        """Explicitly activates or reactivates the on-device webcam hardware."""
        self.stop()
        time.sleep(0.1)

        success = self.start()
        if success:
            msg = f"Webcam Activated (Index {self.camera_index})"
            return True, msg
        else:
            msg = "Could not activate webcam. Check camera privacy settings in Windows."
            return False, msg

    def start(self) -> bool:
        """Starts the capture worker thread."""
        if self.running and self.is_connected:
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
