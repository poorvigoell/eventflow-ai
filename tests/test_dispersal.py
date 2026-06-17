import unittest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.dispersal_sim import simulate_dispersal

class TestCrowdDispersal(unittest.TestCase):
    def test_density_decreases_over_time(self):
        snapshots = simulate_dispersal(12.9788, 77.5996, crowd_size=10000)
        pcts = [s["remaining_pct"] for s in snapshots]
        for i in range(1, len(pcts)):
            self.assertLessEqual(pcts[i], pcts[i-1] + 0.1)

    def test_zero_crowd(self):
        snapshots = simulate_dispersal(12.9788, 77.5996, crowd_size=0)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(len(snapshots[0]["points"]), 0)

    def test_snapshots_count(self):
        snapshots = simulate_dispersal(12.9788, 77.5996, duration_minutes=60, step_minutes=5)
        self.assertEqual(len(snapshots), 13)

    def test_points_have_required_keys(self):
        snapshots = simulate_dispersal(12.9788, 77.5996, crowd_size=5000)
        for point in snapshots[3]["points"]:
            self.assertIn("lat", point)
            self.assertIn("lng", point)
            self.assertIn("density", point)

if __name__ == '__main__':
    unittest.main()
