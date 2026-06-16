import streamlit as st
import osmnx as ox
import pydeck as pdk
import os
import graph.simulator as sim

st.set_page_config(
    page_title="EventFlow AI - Command Center",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background: radial-gradient(circle at top left, #12141d, #050505);
    }
    
    section[data-testid="stSidebar"] {
        background-color: rgba(18, 20, 29, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    .logo-text {
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.4rem;
        margin-bottom: 0px;
        padding-bottom: 0px;
        line-height: 1.1;
    }
    .logo-sub {
        color: #a0aabf;
        font-size: 0.95rem;
        margin-bottom: 25px;
        font-weight: 300;
    }
    
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(4px);
    }
    
    div[data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: 600;
    }
    div[data-testid="stMetricLabel"] {
        color: #a0aabf;
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

# -----------------
# SIDEBAR (Top Left)
# -----------------
st.sidebar.markdown('<div class="logo-text">EventFlow AI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="logo-sub">City-Scale Traffic Simulator</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🎛️ Event Settings")
event_type = st.sidebar.selectbox("Event Category", ["🏟️ Cricket Match", "🚨 VIP Movement", "🎤 Public Concert"])
venue = st.sidebar.selectbox("Target Venue", ["M Chinnaswamy Stadium", "Kanteerava Stadium"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚧 What-If Simulator")
st.sidebar.caption("Powered by NetworkX Dijkstra Algorithm")
road_name = st.sidebar.selectbox("Target Edge for Closure", list(road_options.keys()))

simulate_btn = st.sidebar.button("Execute Simulation", type="primary", use_container_width=True)

if simulate_btn and road_name != "None" and G is not None:
    with st.spinner(f"Simulating closure of {road_name} across city network..."):
        edge_to_close = road_options[road_name]
        results = sim.simulate_road_closure(G, edge_to_close)
        
        st.sidebar.markdown("#### Simulation Results")
        if "error" in results:
            st.sidebar.error(results["error"])
        else:
            pct = results["change_pct"]
            st.sidebar.metric(label="Network Travel Time Change", value=f"{pct:+.1f}%")
            st.sidebar.write(f"Impacted Routes: **{results['impacted_routes']} / {results['total_routes']}**")
            
            if "DO NOT CLOSE" in results["recommendation"]:
                st.sidebar.error(results["recommendation"])
            else:
                st.sidebar.success(results["recommendation"])
elif simulate_btn and road_name == "None":
    st.sidebar.warning("Please select a road to simulate.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Map Settings")
view_mode = st.sidebar.radio("Map View Mode", ["3D Tilted View", "2D Top-Down View"])


# -----------------
# MAIN CONTENT
# -----------------
st.markdown("### 📊 Live Impact Metrics")
m1, m2, m3, m4 = st.columns(4)
m1.metric(label="Predicted Incident Surge", value="+14", delta="Critical", delta_color="inverse")
m2.metric(label="Capacity Loss (Radius)", value="38%", delta="-12% from baseline", delta_color="inverse")
m3.metric(label="Recommended Dispatch", value="12 Units", delta="Traffic Police")
m4.metric(label="Overall Risk Score", value="84/100", delta="High", delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("### 🌐 Live Road Network")

pitch = 50 if "3D" in view_mode else 0
bearing = -15 if "3D" in view_mode else 0

view_state = pdk.ViewState(
    latitude=12.9788,
    longitude=77.5996,
    zoom=14.5,
    pitch=pitch,
    bearing=bearing
)

stadium_layer = pdk.Layer(
    "ScatterplotLayer",
    data=[{"position": [77.5996, 12.9788], "name": "M Chinnaswamy Stadium"}],
    get_position="position",
    get_color=[255, 65, 108, 200], # Pink glow
    get_radius=120,
    pickable=True,
)

st.pydeck_chart(pdk.Deck(
    map_style="dark",
    initial_view_state=view_state,
    layers=[stadium_layer],
    tooltip={"text": "{name}"}
))

if G is None:
    st.error("Graph data not found. Please run `python graph/build_network.py`.")
