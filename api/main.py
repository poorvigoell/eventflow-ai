from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.predict import predict_event_impact, get_economic_impact, get_tactical_recommendation, get_dispatch_recommendation, get_phase_timeline, predict_multi_event
from utils.traffic_signals import get_signal_recommendations
from graph.simulator import get_high_risk_junctions_graph, get_critical_roads, get_emergency_routes
from utils.dispersal_sim import simulate_dispersal
from utils.transit_infrastructure import get_transit_pois, get_metro_corridor_points
from utils.economic_scorer import get_economic_score
import graph.build_network as build_network
import osmnx as ox

app = FastAPI(title="EventFlow AI Backend")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Graph instance
G = None

@app.on_event("startup")
def load_graph_on_startup():
    global G
    graph_path = os.path.join(os.path.dirname(__file__), "..", "graph", "bengaluru_network.graphml")
    if not os.path.exists(graph_path):
        print("Downloading graph (first run)...")
        build_network.download_and_cache_graph()
    print("Loading graph into memory...")
    G = ox.load_graphml(graph_path)
    print("Graph loaded!")

class EventRequest(BaseModel):
    event_type: str
    latitude: float
    longitude: float
    zone: str = "Central"
    start_time: str
    duration_hours: float = 4.0
    weather_rain: bool = False
    multi_event_mode: bool = False
    emergency_mode: bool = False

@app.post("/api/predict")
def predict_event(request: EventRequest):
    global G
    # 1. Base Prediction
    pred = predict_event_impact(
        event_type=request.event_type,
        latitude=request.latitude,
        longitude=request.longitude,
        zone=request.zone,
        start_time=request.start_time,
        duration_hours=request.duration_hours
    )
    
    # Handle multi-event
    if request.multi_event_mode:
        events = [
            {
                "event_type": request.event_type,
                "latitude": request.latitude, "longitude": request.longitude, "zone": request.zone,
                "start_time": request.start_time, "duration_hours": request.duration_hours
            },
            {
                "event_type": "protest",
                "latitude": 12.9782, "longitude": 77.5815, "zone": "Central",
                "start_time": request.start_time, "duration_hours": request.duration_hours
            }
        ]
        multi_data = predict_multi_event(events)
        pred['total_incidents'] = multi_data['combined_total_incidents']
        pred['confidence'] = multi_data['combined_confidence']
    
    # Handle Weather
    if request.weather_rain:
        pred['total_incidents'] = int(pred['total_incidents'] * 1.5)
        pred['confidence'] = 0.65
        
    # 2. Graph routing for High Risk
    if G:
        high_risk = get_high_risk_junctions_graph(G, request.latitude, request.longitude, pred['total_incidents'], radius=1000)
    else:
        high_risk = []
        
    pred['high_risk_junctions'] = high_risk
    
    # 3. Tactical Plan
    tactical = get_tactical_recommendation(
        total_incidents=pred['total_incidents'],
        high_risk_junctions=high_risk,
        duration_hours=request.duration_hours,
        G=G,
        latitude=request.latitude,
        longitude=request.longitude
    )
    
    dispatch = get_dispatch_recommendation(pred['total_incidents'], pred['confidence'])
    real_econ = get_economic_impact(pred['total_incidents'], request.duration_hours, request.event_type)
    econ = {
        "cost_lakhs": round(real_econ['total_cost_inr'] / 100000, 2),
        "person_hours": f"{int(real_econ['person_hours_lost']):,}",
        "surcharge_lakhs": round((real_econ['total_cost_inr'] / 10) / 100000, 2) if real_econ['total_cost_inr'] > 1000000 else 0.0,
        "surcharge_recommendation": real_econ['surcharge_recommendation']
    }
    
    # 4. Map Overlays & Timeline
    critical_roads = get_critical_roads(G, request.latitude, request.longitude, radius=1000) if G else []
    timeline_raw = get_phase_timeline(pred['total_incidents'], request.start_time, request.duration_hours)
    
    # 5. Signals
    signals = get_signal_recommendations(high_risk, pred['total_incidents'])
    
    return {
        "prediction": pred,
        "tactical": tactical,
        "dispatch": dispatch,
        "economic_impact": econ,
        "critical_roads": critical_roads,
        "timeline": timeline_raw,
        "signals": signals
    }

class DispersalRequest(BaseModel):
    event_type: str
    latitude: float
    longitude: float
    total_incidents: int
    crowd_size: int = 30000

@app.post("/api/dispersal")
def get_dispersal(request: DispersalRequest):
    global G
    eco = get_economic_score(request.event_type, "Venue", request.total_incidents)
    pois = get_transit_pois(request.latitude, request.longitude, radius_km=2.5)
    corridors = get_metro_corridor_points(request.latitude, request.longitude, radius_km=3.0)
    
    # Generate crowd dispersal snapshots (t=0 to t=60)
    snapshots = simulate_dispersal(request.latitude, request.longitude, request.crowd_size, G=G)
    
    return {
        "eco_profile": eco,
        "transit_pois": pois,
        "metro_corridors": corridors,
        "snapshots": snapshots
    }

@app.get("/api/initial-map-data")
def get_initial_map_data(lat: float = 12.9788, lng: float = 77.5996):
    # Fetch metro corridors for the initial city view
    from utils.transit_infrastructure import get_metro_corridors_lines
    corridors = get_metro_corridors_lines()
    return {
        "metro_corridors": corridors
    }
