import unittest
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.predict import predict_event_impact, get_high_risk_junctions, get_phase_timeline, generate_unplanned_events, get_tactical_recommendation, get_dispatch_recommendation
from data.correlator import correlate_events

class TestMLBackend(unittest.TestCase):

    def test_generate_unplanned_events(self):
        events = generate_unplanned_events(12.9789, 77.5998, radius_km=2.0)
        self.assertGreaterEqual(len(events), 1)
        self.assertLessEqual(len(events), 3)
        for event in events:
            self.assertIn("id", event)
            self.assertIn("event_type", event)
            self.assertIn("severity", event)
            self.assertIn("latitude", event)
            self.assertIn("longitude", event)
            self.assertIn("description", event)

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

    def test_get_emergency_routes(self):
        import osmnx as ox
        import networkx as nx
        # Create a small grid graph for fast deterministic test
        grid = nx.grid_2d_graph(5, 5)
        G = nx.MultiDiGraph()
        for node in grid.nodes():
            G.add_node(node, x=float(node[0]), y=float(node[1]))
        for u, v in grid.edges():
            G.add_edge(u, v, travel_time=1.0, length=100.0)
            G.add_edge(v, u, travel_time=1.0, length=100.0)

        from graph.simulator import get_emergency_routes
        routes = get_emergency_routes(G, lat=2.0, lng=2.0, blockade_edges=[((2, 2), (2, 3))])
        self.assertGreaterEqual(len(routes), 1)
        self.assertIn("primary_path", routes[0])
        self.assertIn("detour_path", routes[0])

    def test_recommendations(self):
        # Test tactical recommendation logic
        junctions = [{"name": "Junction A", "risk_score": 0.85, "lat": 12.97, "lng": 77.60}]
        tactical = get_tactical_recommendation(total_incidents=10, high_risk_junctions=junctions, duration_hours=3.0)
        self.assertIn("manpower", tactical)
        self.assertIn("barricade_roads", tactical)
        self.assertIn("diversion_plan", tactical)
        self.assertGreater(tactical["manpower"]["traffic_police"], 0)
        
        # Test dispatch recommendation logic
        dispatch = get_dispatch_recommendation(total_incidents=12, risk_score=0.7)
        self.assertIn("total_units", dispatch)
        self.assertIn("alert_level", dispatch)
        self.assertEqual(dispatch["alert_level"], "AMBER")

if __name__ == '__main__':
    unittest.main()
