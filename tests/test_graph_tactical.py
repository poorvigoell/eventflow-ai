import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph import simulator as sim
from models.predict import get_tactical_recommendation
import networkx as nx


class TestGraphTacticalHelpers(unittest.TestCase):

    def setUp(self):
        # Build a tiny directed graph with coordinates and multiple path options.
        self.G = nx.MultiDiGraph()
        self.G.add_node(0, x=77.60, y=12.97)
        self.G.add_node(1, x=77.605, y=12.97)
        self.G.add_node(2, x=77.60, y=12.975)
        self.G.add_node(3, x=77.605, y=12.975)

        # Direct route from origin (0) to target (1)
        self.G.add_edge(0, 1, key=0, travel_time=60.0, length=100.0, highway='primary', name='Main Road')
        self.G.add_edge(1, 0, key=0, travel_time=60.0, length=100.0, highway='primary', name='Main Road')

        # Alternate path around the direct edge
        self.G.add_edge(0, 2, key=0, travel_time=30.0, length=90.0, highway='secondary', name='Side Road A')
        self.G.add_edge(2, 3, key=0, travel_time=30.0, length=90.0, highway='secondary', name='Side Road B')
        self.G.add_edge(3, 1, key=0, travel_time=30.0, length=90.0, highway='secondary', name='Side Road C')

        # Add a second alternate path with a different road name
        self.G.add_edge(0, 3, key=0, travel_time=45.0, length=70.0, highway='tertiary', name='Outer Loop')
        self.G.add_edge(3, 1, key=1, travel_time=45.0, length=70.0, highway='tertiary', name='Outer Loop')

    def test_get_high_risk_junctions_graph(self):
        junctions = sim.get_high_risk_junctions_graph(self.G, 12.97, 77.60, total_incidents=10)
        self.assertGreaterEqual(len(junctions), 1)
        self.assertLessEqual(len(junctions), 5)
        self.assertIn('name', junctions[0])
        self.assertIn('risk_score', junctions[0])
        self.assertGreaterEqual(junctions[0]['risk_score'], 0.0)
        self.assertLessEqual(junctions[0]['risk_score'], 1.0)

    def test_get_diversion_plan(self):
        # Use a high-risk junction that corresponds to the direct edge.
        high_risk = [{
            'name': 'Main Road',
            'lat': 12.97,
            'lng': 77.6025,
            'risk_score': 0.85,
            'u': 0,
            'v': 1,
            'key': 0
        }]

        diversion_plan = sim.get_diversion_plan(self.G, 12.97, 77.60, high_risk, num_routes=1)
        self.assertGreaterEqual(len(diversion_plan), 1)
        route = diversion_plan[0]
        self.assertIn('from', route)
        self.assertIn('via', route)
        self.assertIn('to', route)
        self.assertIn('added_time', route)
        self.assertGreaterEqual(len(route.get('path', [])), 2)

    def test_get_tactical_recommendation_with_graph(self):
        # Ensure the graph-aware tactical recommendation returns non-empty route guidance.
        tactical = get_tactical_recommendation(
            total_incidents=12,
            high_risk_junctions=[],
            duration_hours=3.0,
            G=self.G,
            latitude=12.97,
            longitude=77.60
        )
        self.assertIn('manpower', tactical)
        self.assertIn('barricade_roads', tactical)
        self.assertIn('diversion_plan', tactical)
        self.assertGreaterEqual(len(tactical['barricade_roads']), 1)
        self.assertGreaterEqual(len(tactical['diversion_plan']), 1)


if __name__ == '__main__':
    unittest.main()
