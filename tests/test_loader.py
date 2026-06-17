import unittest
import pandas as pd
import tempfile
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.loader import load_and_clean_data, split_planned_unplanned

class TestCSVLoader(unittest.TestCase):
    def setUp(self):
        # Create a temporary CSV file with mock event data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, "test_events.csv")
        
        # Define sample data conforming to KEEP_COLUMNS
        self.mock_data = pd.DataFrame([
            {
                'id': 'E1',
                'event_type': 'planned',
                'latitude': 12.9715,
                'longitude': 77.5946,
                'event_cause': 'cricket_match',
                'start_datetime': '2026-06-18 18:00:00',
                'end_datetime': '2026-06-18 21:00:00',
                'veh_type': 'private_car',
                'priority': 'High',
                'zone': 'Central'
            },
            {
                'id': 'E2',
                'event_type': 'unplanned',
                'latitude': 13.0250,
                'longitude': 77.6100,
                'event_cause': 'waterlogging',
                'start_datetime': '2026-06-18 14:00:00',
                'end_datetime': None, # Should be imputed +2 hours
                'veh_type': 'two_wheeler',
                'priority': 'Medium',
                'zone': None # Should be computed/assigned based on lat/lng
            },
            {
                'id': 'E3',
                'event_type': 'planned',
                'latitude': 0.0, # Invalid lat, should be cleaned out
                'longitude': 0.0,
                'event_cause': 'vip_movement',
                'start_datetime': '2026-06-18 10:00:00',
                'end_datetime': '2026-06-18 11:00:00',
                'veh_type': 'unknown',
                'priority': 'Low',
                'zone': 'Unknown'
            }
        ])
        self.mock_data.to_csv(self.csv_path, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_and_clean_data(self):
        df = load_and_clean_data(self.csv_path)
        
        self.assertIsNotNone(df)
        # E3 should be dropped due to invalid coordinates (0.0, 0.0)
        self.assertEqual(len(df), 2)
        
        # Check that durations are computed correctly
        # E1: 3 hours
        self.assertEqual(df.loc[df['id'] == 'E1', 'duration_hours'].values[0], 3.0)
        
        # E2: End time was null, should be imputed to start + 2 hours (2.0 hours duration)
        self.assertEqual(df.loc[df['id'] == 'E2', 'duration_hours'].values[0], 2.0)
        self.assertIsNotNone(df.loc[df['id'] == 'E2', 'end_datetime'].values[0])
        
        # Check zone auto-assignment for E2 (13.025, 77.61 is North zone based on constants)
        self.assertEqual(df.loc[df['id'] == 'E2', 'zone'].values[0], 'North')

    def test_split_planned_unplanned(self):
        df = load_and_clean_data(self.csv_path)
        planned, unplanned = split_planned_unplanned(df)
        
        self.assertEqual(len(planned), 1)
        self.assertEqual(len(unplanned), 1)
        self.assertEqual(planned.iloc[0]['id'], 'E1')
        self.assertEqual(unplanned.iloc[0]['id'], 'E2')

if __name__ == '__main__':
    unittest.main()
