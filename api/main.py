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
import uuid
import datetime
try:
    from stable_baselines3 import PPO
    from rl.gym_env import EventFlowEnv
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False

rl_sessions = {}

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
        "affected_commuters": real_econ.get('affected_commuters', 0),
        "fuel_liters_wasted": real_econ.get('fuel_liters_wasted', 0),
        "surcharge_lakhs": round((real_econ['total_cost_inr'] / 10) / 100000, 2) if real_econ['total_cost_inr'] > 1000000 else 0.0,
        "surcharge_recommendation": real_econ['surcharge_recommendation']
    }
    
    # 4. Map Overlays & Timeline
    critical_roads = get_critical_roads(G, request.latitude, request.longitude, radius=600) if G else []
    emergency_routes = get_emergency_routes(G, request.latitude, request.longitude) if G else []
    timeline_raw = get_phase_timeline(pred['total_incidents'], request.start_time, request.duration_hours)
    
    # Generate Emergency Services for the UI
    import random
    from utils.geo import haversine_distance
    
    emergency_services = []
    # If emergency_routes has real hospitals, use them
    for er in emergency_routes:
        if len(er.get("primary_path", [])) > 0:
            target_pt = er["primary_path"][-1]
            dist = haversine_distance(request.latitude, request.longitude, target_pt[0], target_pt[1])
            emergency_services.append({"type": "hospital", "name": er["name"], "distance_km": round(dist, 1)})
            
    # Fill in police stations and any missing hospitals
    if len(emergency_services) < 2:
        emergency_services.append({"type": "hospital", "name": "City General Hospital", "distance_km": round(random.uniform(1.2, 3.0), 1)})
    
    emergency_services.extend([
        {"type": "police", "name": "Central Police Station", "distance_km": round(random.uniform(0.5, 2.0), 1)},
        {"type": "police", "name": "Traffic Police Outpost", "distance_km": round(random.uniform(1.0, 2.5), 1)}
    ])
    
    # Sort by distance
    emergency_services.sort(key=lambda x: x["distance_km"])
    
    # 5. Signals
    signals = get_signal_recommendations(high_risk, pred['total_incidents'])
    
    return {
        "prediction": pred,
        "tactical": tactical,
        "dispatch": dispatch,
        "economic_impact": econ,
        "critical_roads": critical_roads,
        "emergency_routes": emergency_routes,
        "emergency_services": emergency_services,
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

class RLStartRequest(BaseModel):
    latitude: float
    longitude: float
    event_type: str
    duration_hours: float
    weather_rain: bool

@app.get("/api/rl/status")
def get_rl_status():
    if not RL_AVAILABLE:
        return {"model_exists": False, "error": "RL not installed"}
    model_path = os.path.join(os.path.dirname(__file__), "..", "rl", "checkpoints", "ppo_eventflow.zip")
    exists = os.path.exists(model_path)
    return {
        "model_exists": exists,
        "checkpoint_path": model_path if exists else None,
        "last_trained": datetime.datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat() if exists else None
    }

@app.post("/api/rl/start-session")
def start_rl_session(request: RLStartRequest):
    if not RL_AVAILABLE:
        return {"error": "RL not available"}
    global G
    model_path = os.path.join(os.path.dirname(__file__), "..", "rl", "checkpoints", "ppo_eventflow.zip")
    if not os.path.exists(model_path):
        return {"error": "RL model not trained yet."}
        
    session_id = str(uuid.uuid4())
    
    config = {
        'latitude': request.latitude,
        'longitude': request.longitude,
        'event_type': request.event_type,
        'duration_hours': request.duration_hours,
        'weather_rain': request.weather_rain,
    }
    
    env = EventFlowEnv(G=G, config=config)
    obs, _ = env.reset()
    
    model = PPO.load(model_path, env=env)
    
    rl_sessions[session_id] = {
        "env": env,
        "model": model,
        "last_accessed": datetime.datetime.now()
    }
    
    junctions_data = []
    for i, j in enumerate(env.junctions):
        junctions_data.append({
            "name": j.get('name', f"Junction {i+1}"),
            "initial_green_sec": env.green_times[i],
            "initial_queue": env.queues[i]
        })
        
    return {
        "session_id": session_id,
        "junctions": junctions_data,
        "total_incidents": env.total_incidents
    }

class RLActionRequest(BaseModel):
    session_id: str

@app.post("/api/rl/next-action")
def get_rl_next_action(request: RLActionRequest):
    if not RL_AVAILABLE:
        return {"error": "RL not available"}
    session = rl_sessions.get(request.session_id)
    if not session:
        return {"error": "Invalid or expired session ID."}
        
    env = session["env"]
    model = session["model"]
    session["last_accessed"] = datetime.datetime.now()
    
    obs = env._get_obs()
    action, _ = model.predict(obs, deterministic=True)
    
    old_greens = list(env.green_times)
    
    obs, reward, done, _, info = env.step(action)
    
    actions_taken = []
    for i in range(env.num_junctions):
        adjustment = env.green_times[i] - old_greens[i]
        actions_taken.append({
            "junction": env.junctions[i].get('name', f"Junction {i+1}"),
            "adjustment_sec": float(adjustment),
            "new_green_sec": float(env.green_times[i]),
            "queue": float(env.queues[i])
        })
        
    return {
        "step": env.current_step,
        "actions": actions_taken,
        "metrics": {
            "avg_queue": float(info.get('avg_queue', 0)),
            "crowd_remaining_pct": float(env.crowd_remaining * 100),
            "reward": float(reward)
        },
        "done": done
    }

@app.post("/api/rl/end-session")
def end_rl_session(request: RLActionRequest):
    if request.session_id in rl_sessions:
        del rl_sessions[request.session_id]
    return {"status": "success"}

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

