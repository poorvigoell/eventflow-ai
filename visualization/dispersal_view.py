import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from utils.dispersal_sim import simulate_dispersal

def render_dispersal_tab(lat: float, lng: float, crowd_size: int = 30000):
    """
    Full-page crowd dispersal visualization:
    - st.slider for "Minutes after event" (0 to 60, step 5)
    - Folium HeatMap showing crowd density at the selected snapshot
    - Metrics: remaining crowd %, estimated road clearance time
    """
    st.markdown("### 🏃 Crowd Dispersal Simulation")
    st.caption("Predicting outward crowd movement for 60 minutes post-event")

    time_min = st.slider(
        "Minutes after event ends",
        min_value=0, max_value=60, value=15, step=5,
        help="Slide to see how the crowd disperses over time"
    )

    @st.cache_data
    def get_dispersal(lat, lng, crowd_size):
        return simulate_dispersal(lat, lng, crowd_size)

    snapshots = get_dispersal(lat, lng, crowd_size)
    snapshot = next((s for s in snapshots if s["time_min"] == time_min), snapshots[0])

    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("Crowd Near Venue (<500m)", f"{snapshot['remaining_pct']:.0f}%")
    
    clearance_min = 0
    for s in snapshots:
        if s["remaining_pct"] < 10:
            clearance_min = s["time_min"]
            break
    if clearance_min == 0:
        clearance_min = 60
        
    col_metric2.metric("Est. Road Clearance", f"{clearance_min} min")

    m = folium.Map(location=[lat, lng], zoom_start=14, tiles="CartoDB dark_matter")
    
    folium.CircleMarker(location=[lat, lng], radius=8, color="#ff416c", fill=True, 
                         fill_opacity=1.0, tooltip="📍 Venue").add_to(m)

    if snapshot["points"]:
        heat_data = [[p["lat"], p["lng"], p["density"]] for p in snapshot["points"]]
        HeatMap(
            heat_data, radius=20, blur=15, max_zoom=16,
            gradient={0.2: '#00d2ff', 0.5: '#ffbb00', 0.8: '#ff4b2b', 1: '#ff0000'}
        ).add_to(m)

    st_folium(m, width="100%", height=450, returned_objects=[], key=f"dispersal_{time_min}")
