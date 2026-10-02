import unittest
from types import SimpleNamespace
from handsfree.core.gestures import GestureEngine, distance_2d


class MockPoint:
    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


class MockMouseController:
    def __init__(self) -> None:
        self.pos = (0, 0)
        self.clicks = []
        self.scrolls = []
        self.is_left_down = False

    def get_screen_size(self):
        return 1920, 1080

    def move_to(self, x: int, y: int):
        self.pos = (x, y)

    def mouse_down(self, button: str = "left"):
        self.is_left_down = True

    def mouse_up(self, button: str = "left"):
        self.is_left_down = False

    def click(self, button: str = "left"):
        self.clicks.append(button)

    def scroll(self, amount: float):
        self.scrolls.append(amount)

    def release_all(self):
        self.is_left_down = False


def create_mock_landmarks(
    thumb_x=0.4, thumb_y=0.4,
    index_x=0.5, index_y=0.4,
    middle_x=0.6, middle_y=0.4
):
    """Generates 21 landmark mock array."""
    pts = [MockPoint(0.5, 0.8) for _ in range(21)]
    pts[0] = MockPoint(0.5, 0.8)    # Wrist
    pts[4] = MockPoint(thumb_x, thumb_y)   # Thumb tip
    pts[5] = MockPoint(0.48, 0.6)  # Index MCP
    pts[8] = MockPoint(index_x, index_y)   # Index tip
    pts[9] = MockPoint(0.52, 0.6)  # Middle MCP
    pts[12] = MockPoint(middle_x, middle_y) # Middle tip
    return pts


class TestGestures(unittest.TestCase):
    def setUp(self):
        self.mock_mouse = MockMouseController()
        self.engine = GestureEngine(self.mock_mouse)

    def test_cursor_movement_mapping(self):
        # Index finger at (0.5, 0.5)
        lm = create_mock_landmarks(thumb_x=0.2, index_x=0.5, index_y=0.5, middle_x=0.8)
        res = self.engine.process_hand(lm)
        self.assertEqual(res["mode"], "MOVE")
        # Ensure coordinates are within screen dimensions
        self.assertGreaterEqual(res["cursor_x"], 0)
        self.assertLessEqual(res["cursor_x"], 1920)

    def test_pinch_click(self):
        # 1. Close pinch distance (thumb and index at nearly identical coordinates)
        lm_pinched = create_mock_landmarks(thumb_x=0.501, thumb_y=0.4, index_x=0.5, index_y=0.4, middle_x=0.8)
        res1 = self.engine.process_hand(lm_pinched)
        self.assertEqual(res1["mode"], "PINCH")

        # 2. Release pinch (move thumb away)
        lm_open = create_mock_landmarks(thumb_x=0.3, thumb_y=0.4, index_x=0.5, index_y=0.4, middle_x=0.8)
        res2 = self.engine.process_hand(lm_open)
        self.assertEqual(res2["mode"], "CLICKED")
        self.assertIn("left", self.mock_mouse.clicks)

    def test_two_finger_scroll(self):
        # Index and middle finger touching together (small distance between 8 and 12)
        lm_scroll1 = create_mock_landmarks(
            thumb_x=0.2, thumb_y=0.5,
            index_x=0.5, index_y=0.4,
            middle_x=0.505, middle_y=0.4
        )
        res1 = self.engine.process_hand(lm_scroll1)
        self.assertEqual(res1["mode"], "SCROLL")

        # Swiping down (y increases to 0.45)
        lm_scroll2 = create_mock_landmarks(
            thumb_x=0.2, thumb_y=0.5,
            index_x=0.5, index_y=0.45,
            middle_x=0.505, middle_y=0.45
        )
        res2 = self.engine.process_hand(lm_scroll2)
        self.assertEqual(res2["mode"], "SCROLL")
        self.assertTrue(len(self.mock_mouse.scrolls) > 0)


if __name__ == "__main__":
    unittest.main()
