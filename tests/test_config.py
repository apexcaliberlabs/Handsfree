import os
import unittest
from handsfree.config import ConfigManager


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = ConfigManager()
        self.assertEqual(cfg.get("camera_index"), 0)
        self.assertEqual(cfg.get("flip_horizontal"), True)
        self.assertEqual(cfg.get("cursor_color"), "#00e5ff")

    def test_update_and_get(self):
        cfg = ConfigManager()
        cfg.set("test_key", 999)
        self.assertEqual(cfg.get("test_key"), 999)


if __name__ == "__main__":
    unittest.main()
