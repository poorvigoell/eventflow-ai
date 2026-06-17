import unittest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.live_traffic import fetch_live_traffic

class TestLiveTraffic(unittest.TestCase):
    def test_fetch_live_traffic(self):
        lat = 12.9716
        lng = 77.5946
        traffic = fetch_live_traffic(lat, lng)
        self.assertTrue(len(traffic) > 0)
        self.assertIn("path", traffic[0])
        self.assertIn("level", traffic[0])
        self.assertIn("color", traffic[0])
        self.assertEqual(len(traffic[0]["path"]), 2)

if __name__ == '__main__':
    unittest.main()
