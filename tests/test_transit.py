import unittest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.transit_estimator import estimate_transit_diversion

class TestTransitEstimator(unittest.TestCase):
    def test_high_impact_near_metro(self):
        result = estimate_transit_diversion("Chinnaswamy Stadium", 500)
        self.assertEqual(result["nearest_station"], "Cubbon Park")
        self.assertEqual(result["line_color"], "Purple")
        self.assertTrue(result["divertable_commuters"] > 1000)

    def test_low_impact_far_metro(self):
        result = estimate_transit_diversion("Silk Board", 50)
        self.assertEqual(result["nearest_station"], "Rashtriya Vidyalaya Road")
        self.assertEqual(result["line_color"], "Green")
        self.assertTrue(result["divertable_commuters"] < 1000)

if __name__ == '__main__':
    unittest.main()
