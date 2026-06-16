import unittest
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.predict import predict_event_impact, get_high_risk_junctions, get_phase_timeline
from data.correlator import correlate_events

class TestMLBackend(unittest.TestCase):

    def test_predict_event_impact_edge_cases(self):
        # Test unknown zone
        res1 = predict_event_impact(
            event_type="public_event",
            latitude=12.97,
            longitude=77.60,
            zone="Unknown_Zone_XYZ",
            start_time="2024-03-15 18:00:00",
            duration_hours=2.0
        )
        self.assertIn("total_incidents", res1)
        self.assertGreaterEqual(res1["total_incidents"], 0)
        
        # Test zero duration
        res2 = predict_event_impact(
            event_type="vip_movement",
            latitude=12.97,
            longitude=77.60,
            zone="Central",
            start_time="2024-03-15 18:00:00",
            duration_hours=0.0
        )
        self.assertIn("total_incidents", res2)

    def test_get_high_risk_junctions(self):
        # Less than 3 incidents should return empty list
        self.assertEqual(len(get_high_risk_junctions(12.0, 77.0, 2)), 0)
        
        # Should return exactly up to 5 junctions
        junctions = get_high_risk_junctions(12.97, 77.60, 15)
        self.assertGreaterEqual(len(junctions), 1)
        self.assertLessEqual(len(junctions), 5)
        self.assertIn("name", junctions[0])
        self.assertIn("risk_score", junctions[0])
        
        # Check sorting
        scores = [j['risk_score'] for j in junctions]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_get_phase_timeline(self):
        # Test timeline generation
        timeline = get_phase_timeline(10, "2024-03-15 18:00:00", 3.0)
        self.assertGreater(len(timeline), 0)
        
        phases = [item['phase'] for item in timeline]
        self.assertIn("inflow", phases)
        self.assertIn("steady", phases)
        self.assertIn("exodus", phases)

    def test_correlator_logic(self):
        # Create tiny mock dataframes
        planned = pd.DataFrame([{
            'id': 'E1',
            'event_cause': 'public_event',
            'latitude': 12.9700,
            'longitude': 77.6000,
            'start_datetime': pd.to_datetime("2024-03-15 15:00:00"),
            'end_datetime': pd.to_datetime("2024-03-15 18:00:00"),
            'duration_hours': 3.0,
            'zone': 'Central',
            'priority': 'High'
        }])
        
        unplanned = pd.DataFrame([{
            'id': 'U1',
            'latitude': 12.9710, # Very close
            'longitude': 77.6010,
            'start_datetime': pd.to_datetime("2024-03-15 16:00:00"), # During steady
        }, {
            'id': 'U2',
            'latitude': 13.9700, # Too far
            'longitude': 77.6000,
            'start_datetime': pd.to_datetime("2024-03-15 16:00:00"), 
        }])
        
        training_df = correlate_events(planned, unplanned)
        self.assertEqual(len(training_df), 1)
        
        row = training_df.iloc[0]
        self.assertEqual(row['total_incidents'], 1)
        self.assertEqual(row['steady_incidents'], 1)

if __name__ == '__main__':
    unittest.main()
