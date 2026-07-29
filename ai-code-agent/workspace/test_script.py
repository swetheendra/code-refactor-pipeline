import unittest
from script import calculate_total


class TestScript(unittest.TestCase):
    def test_calculate_total(self):
        self.assertEqual(calculate_total(100, 2), 180.0)
        self.assertEqual(calculate_total(50, 3), 135.0)
        self.assertEqual(calculate_total(0, 5), 0.0)


if __name__ == "__main__":
    unittest.main()
