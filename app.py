import streamlit as st
import osmnx as ox
import os
import graph.simulator as sim
from visualization.timeline import render_timeline
from visualization.command_center import render_command_center
from visualization.digital_twin import render_digital_twin
from visualization.map_view import render_folium_map
from models.predict import predict_event_impact, get_economic_impact, predict_multi_event, get_tactical_recommendation, get_dispatch_recommendation
from utils.traffic_signals import get_signal_recommendations
from visualization.signal_timing_view import render_signal_timing
from visualization.report_view import render_report_download
from visualization.dispersal_view import render_dispersal_tab
from visualization.nlp_input_view import render_nlp_input
from visualization.transit_view import render_transit_view
from utils.live_traffic import fetch_live_traffic
from utils.transit_infrastructure import get_transit_pois
import json

st.set_page_config(
    page_title="EventFlow AI - Command Center",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background-color: var(--background-color);
    }
    
    section[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color) !important;
        border-right: 1px solid rgba(128, 128, 128, 0.1);
    }

    .logo-text {
        background: -webkit-linear-gradient(45deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.4rem;
        margin-bottom: 0px;
        padding-bottom: 0px;
        line-height: 1.1;
    }
    .logo-sub {
        color: var(--text-color);
        opacity: 0.6;
        font-size: 0.95rem;
        margin-bottom: 25px;
        font-weight: 300;
    }
    
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    div[data-testid="stMetricValue"] {
        color: var(--text-color);
        font-weight: 600;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-color);
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_graph():
    graph_path = os.path.join(os.path.dirname(__file__), "graph", "bengaluru_network.graphml")
    if os.path.exists(graph_path):
        return ox.load_graphml(graph_path)
    return None

with st.spinner('Loading City Digital Twin Graph...'):
    G = load_graph()

@st.cache_data
def get_road_options(_G):
    if _G is None:
        return {"None": None}
    roads = sim.get_major_roads(_G, num_roads=100)
    options = {"None": None}
    options.update(roads)
    return options

road_options = get_road_options(G)

st.sidebar.markdown('<div class="logo-text">EventFlow AI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="logo-sub">City-Scale Traffic Simulator</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🎛️ Event Settings")

st.sidebar.markdown("#### 📂 Load Custom Dataset")
uploaded_csv = st.sidebar.file_uploader("Upload Events CSV for testing", type=["csv"])
if uploaded_csv:
    st.sidebar.success(f"Successfully synced events from {uploaded_csv.name}")

# 1. Upcoming Events Feed
try:
    with open(os.path.join(os.path.dirname(__file__), "data", "upcoming_events.json"), "r") as f:
        upcoming_events = json.load(f)
    with st.sidebar.expander("📅 Upcoming City Events"):
        for ev in upcoming_events[:3]:
            st.markdown(f"**{ev['name']}**")
            st.caption(f"{ev['venue']} | {ev['date']} {ev['time']}")
            st.markdown("---")
except:
    pass

# 2. NLP Input
parsed_nlp = render_nlp_input()

event_types = [
    "🏟️ Cricket Match", "🚨 VIP Movement", "🎤 Public Concert",
    "📢 Protest/Rally", "🚧 Road Construction", "🕌 Religious Procession", "🌳 Tree Fall/Blockage"
]
venue_list = [
    "M Chinnaswamy Stadium (Central)", "Kanteerava Stadium (Central)",
    "Freedom Park (Central)", "Manyata Tech Park (North)",
    "Phoenix Marketcity Mall (East)", "Lalbagh Botanical Garden (South)",
    "IIM Bangalore (South)"
]

event_type_map = {
    "🏟️ Cricket Match": "sports", "🚨 VIP Movement": "vip_movement",
    "🎤 Public Concert": "public_event", "📢 Protest/Rally": "protest",
    "🚧 Road Construction": "construction", "🕌 Religious Procession": "religious",
    "🌳 Tree Fall/Blockage": "tree_fall"
}

# Update Session State if NLP was parsed
if parsed_nlp:
    v_lower = parsed_nlp['venue_name'].lower()
    for v in venue_list:
        if v_lower in v.lower() or v.lower() in v_lower or v_lower.split()[0] in v.lower():
            st.session_state['selected_venue_idx'] = venue_list.index(v)
            break
            
    e_map_rev = {v: k for k, v in event_type_map.items()}
    if parsed_nlp['event_type'] in e_map_rev:
        st.session_state['selected_event_idx'] = event_types.index(e_map_rev[parsed_nlp['event_type']])

# Default Indices
evt_idx = st.session_state.get('selected_event_idx', 0)
ven_idx = st.session_state.get('selected_venue_idx', 0)

event_type_ui = st.sidebar.selectbox("Event Category", event_types, index=evt_idx)
venue = st.sidebar.selectbox("Target Venue / Location", venue_list, index=ven_idx)

st.sidebar.markdown("#### 🕒 Event Schedule")
import datetime
col_d, col_t = st.sidebar.columns(2)
with col_d:
    event_date = st.date_input("Start Date", value=datetime.date.today())
with col_t:
    event_time = st.time_input("Start Time", value=datetime.time(18, 0))
    
duration_val = st.sidebar.slider("Duration (Hours)", min_value=1.0, max_value=12.0, value=4.0, step=0.5)

start_time_val = f"{event_date} {event_time}"
event_type_key = event_type_map[event_type_ui]

venue_coords = {
    "M Chinnaswamy Stadium (Central)": {"lat": 12.9788, "lng": 77.5996, "zone": "Central"},
    "Kanteerava Stadium (Central)": {"lat": 12.9694, "lng": 77.5938, "zone": "Central"},
    "Freedom Park (Central)": {"lat": 12.9782, "lng": 77.5815, "zone": "Central"},
    "Manyata Tech Park (North)": {"lat": 13.0450, "lng": 77.6200, "zone": "North"},
    "Phoenix Marketcity Mall (East)": {"lat": 12.9958, "lng": 77.6963, "zone": "East"},
    "Lalbagh Botanical Garden (South)": {"lat": 12.9507, "lng": 77.5844, "zone": "South"},
    "IIM Bangalore (South)": {"lat": 12.8950, "lng": 77.6010, "zone": "South"}
}

lat = venue_coords[venue]["lat"]
lng = venue_coords[venue]["lng"]
zone = venue_coords[venue]["zone"]

# Fetch nearby transit POIs for the selected venue
@st.cache_data
def get_venue_pois(lt, lg):
    return get_transit_pois(lt, lg, radius_km=2.5)

transit_points = get_venue_pois(lat, lng)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌩️ Environment Variables")
weather_rain = st.sidebar.toggle("Heavy Rain Forecast", value=False)
emergency_mode = st.sidebar.toggle("🚨 Emergency Routing Mode", value=False)
multi_event_mode = st.sidebar.toggle("💥 Multi-Event Simulator", value=False)
live_traffic_mode = st.sidebar.toggle("📡 Live Traffic Mode (TomTom)", value=False)

if multi_event_mode:
    st.sidebar.markdown("#### Secondary Event")
    sec_event_ui = st.sidebar.selectbox("Simultaneous Event", ["🚧 MG Road Construction", "📢 Freedom Park Protest"])
    sec_coords = {
        "🚧 MG Road Construction": {"lat": 12.9750, "lng": 77.6050, "zone": "Central", "type": "construction"},
        "📢 Freedom Park Protest": {"lat": 12.9782, "lng": 77.5815, "zone": "Central", "type": "protest"}
    }
    sec_lat = sec_coords[sec_event_ui]["lat"]
    sec_lng = sec_coords[sec_event_ui]["lng"]
    sec_zone = sec_coords[sec_event_ui]["zone"]
    sec_type = sec_coords[sec_event_ui]["type"]

prediction_data = predict_event_impact(
    event_type=event_type_key,
    latitude=lat,
    longitude=lng,
    zone=zone,
    start_time=start_time_val,
    duration_hours=duration_val
)

multi_event_data = None
if multi_event_mode:
    events = [
        {
            "event_type": event_type_map[event_type_ui],
            "latitude": lat, "longitude": lng, "zone": zone,
            "start_time": start_time_val, "duration_hours": duration_val
        },
        {
            "event_type": sec_type,
            "latitude": sec_lat, "longitude": sec_lng, "zone": sec_zone,
            "start_time": start_time_val, "duration_hours": duration_val
        }
    ]
    multi_event_data = predict_multi_event(events)
    prediction_data['total_incidents'] = multi_event_data['combined_total_incidents']
    prediction_data['confidence'] = multi_event_data['combined_confidence']

# Apply Weather Multiplier directly to core total before rendering
if weather_rain:
    prediction_data['total_incidents'] = int(prediction_data['total_incidents'] * 1.5)
    prediction_data['confidence'] = 0.65

# Re-calculate timeline based on final compounded/weather totals
from models.predict import get_phase_timeline, get_high_risk_junctions
prediction_data['timeline'] = get_phase_timeline(prediction_data['total_incidents'], start_time_val, duration_val)
prediction_data['high_risk_junctions'] = get_high_risk_junctions(lat, lng, prediction_data['total_incidents'])

# Extract timeline before passing prediction_data to visualizations that don't expect it
raw_timeline = prediction_data.pop("timeline", [])

# Call real ML backend for economic impact
real_econ = get_economic_impact(
    total_incidents=prediction_data['total_incidents'], 
    duration_hours=duration_val, 
    event_type=event_type_key
)

economic_impact = {
    "cost_lakhs": round(real_econ['total_cost_inr'] / 100000, 2),
    "person_hours": f"{int(real_econ['person_hours_lost']):,}",
    "surcharge_lakhs": round((real_econ['total_cost_inr'] / 10) / 100000, 2) if real_econ['total_cost_inr'] > 1000000 else 0.0,
    "surcharge_recommendation": real_econ['surcharge_recommendation']
}

@st.cache_data
def get_critical_roads_cached(_G, lat, lng):
    return sim.get_critical_roads(_G, lat, lng)

@st.cache_data
def get_emergency_routes_raw_cached(_G, lat, lng):
    return sim.get_emergency_routes(_G, lat, lng)

def _build_emergency_routes(G, lat, lng, emergency_mode):
    """
    Normalises the simulator output (which uses primary_path / detour_path)
    into the flat list-of-{path} dicts that render_folium_map expects.
    Falls back to hard-coded radial routes when the graph is unavailable.
    """
    if not emergency_mode:
        return None

    flat_routes = []

    if G:
        raw = get_emergency_routes_raw_cached(G, lat, lng)
        for r in raw:
            if r.get("primary_path"):
                flat_routes.append({"path": r["primary_path"]})
            if r.get("detour_path") and r["detour_path"] != r.get("primary_path"):
                flat_routes.append({"path": r["detour_path"]})

    # Fallback: synthetic radial evacuation corridors so the map always shows
    # something meaningful when the graph isn't loaded or routes are empty.
    if not flat_routes:
        import math
        num_spokes = 4
        spoke_len_deg = 0.018  # ~2 km
        for i in range(num_spokes):
            angle = math.radians(i * (360 / num_spokes))
            end_lat = lat + spoke_len_deg * math.cos(angle)
            end_lng = lng + spoke_len_deg * math.sin(angle)
            # 5-point smooth line
            flat_routes.append({
                "path": [
                    [lng, lat],
                    [lng + (end_lng - lng) * 0.25, lat + (end_lat - lat) * 0.25],
                    [lng + (end_lng - lng) * 0.50, lat + (end_lat - lat) * 0.50],
                    [lng + (end_lng - lng) * 0.75, lat + (end_lat - lat) * 0.75],
                    [end_lng, end_lat],
                ]
            })

    return flat_routes

critical_roads = get_critical_roads_cached(G, lat, lng) if G else None
emergency_routes = _build_emergency_routes(G, lat, lng, emergency_mode)

timeline_data = {
    "hours": [item["time"] for item in raw_timeline],
    "counts": [item["count"] for item in raw_timeline],
    "phases": [item["phase"] for item in raw_timeline]
}

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Map Settings")
view_mode = st.sidebar.radio("Map View Mode", ["3D Tilted View", "2D Top-Down View"])

tab_live, tab_tactical, tab_signals, tab_dispersal, tab_twin = st.tabs([
    "🚦 Live Dashboard", "📋 Tactical Plan", "🚥 Signals", "🏃 Crowd Dispersal", "⏳ Digital Twin"
])

with tab_live:
    col_main, col_cmd = st.columns([2.2, 1])

    with col_main:
        st.markdown("### 📊 Live Impact Metrics")
        
        if multi_event_mode and multi_event_data and multi_event_data['compounding_penalty_applied']:
            st.warning(f"⚠️ **Compounding Alert:** Overlapping events detected! Applied a {multi_event_data['penalty_multiplier']}x severity penalty.", icon="💥")

        # Get dynamic dispatch metrics
        dispatch = get_dispatch_recommendation(prediction_data['total_incidents'], prediction_data['confidence'])
        cap_loss = min(100, int((len(critical_roads) / max(1, len(road_options))) * 100)) if critical_roads else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="Predicted Incident Surge", value=f"+{prediction_data['total_incidents']}", delta="Critical", delta_color="inverse")
        m2.metric(label="Capacity Loss (Radius)", value=f"{cap_loss}%", delta="Dynamic", delta_color="inverse")
        m3.metric(label="Recommended Dispatch", value=f"{dispatch['total_units']} Units", delta=f"{dispatch['alert_level']} Alert", delta_color="off" if dispatch['alert_level']=="GREEN" else "inverse")
        m4.metric(label="Overall Risk Score", value=f"{int(prediction_data['confidence']*100)}/100", delta="High", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 🌐 Live Road Network")
        if emergency_mode:
            st.success("🟢 **Emergency Routing Mode Active** — Green corridors show designated evacuation routes.", icon="🚨")

        live_lines = fetch_live_traffic(lat, lng) if live_traffic_mode else None

        render_folium_map(
            lat=lat,
            lng=lng,
            prediction_data=prediction_data,
            critical_roads=critical_roads,
            emergency_routes=emergency_routes,
            live_traffic_lines=live_lines,
            height=500,
            venue_name=venue,
            transit_points=transit_points,
        )
        
        if G is None:
            st.error("Graph data not found. Please run `python graph/build_network.py`.")
            
        st.markdown("---")
        render_timeline(timeline_data)

    with col_cmd:
        render_command_center(prediction_data, G, road_options, economic_impact, critical_roads)

with tab_tactical:
    st.markdown("## 📋 Deployment & Tactical Plan")
    tactical = get_tactical_recommendation(prediction_data['total_incidents'], prediction_data.get('high_risk_junctions', []), duration_val)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Manpower Breakdown")
        mp = tactical['manpower']
        st.info(f"👮 Traffic Police: {mp['traffic_police']}")
        st.info(f"🚓 Patrol Vehicles: {mp['patrol_vehicles']}")
        st.info(f"🚑 Ambulances: {mp['ambulances']}")
        st.info(f"🚜 Tow Trucks: {mp['tow_trucks']}")
        st.info(f"🚧 Barricade Teams: {mp['barricade_teams']}")
        
        # Add dynamic pie chart
        from visualization.timeline import render_tactical_pie_chart
        st.markdown("<br>#### Resource Allocation", unsafe_allow_html=True)
        render_tactical_pie_chart(tactical)
        
    with col2:
        render_transit_view(venue, prediction_data['total_incidents'])
        signals = get_signal_recommendations(prediction_data.get('high_risk_junctions', []), prediction_data['total_incidents'])
        render_report_download(venue, event_type_key, prediction_data, economic_impact, tactical, signals, None)

with tab_signals:
    signals = get_signal_recommendations(prediction_data.get('high_risk_junctions', []), prediction_data['total_incidents'])
    render_signal_timing(signals)

with tab_dispersal:
    render_dispersal_tab(
        lat=lat,
        lng=lng,
        crowd_size=prediction_data['total_incidents'] * 150,
        G=G,
        event_type=event_type_key,
        venue_name=venue,
        total_incidents=prediction_data['total_incidents'],
    )

with tab_twin:
    render_digital_twin("EVT-4402", lat, lng, prediction_data, event_date=event_date)
