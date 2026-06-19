from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.predict import predict_event_impact, get_economic_impact, get_tactical_recommendation, get_dispatch_recommendation, get_phase_timeline, predict_multi_event, get_high_risk_junctions
from utils.traffic_signals import get_signal_recommendations
from graph.simulator import get_high_risk_junctions_graph, get_critical_roads, get_emergency_routes, get_diversion_plan, get_barricade_recommendations, get_major_roads, get_transit_infrastructure
from utils.dispersal_sim import simulate_dispersal
from utils.transit_infrastructure import get_transit_pois, get_metro_corridor_points
from utils.economic_scorer import get_economic_score
import graph.build_network as build_network
import osmnx as ox
from models.train import train_model

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
    model_dir = os.path.join(os.path.dirname(__file__), "..", "models", "saved")
    model_path = os.path.join(model_dir, "xgb_incident_model.joblib")
    meta_path = os.path.join(model_dir, "model_meta.joblib")
    
    # First-run: download graph if missing
    if not os.path.exists(graph_path):
        print("Downloading graph (first run)...")
        build_network.download_and_cache_graph()
    
    # First-run: train model if missing
    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        print("Training incident prediction model (first run)...")
        os.makedirs(model_dir, exist_ok=True)
        train_model()
        print("Model training complete!")
    
    print("Loading graph into memory...")
    sys.stdout.flush()
    try:
        G = ox.load_graphml(graph_path)
        print("Graph loaded successfully!")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error loading graph: {e}")
        sys.stdout.flush()
        raise

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
    emergency_routes = get_emergency_routes(G, request.latitude, request.longitude) if G else []
    timeline_raw = get_phase_timeline(pred['total_incidents'], request.start_time, request.duration_hours)
    
    # 5. Signals
    signals = get_signal_recommendations(high_risk, pred['total_incidents'])
    
    return {
        "prediction": pred,
        "tactical": tactical,
        "dispatch": dispatch,
        "economic_impact": econ,
        "critical_roads": critical_roads,
        "emergency_routes": emergency_routes,
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

class TacticalRequest(BaseModel):
    total_incidents: int
    high_risk_junctions: List = []
    duration_hours: float
    latitude: float
    longitude: float

@app.post("/api/tactical")
def get_tactical_plan(request: TacticalRequest):
    """Get comprehensive tactical deployment recommendations."""
    global G
    tactical = get_tactical_recommendation(
        total_incidents=request.total_incidents,
        high_risk_junctions=request.high_risk_junctions,
        duration_hours=request.duration_hours,
        G=G,
        latitude=request.latitude,
        longitude=request.longitude
    )
    return tactical

class SignalsRequest(BaseModel):
    high_risk_junctions: List
    total_incidents: int

@app.post("/api/signals")
def get_signals_optimization(request: SignalsRequest):
    """Get traffic signal timing optimization."""
    signals = get_signal_recommendations(request.high_risk_junctions, request.total_incidents)
    return signals

class RoadNetworkRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = 1000

@app.post("/api/road-network")
def get_road_network(request: RoadNetworkRequest):
    """Get critical roads and network analysis."""
    global G
    if not G:
        return {"critical_roads": [], "error": "Graph not loaded"}
    
    critical_roads = get_critical_roads(G, request.latitude, request.longitude, radius=request.radius_meters)
    major_roads = get_major_roads(G, num_roads=20)
    
    return {
        "critical_roads": critical_roads,
        "major_roads": major_roads
    }

class RoutingRequest(BaseModel):
    latitude: float
    longitude: float
    total_incidents: int
    emergency_mode: bool = False

@app.post("/api/routing")
def get_routing(request: RoutingRequest):
    """Get emergency routes and diversions."""
    global G
    if not G:
        return {"emergency_routes": [], "error": "Graph not loaded"}
    
    emergency_routes = get_emergency_routes(G, request.latitude, request.longitude)
    
    # Get diversion plan for high-incident scenarios
    diversion_plan = None
    if request.total_incidents > 50:
        diversion_plan = get_diversion_plan(G, request.latitude, request.longitude, request.total_incidents)
    
    return {
        "emergency_routes": emergency_routes,
        "diversion_plan": diversion_plan,
        "emergency_mode_enabled": request.emergency_mode
    }

class BarricadeRequest(BaseModel):
    latitude: float
    longitude: float
    total_incidents: int

@app.post("/api/barricades")
def get_barricade_plan(request: BarricadeRequest):
    """Get barricade placement recommendations."""
    global G
    if not G:
        return {"barricade_locations": [], "error": "Graph not loaded"}
    
    barricades = get_barricade_recommendations(G, request.latitude, request.longitude, request.total_incidents)
    return {"barricade_locations": barricades}

class TransitRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 2.5

@app.post("/api/transit")
def get_transit_data(request: TransitRequest):
    """Get transit and dispersal infrastructure."""
    pois = get_transit_pois(request.latitude, request.longitude, radius_km=request.radius_km)
    corridors = get_transit_infrastructure(None, request.latitude, request.longitude)
    
    return {
        "pois": pois,
        "corridors": corridors
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    global G
    return {
        "status": "ok",
        "graph_loaded": G is not None
    }

