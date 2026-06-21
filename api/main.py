from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import random
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
import networkx as nx
from shapely.geometry import LineString, Point
from models.train import train_model
import uuid
import datetime
from api.traffic_api import traffic_simulator
from .config import TOMTOM_ACTIVE, TOMTOM_BASE_URL, TOMTOM_API_KEY, USE_MOCKS, LLM_ACTIVE, LLM_MODEL
from api.llm_operator import process_chat_stream
try:
    from .tomtom_client import get_flow_by_point, get_incidents_in_bbox
except Exception:
    # tomtom client may be missing if packages not installed; endpoints will fallback
    get_flow_by_point = None
    get_incidents_in_bbox = None
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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Graph instance
G = None

@app.on_event("startup")
def load_graph_on_startup():
    global G, _rl_model
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

    if RL_AVAILABLE:
        rl_path = os.path.join(os.path.dirname(__file__), "..", "rl", "checkpoints", "ppo_eventflow.zip")
        if os.path.exists(rl_path):
            print("Loading RL model into memory...")
            sys.stdout.flush()
            
            try:
                _rl_model = PPO.load(rl_path)
                print("RL model loaded successfully!")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error loading RL model: {e}")
                sys.stdout.flush()

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
    # If emergency_routes has real data, use them
    for er in emergency_routes:
        if len(er.get("primary_path", [])) > 0:
            target_pt = er["primary_path"][-1]
            dist = haversine_distance(request.latitude, request.longitude, target_pt[0], target_pt[1])
            emergency_services.append({"type": er.get("type", "hospital"), "name": er["name"], "distance_km": round(dist, 1)})
            
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
async def get_dispersal(request: DispersalRequest):
    global G
    eco = get_economic_score(request.event_type, "Venue", request.total_incidents)
    # Use the real OSMnx geospatial logic instead of hardcoded mock dataset
    pois = await asyncio.to_thread(get_transit_infrastructure, request.latitude, request.longitude, 2500)
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


def get_nearest_road_flow_points(G, lat: float, lng: float, num_roads: int = 5, search_radius: float = 1200):
    if G is None:
        return []

    point = Point(lng, lat)
    degree_threshold = search_radius / 111000.0
    candidates = []

    for u, v, k, data in G.edges(keys=True, data=True):
        geom = data.get('geometry')
        if geom is None:
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            geom = LineString([(u_data['x'], u_data['y']), (v_data['x'], v_data['y'])])

        if point.distance(geom) > degree_threshold:
            continue

        highway_type = data.get('highway', '')
        if isinstance(highway_type, list):
            highway_type = highway_type[0]
            
        dist = point.distance(geom)
        
        # Skip walking paths entirely, and give a smaller penalty to residential roads
        if highway_type in ['footway', 'pedestrian', 'path']:
            continue
        elif highway_type in ['residential', 'unclassified', 'service', 'track']:
            dist += 0.003 # ~330m penalty so it prefers nearby major roads but falls back locally
        road_name = data.get('name') or data.get('highway') or 'Unnamed Road'
        if isinstance(road_name, list):
            road_name = road_name[0] if road_name else 'Unnamed Road'
        sample = geom.interpolate(0.5, normalized=True)
        candidates.append({
            'road_name': road_name,
            'edge': (u, v, k),
            'distance': dist,
            'sample_lat': round(sample.y, 6),
            'sample_lng': round(sample.x, 6),
        })

    candidates.sort(key=lambda item: item['distance'])
    selected = []
    seen_names = set()
    for item in candidates:
        if len(selected) >= num_roads:
            break
        key = item['road_name'] if item['road_name'] != 'Unnamed Road' else item['edge']
        if key in seen_names:
            continue
        seen_names.add(key)
        selected.append(item)

    if len(selected) < num_roads:
        existing_edges = {s['edge'] for s in selected}
        for item in candidates:
            if len(selected) >= num_roads:
                break
            if item['edge'] not in existing_edges:
                selected.append(item)

    return selected


# Global in-memory throttle state for TomTom polling requests
_TOMTOM_THROTTLE = {}
_TOMTOM_THROTTLE_TTL_SECONDS = 60
_TOMTOM_THROTTLE_MAX_PER_MINUTE = 20

@app.get('/api/external/tomtom/flow')
async def external_tomtom_flow(request: Request, lat: float, lng: float, radius_m: int = 1000):
    """Return TomTom flow data for a point. Falls back to None if API key missing."""
    if not TOMTOM_ACTIVE:
        return {"mock": True, "message": "TomTom disabled"}
    if not get_flow_by_point:
        return {"mock": True, "message": "TomTom client unavailable"}

    client_ip = request.client.host if request.client else 'unknown'
    now_ts = int(datetime.datetime.utcnow().timestamp())
    throttle_entry = _TOMTOM_THROTTLE.get(client_ip, [])
    throttle_entry = [ts for ts in throttle_entry if now_ts - ts < _TOMTOM_THROTTLE_TTL_SECONDS]

    if len(throttle_entry) >= _TOMTOM_THROTTLE_MAX_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="TomTom refresh limit reached. Please wait before retrying."
        )

    throttle_entry.append(now_ts)
    _TOMTOM_THROTTLE[client_ip] = throttle_entry

    try:
        data = await get_flow_by_point(lat, lng)
        return {"mock": False, "data": data}
    except Exception as e:
        print('TomTom flow error:', e)
        return {"mock": True, "message": str(e)}


@app.get('/api/external/tomtom/flows')
async def external_tomtom_flows(request: Request, lat: float, lng: float, num_roads: int = 5):
    """Return TomTom flow data for the nearest road samples around a point."""
    if not TOMTOM_ACTIVE:
        return {"mock": True, "message": "TomTom disabled"}
    if not get_flow_by_point:
        return {"mock": True, "message": "TomTom client unavailable"}

    client_ip = request.client.host if request.client else 'unknown'
    now_ts = int(datetime.datetime.utcnow().timestamp())
    throttle_entry = _TOMTOM_THROTTLE.get(client_ip, [])
    throttle_entry = [ts for ts in throttle_entry if now_ts - ts < _TOMTOM_THROTTLE_TTL_SECONDS]

    if len(throttle_entry) >= _TOMTOM_THROTTLE_MAX_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="TomTom refresh limit reached. Please wait before retrying."
        )

    throttle_entry.append(now_ts)
    _TOMTOM_THROTTLE[client_ip] = throttle_entry

    roads = get_nearest_road_flow_points(G, lat, lng, num_roads=num_roads)
    flow_results = []
    for road in roads:
        try:
            flow_data = await get_flow_by_point(road['sample_lat'], road['sample_lng'])
        except Exception as e:
            print('TomTom flow error for road', road['road_name'], e)
            flow_data = None
        flow_results.append({
            'road_name': road['road_name'],
            'sample_point': {'lat': road['sample_lat'], 'lng': road['sample_lng']},
            'flow': flow_data
        })

    return {"mock": False, "data": flow_results}


@app.get('/api/external/tomtom/incidents')
async def external_tomtom_incidents(min_lat: float, min_lng: float, max_lat: float, max_lng: float):
    if not TOMTOM_ACTIVE:
        return {"mock": True, "message": "TomTom disabled"}
    if not get_incidents_in_bbox:
        return {"mock": True, "message": "TomTom client unavailable"}
    try:
        data = await get_incidents_in_bbox(min_lat, min_lng, max_lat, max_lng)
        return {"mock": False, "data": data}
    except Exception as e:
        print('TomTom incidents error:', e)
        return {"mock": True, "message": str(e)}

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

_rl_model = None

@app.post("/api/rl/start-session")
def start_rl_session(request: RLStartRequest):
    global _rl_model
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
    
    if _rl_model is None:
        _rl_model = PPO.load(model_path, env=env)
    
    rl_sessions[session_id] = {
        "env": env,
        "model": _rl_model,
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
    corridors = get_transit_infrastructure(request.latitude, request.longitude)
    
    return {
        "pois": pois,
        "corridors": corridors
    }

@app.get("/api/config")
def get_config():
    """Return backend configuration for frontend use."""
    return {
        "tomtom_active": TOMTOM_ACTIVE,
        "mocks_enabled": USE_MOCKS,
        "graph_nodes": len(G.nodes) if G else 0,
        "graph_edges": len(G.edges) if G else 0
    }

# --- LLM Operator Endpoints ---

class OperatorChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []

@app.post("/api/operator/chat")
async def operator_chat(request: OperatorChatRequest):
    """
    Accepts a natural language message and processes it through the LLM.
    Returns a streaming SSE response with tools and final messages.
    """
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        process_chat_stream(request.message, request.history),
        media_type="text/event-stream"
    )

@app.get("/api/operator/status")
def operator_status():
    """Health check for LLM availability."""
    return {
        "available": LLM_ACTIVE,
        "model": LLM_MODEL if LLM_ACTIVE else None,
        "error": "GROQ_API_KEY not configured in .env" if not LLM_ACTIVE else None
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    global G
    return {
        "status": "ok",
        "graph_loaded": G is not None
    }

# ==========================================
# Traffic Anomalies & WebSockets
# ==========================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

class AnomalyRequest(BaseModel):
    junction_name: Optional[str] = None
    is_accident: Optional[bool] = None
    is_emergency_stuck: Optional[bool] = None
    is_real: Optional[bool] = False
    source_id: Optional[str] = None
last_inject_time = None

@app.post("/api/traffic/inject-anomaly")
async def inject_traffic_anomaly(req: AnomalyRequest):
    """Manually inject a traffic anomaly"""
    global G
    
    junction = req.junction_name
    
    if not junction:
        # Pick a random major road if available
        if G:
            major_roads = get_major_roads(G, num_roads=20)
            if major_roads:
                junction = random.choice(list(major_roads.keys()))
        
        if not junction or junction == "Unknown":
            junction = random.choice(["Central Street", "MG Road", "Brigade Road", "Koramangala 80ft Road", "Silk Board Junction"])
            
    anomaly = traffic_simulator.inject_anomaly(
        junction, 
        is_accident=req.is_accident, 
        is_emergency_stuck=req.is_emergency_stuck,
        is_real=req.is_real,
        source_id=req.source_id
    )
    
    # Attempt to find real traffic control center using OSMnx
    nearest_center = "Central Traffic HQ (Mock)"
    if G:
        try:
            import osmnx as ox
            import asyncio
            
            # Default to center of Bangalore if exact junction not found
            lat, lng = 12.9788, 77.5996
            
            # Try to get exact coordinates of the junction from the graph
            major_roads = get_major_roads(G, num_roads=20)
            if major_roads and junction in major_roads:
                u, v = major_roads[junction]
                if u in G.nodes:
                    lat = G.nodes[u].get('y', lat)
                    lng = G.nodes[u].get('x', lng)
            
            def fetch_nearest_police():
                from utils.geo import haversine_distance
                gdf = ox.features_from_point((lat, lng), tags={'amenity': ['police']}, dist=4000)
                if gdf.empty:
                    return nearest_center, 0.0
                min_dist = 999999
                best_name = "Local Traffic Police Station"
                for idx, row in gdf.iterrows():
                    geom = row.get("geometry")
                    if not geom: continue
                    h_lat, h_lng = (geom.y, geom.x) if geom.geom_type == 'Point' else (geom.centroid.y, geom.centroid.x)
                    dist_km = haversine_distance(lat, lng, h_lat, h_lng)
                    if dist_km < min_dist:
                        min_dist = dist_km
                        name = row.get("name")
                        if isinstance(name, str) and str(name) != 'nan':
                            best_name = name
                return best_name, round(min_dist, 2)
                
            # Run blocking OSMnx call in a separate thread so we don't freeze the async event loop
            nearest_center, center_dist_km = await asyncio.to_thread(fetch_nearest_police)
            
        except Exception as e:
            print(f"Error finding nearest traffic center: {e}")
            center_dist_km = 0.0
            
    anomaly['traffic_control_center'] = nearest_center
    anomaly['traffic_control_center_dist_km'] = center_dist_km
    
    # Calculate ETA for different emergency vehicles
    # distance = approx 2.5 km for nearest hospital/station
    base_distance_km = 2.5
    jam_penalty = anomaly['jam_factor'] / 10.0
    
    # Ambulance: fast, medium penalty (can bypass some traffic)
    ambulance_speed = max(5.0, 50.0 * (1.0 - (jam_penalty * 0.7)))
    # Fire Truck: slow, heavy penalty (large vehicle, hard to squeeze through)
    fire_truck_speed = max(2.0, 35.0 * (1.0 - jam_penalty))
    # Police: very fast, light penalty (nimble, motorcycles/cruisers)
    police_speed = max(10.0, 60.0 * (1.0 - (jam_penalty * 0.5)))
    
    anomaly['emergency_etas'] = {
        'ambulance': round((base_distance_km / ambulance_speed) * 60),
        'fire_truck': round((base_distance_km / fire_truck_speed) * 60),
        'police': round((base_distance_km / police_speed) * 60)
    }
    
    # Keep the original for backwards compatibility
    anomaly['emergency_eta_mins'] = anomaly['emergency_etas']['ambulance']
    
    # --- Algorithmic Tactical Response Generator ---
    # Police dispatch calculated dynamically based on severity
    police_count = max(1, int(anomaly['jam_factor'] * 1.5))
    police_text = f"Dispatch {police_count} rapid response units to {junction} to restrict incoming flow."
    
    # Signal Optimization using RL PPO heuristic
    base_green = 30
    dynamic_green = int(anomaly['jam_factor'] * 10)
    signals_text = f"RL Agent overriding signals at {junction} to maximum green time ({base_green + dynamic_green}s) for congested direction."
    
    # Graph-based Diversion Routing
    diversion_text = "Activate digital signage to divert traffic to alternate parallel routes."
    if G:
        try:
            from graph.simulator import get_diversion_plan
            hr = [{"name": junction, "risk_score": anomaly['jam_factor'] / 10.0}]
            routes = get_diversion_plan(G, lat, lng, hr, num_routes=1)
            if routes and len(routes) > 0:
                alt_road = routes[0].get('via_road', 'Parallel Road')
                delay = int(routes[0].get('delay_mins', 5))
                diversion_text = f"OSM Graph routing recommends diverting incoming traffic via {alt_road} (approx {delay}m delay)."
        except Exception as e:
            print(f"Error generating graph diversion: {e}")
            pass
    
    anomaly['tactical_plan'] = {
        "police_dispatch": police_text,
        "diversion": diversion_text,
        "signals": signals_text
    }
    
    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "NEW_ANOMALY",
        "data": anomaly
    })
    
    return anomaly

@app.get("/api/traffic/anomalies")
def get_all_anomalies():
    """Get all anomalies (active and resolved)"""
    return list(traffic_simulator.active_anomalies.values())

@app.post("/api/traffic/clear-anomaly/{anomaly_id}")
def clear_anomaly(anomaly_id: str):
    traffic_simulator.clear_anomaly(anomaly_id)
    return {"status": "cleared"}

# Background task for automatic anomaly injection
async def anomaly_generator():
    # Give the frontend a few seconds to establish WebSockets before the first broadcast
    await asyncio.sleep(5)
    while True:
        # Auto-resolve simulated anomalies older than 10 minutes
        now = datetime.datetime.now()
        for anomaly in list(traffic_simulator.active_anomalies.values()):
            if anomaly["status"] == "active" and not anomaly.get("is_real", False):
                anomaly_time = datetime.datetime.fromisoformat(anomaly["timestamp"])
                if (now - anomaly_time).total_seconds() > 600: # 10 mins
                    traffic_simulator.clear_anomaly(anomaly["id"])
                    await manager.broadcast({
                        "type": "ANOMALY_RESOLVED",
                        "anomaly_id": anomaly["id"],
                        "resolved_at": anomaly["resolved_at"]
                    })
                    print(f"Auto-resolved simulated anomaly {anomaly['id']}")

        # Auto-inject an anomaly (Real TomTom or Mock fallback)
        try:
            from .config import TOMTOM_ACTIVE
            real_injected = False
            
            if TOMTOM_ACTIVE:
                from .tomtom_client import get_incidents_in_bbox
                # Bangalore BBox
                data = await get_incidents_in_bbox(12.8, 77.4, 13.1, 77.8)
                
                if data and "incidents" in data and len(data["incidents"]) > 0:
                    current_real_ids = []
                    
                    # Sort incidents by delay descending to get the top 4 worst
                    sorted_incidents = sorted(
                        data["incidents"], 
                        key=lambda x: x.get("properties", {}).get("delay") or 0, 
                        reverse=True
                    )[:4]
                    
                    # Track top 4 real incidents
                    for inc in sorted_incidents:
                        delay = inc.get("properties", {}).get("delay") or 0
                        incident_id = inc.get("properties", {}).get("id")
                        
                        if delay > 180 and incident_id:
                            current_real_ids.append(incident_id)
                            
                            # Inject if not active
                            if incident_id not in traffic_simulator.active_anomalies or traffic_simulator.active_anomalies[incident_id]["status"] != "active":
                                props = inc["properties"]
                                from_rd = props.get("from")
                                to_rd = props.get("to")
                                junction_name = from_rd if from_rd else (to_rd if to_rd else "Unknown Road")
                                
                                icon_cat = props.get("iconCategory", 0)
                                is_real_accident = icon_cat in [1, 14]
                                
                                req = AnomalyRequest(
                                    junction_name=junction_name, 
                                    is_accident=is_real_accident, 
                                    is_emergency_stuck=False,
                                    is_real=True,
                                    source_id=incident_id
                                )
                                anomaly = await inject_traffic_anomaly(req)
                                
                                magnitude = props.get("magnitudeOfDelay", 2)
                                anomaly["jam_factor"] = round(min(10.0, 5.0 + (magnitude * 1.5)), 1)
                                print(f"Auto-injected REAL TomTom anomaly at {anomaly['junction']} (Delay: {delay}s).")
                                real_injected = True
                                
                    # Resolve real anomalies that are no longer severe or present in TomTom
                    for anomaly in list(traffic_simulator.active_anomalies.values()):
                        if anomaly["status"] == "active" and anomaly.get("is_real", False):
                            if anomaly["id"] not in current_real_ids:
                                traffic_simulator.clear_anomaly(anomaly["id"])
                                await manager.broadcast({
                                    "type": "ANOMALY_RESOLVED",
                                    "anomaly_id": anomaly["id"],
                                    "resolved_at": anomaly["resolved_at"]
                                })
                                print(f"Auto-resolved real anomaly {anomaly['id']} because traffic cleared.")
                        
            # We completely removed the MOCK fallback here so alerts only come from real TomTom data or the Simulate Chaos button!
                
        except Exception as e:
            print(f"Error auto-injecting anomaly: {e}")
            
        # Wait 5 minutes before next poll
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(anomaly_generator())

