import streamlit as st
import osmnx as ox
import pydeck as pdk
import os
import graph.simulator as sim
from visualization.shockwave import get_shockwave_layers
from visualization.timeline import render_timeline
from visualization.command_center import render_command_center
from visualization.digital_twin import render_digital_twin
from models.predict import predict_event_impact

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
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.15);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
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
    roads = sim.get_major_roads(_G, num_roads=15)
    options = {"None": None}
    options.update(roads)
    return options

road_options = get_road_options(G)

st.sidebar.markdown('<div class="logo-text">EventFlow AI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="logo-sub">City-Scale Traffic Simulator</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🎛️ Event Settings")
event_type_ui = st.sidebar.selectbox("Event Category", ["🏟️ Cricket Match", "🚨 VIP Movement", "🎤 Public Concert"])
venue = st.sidebar.selectbox("Target Venue", ["M Chinnaswamy Stadium", "Kanteerava Stadium"])

event_type_map = {
    "🏟️ Cricket Match": "sports",
    "🚨 VIP Movement": "vip_movement",
    "🎤 Public Concert": "public_event"
}

venue_coords = {
    "M Chinnaswamy Stadium": {"lat": 12.9788, "lng": 77.5996, "zone": "Central"},
    "Kanteerava Stadium": {"lat": 12.9694, "lng": 77.5938, "zone": "Central"}
}

lat = venue_coords[venue]["lat"]
lng = venue_coords[venue]["lng"]
zone = venue_coords[venue]["zone"]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌩️ Environment Variables")
weather_rain = st.sidebar.toggle("Heavy Rain Forecast", value=False)
emergency_mode = st.sidebar.toggle("🚨 Emergency Routing Mode", value=False)
multi_event_mode = st.sidebar.toggle("💥 Multi-Event Simulator", value=False)

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

from models.predict import predict_event_impact, get_economic_impact, predict_multi_event

prediction_data = predict_event_impact(
    event_type=event_type_map[event_type_ui],
    latitude=lat,
    longitude=lng,
    zone=zone,
    start_time="2024-03-15 18:00:00",
    duration_hours=4.0
)

multi_event_data = None
if multi_event_mode:
    events = [
        {
            "event_type": event_type_map[event_type_ui],
            "latitude": lat, "longitude": lng, "zone": zone,
            "start_time": "2024-03-15 18:00:00", "duration_hours": 4.0
        },
        {
            "event_type": sec_type,
            "latitude": sec_lat, "longitude": sec_lng, "zone": sec_zone,
            "start_time": "2024-03-15 18:00:00", "duration_hours": 4.0
        }
    ]
    multi_event_data = predict_multi_event(events)
    # Override primary prediction with combined totals
    prediction_data['total_incidents'] = multi_event_data['combined_total_incidents']
    prediction_data['confidence'] = multi_event_data['combined_confidence']

# Extract timeline before passing prediction_data to visualizations that don't expect it
raw_timeline = prediction_data.pop("timeline", [])

if weather_rain:
    prediction_data['total_incidents'] = int(prediction_data['total_incidents'] * 1.3)
    prediction_data['confidence'] = 0.65

# Call real ML backend for economic impact
real_econ = get_economic_impact(
    total_incidents=prediction_data['total_incidents'], 
    duration_hours=4.0, 
    event_type=event_type_map[event_type_ui]
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
def get_emergency_routes_cached(_G, lat, lng):
    return sim.get_emergency_routes(_G, lat, lng)

critical_roads = get_critical_roads_cached(G, lat, lng) if G else None
emergency_routes = get_emergency_routes_cached(G, lat, lng) if emergency_mode and G else None

timeline_data = {
    "hours": [item["time"] for item in raw_timeline],
    "counts": [item["count"] for item in raw_timeline],
    "phases": [item["phase"] for item in raw_timeline]
}

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Map Settings")
view_mode = st.sidebar.radio("Map View Mode", ["3D Tilted View", "2D Top-Down View"])

tab_live, tab_twin = st.tabs(["🚦 Live Command Center", "⏳ Digital Twin (Replay)"])

with tab_live:
    col_main, col_cmd = st.columns([2.2, 1])

    with col_main:
        st.markdown("### 📊 Live Impact Metrics")
        
        if multi_event_mode and multi_event_data and multi_event_data['compounding_penalty_applied']:
            st.warning(f"⚠️ **Compounding Alert:** Overlapping events detected! Applied a {multi_event_data['penalty_multiplier']}x severity penalty.", icon="💥")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="Predicted Incident Surge", value=f"+{prediction_data['total_incidents']}", delta="Critical", delta_color="inverse")
        m2.metric(label="Capacity Loss (Radius)", value="38%", delta="-12% from baseline", delta_color="inverse")
        m3.metric(label="Recommended Dispatch", value="12 Units", delta="Traffic Police")
        m4.metric(label="Overall Risk Score", value=f"{int(prediction_data['confidence']*100)}/100", delta="High", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 🌐 Live Road Network")

        pitch = 50 if "3D" in view_mode else 0
        bearing = -15 if "3D" in view_mode else 0

        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lng,
            zoom=14.5,
            pitch=pitch,
            bearing=bearing
        )

        layers = get_shockwave_layers(lat, lng, prediction_data, critical_roads, emergency_routes)

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=layers,
            tooltip={"text": "{name}"}
        ))
        
        if G is None:
            st.error("Graph data not found. Please run `python graph/build_network.py`.")
            
        st.markdown("---")
        render_timeline(timeline_data)

    with col_cmd:
        render_command_center(prediction_data, G, road_options, economic_impact, critical_roads)

with tab_twin:
    render_digital_twin("EVT-4402", lat, lng)
 
