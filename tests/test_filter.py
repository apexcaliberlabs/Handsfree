import math
import time
import unittest
from handsfree.core.filter import OneEuroFilter1D, PointFilter2D


class TestOneEuroFilter(unittest.TestCase):
    def test_stationary_jitter_reduction(self):
        """Test that random micro-jitter around a stationary point is heavily smoothed."""
        f = OneEuroFilter1D(min_cutoff=1.0, beta=0.0)
        t = 0.0
        outputs = []
        base = 100.0

        for i in range(50):
            # Alternating jitter +/- 2.0
            jitter = 2.0 if (i % 2 == 0) else -2.0
            x = base + jitter
            val = f.filter(x, t)
            outputs.append(val)
            t += 0.033  # ~30fps

        # Last output should be close to base (100.0) with jitter attenuated
        self.assertAlmostEqual(outputs[-1], base, delta=0.8)

    def test_fast_motion_responsiveness(self):
        """Test that fast sudden movement adapts cutoff frequency and follows quickly."""
        f = OneEuroFilter1D(min_cutoff=1.0, beta=0.1)
        t = 0.0
        f.filter(0.0, t)

        # Large sudden step jump to 1000.0
        t += 0.033
        step_val = f.filter(1000.0, t)
        # Should have jumped substantially toward 1000.0 due to high velocity beta
        self.assertGreater(step_val, 200.0)

    def test_point_filter_2d(self):
        pf = PointFilter2D()
        sx, sy = pf.filter(500.0, 300.0, time.perf_counter())
        self.assertEqual(sx, 500.0)
        self.assertEqual(sy, 300.0)


if __name__ == "__main__":
    unittest.main()
