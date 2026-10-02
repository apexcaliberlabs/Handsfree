import math
import time
from typing import Optional, Tuple


class LowPassFilter:
    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha: float = alpha
        self.hat_x_prev: Optional[float] = None

    def reset(self) -> None:
        self.hat_x_prev = None

    def filter(self, x: float, alpha: Optional[float] = None) -> float:
        if alpha is not None:
            self.alpha = alpha
        if self.hat_x_prev is None:
            self.hat_x_prev = x
            return x
        hat_x = self.alpha * x + (1.0 - self.alpha) * self.hat_x_prev
        self.hat_x_prev = hat_x
        return hat_x

    def last_value(self) -> Optional[float]:
        return self.hat_x_prev


class OneEuroFilter1D:
    """
    1-Euro Filter 1-dimensional implementation.
    Reference: Casiez, G., Roussel, N. and Vogel, F. (2012).
    1 € Filter: A Simple Speed-based Low-pass Filter for Noisy Input in HCI.
    """

    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.05,
        d_cutoff: float = 1.0
    ) -> None:
        self.min_cutoff: float = min_cutoff
        self.beta: float = beta
        self.d_cutoff: float = d_cutoff
        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.t_prev: Optional[float] = None

    def reset(self) -> None:
        self.x_filter.reset()
        self.dx_filter.reset()
        self.t_prev = None

    def _alpha(self, rate: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate if rate > 0 else 0.001
        return 1.0 / (1.0 + tau / te)

    def filter(self, x: float, timestamp: Optional[float] = None) -> float:
        if timestamp is None:
            timestamp = time.perf_counter()

        if self.t_prev is None:
            self.t_prev = timestamp
            return self.x_filter.filter(x)

        dt = timestamp - self.t_prev
        self.t_prev = timestamp

        # Guard against zero or negative delta
        if dt <= 0.0:
            dt = 1e-4

        rate = 1.0 / dt

        # Estimate the current rate of change (derivative)
        prev_x = self.x_filter.last_value()
        dx = (x - prev_x) / dt if prev_x is not None else 0.0
        edx = self.dx_filter.filter(dx, self._alpha(rate, self.d_cutoff))

        # Dynamic cutoff frequency based on velocity
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self.x_filter.filter(x, self._alpha(rate, cutoff))


class PointFilter2D:
    """Filters 2D (x, y) coordinates with independent 1-Euro filters."""

    def __init__(
        self,
        min_cutoff: float = 1.2,
        beta: float = 0.04,
        d_cutoff: float = 1.0
    ) -> None:
        self.filter_x = OneEuroFilter1D(min_cutoff, beta, d_cutoff)
        self.filter_y = OneEuroFilter1D(min_cutoff, beta, d_cutoff)

    def reset(self) -> None:
        self.filter_x.reset()
        self.filter_y.reset()

    def update_params(self, min_cutoff: float, beta: float) -> None:
        self.filter_x.min_cutoff = min_cutoff
        self.filter_x.beta = beta
        self.filter_y.min_cutoff = min_cutoff
        self.filter_y.beta = beta

    def filter(self, x: float, y: float, timestamp: Optional[float] = None) -> Tuple[float, float]:
        if timestamp is None:
            timestamp = time.perf_counter()
        smooth_x = self.filter_x.filter(x, timestamp)
        smooth_y = self.filter_y.filter(y, timestamp)
        return smooth_x, smooth_y
