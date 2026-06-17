import unittest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.traffic_signals import calculate_webster_timing, get_signal_recommendations

class TestSignalTiming(unittest.TestCase):
    def test_cycle_length_within_bounds(self):
        result = calculate_webster_timing([0.3, 0.2])
        self.assertGreaterEqual(result["cycle_length_sec"], 45)
        self.assertLessEqual(result["cycle_length_sec"], 120)

    def test_green_splits_positive(self):
        result = calculate_webster_timing([0.4, 0.3])
        for phase in result["phases"]:
            self.assertGreater(phase["green_sec"], 0)
            self.assertGreater(phase["red_sec"], 0)

    def test_high_flow_capped_at_120(self):
        result = calculate_webster_timing([0.6, 0.3])
        self.assertLessEqual(result["cycle_length_sec"], 120)

    def test_recommendations_empty_when_low_incidents(self):
        junctions = [{"name": "Test", "risk_score": 0.5, "lat": 12.97, "lng": 77.60}]
        self.assertEqual(get_signal_recommendations(junctions, 2), [])

    def test_recommendations_generated(self):
        junctions = [
            {"name": "Junction A", "risk_score": 0.8, "lat": 12.97, "lng": 77.60},
            {"name": "Junction B", "risk_score": 0.5, "lat": 12.98, "lng": 77.61},
        ]
        recs = get_signal_recommendations(junctions, 10)
        self.assertEqual(len(recs), 2)
        self.assertIn("junction_name", recs[0])
        self.assertIn("cycle_length_sec", recs[0])

if __name__ == '__main__':
    unittest.main()
