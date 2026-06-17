import streamlit as st
import folium
from streamlit_folium import st_folium

def _risk_color(score):
    if score > 0.8:
        return "#ff3333"
    if score > 0.6:
        return "#ff9900"
    return "#ffcc00"

def render_folium_map(lat, lng, prediction_data, critical_roads=None, emergency_routes=None, live_traffic_lines=None, height=500, venue_name="Venue", transit_points=None):
    """
    Renders the Live Road Network map using Folium (Leaflet.js).
    Dynamically adjusts line thickness based on map zoom level.
    """
    # Track map center and zoom level in session state to handle dynamic sizing
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 14
    if "map_center" not in st.session_state:
        st.session_state.map_center = [lat, lng]

    # If coordinates changed (user selected different venue), reset center & zoom
    if abs(st.session_state.map_center[0] - lat) > 0.001 or abs(st.session_state.map_center[1] - lng) > 0.001:
        st.session_state.map_center = [lat, lng]
        st.session_state.map_zoom = 14

    # Calculate dynamic line weight based on current zoom
    # At zoom 14, weight = 5. Scales exponentially.
    zoom_level = st.session_state.map_zoom
    dynamic_weight = max(1.5, min(30.0, 5.0 * (2.0 ** (zoom_level - 14))))

    # Sync map theme with Streamlit
    theme_base = st.get_option("theme.base")
    tiles = "CartoDB positron" if theme_base == "light" else "CartoDB dark_matter"

    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles=tiles,
        prefer_canvas=True,
    )

    # --- Impact zone rings ---
    zones = [
        {"radius": 2500, "color": "#ff4b2b", "fill_opacity": 0.05, "label": "Outer Risk Zone (2.5km)"},
        {"radius": 1500, "color": "#00d2ff", "fill_opacity": 0.08, "label": "Event Inflow Zone (1.5km)"},
        {"radius": 800,  "color": "#ffbb00", "fill_opacity": 0.12, "label": "Critical Congestion Zone (800m)"},
    ]
    for z in zones:
        folium.Circle(
            location=[lat, lng],
            radius=z["radius"],
            color=z["color"],
            weight=1.5,
            fill=True,
            fill_color=z["color"],
            fill_opacity=z["fill_opacity"],
            tooltip=z["label"],
        ).add_to(m)

    # --- Venue pin ---
    folium.CircleMarker(
        location=[lat, lng],
        radius=9,
        color="#ff416c",
        fill=True,
        fill_color="#ff416c",
        fill_opacity=1.0,
        tooltip=f"📍 {venue_name}",
        popup="Event Venue",
    ).add_to(m)

    # --- Critical roads ---
    if critical_roads:
        for road in critical_roads:
            path = road.get("path", [])
            if len(path) < 2:
                continue
            latlngs = [[c[1], c[0]] for c in path]
            folium.PolyLine(
                locations=latlngs,
                color="#ff3333",
                weight=dynamic_weight,
                opacity=0.9,
                tooltip=f"🚨 Critical Road Segment (Congestion Risk: {road.get('score', 0):.2f})",
            ).add_to(m)

    # --- Emergency routes ---
    if emergency_routes:
        for route in emergency_routes:
            path = route.get("path", [])
            if len(path) < 2:
                continue
            latlngs = [[c[1], c[0]] for c in path]
            folium.PolyLine(
                locations=latlngs,
                color="#00ff88",
                weight=dynamic_weight,
                opacity=0.9,
                tooltip="Designated Emergency Route",
            ).add_to(m)

    # --- Live Traffic ---
    if live_traffic_lines:
        for route in live_traffic_lines:
            path = route.get("path", [])
            folium.PolyLine(
                locations=path,
                color=route.get("color", "#ffffff"),
                weight=dynamic_weight * 0.6,  # Slightly thinner than critical roads
                opacity=0.7,
                tooltip=f"Live Traffic: {route.get('level', 'unknown').title()}",
                dash_array='5, 5'  # dashed to distinguish from routes
            ).add_to(m)

    # --- Transit Infrastructure POIs ---
    if transit_points:
        for pt in transit_points:
            pt_type = pt.get("type", "bus")
            if pt_type == "metro":
                icon_color = "purple"
                icon_symbol = "subway"
                prefix = "fa"
            elif pt_type == "bus":
                icon_color = "blue"
                icon_symbol = "bus"
                prefix = "fa"
            else: # parking
                icon_color = "green"
                icon_symbol = "square" # fallback for standard parking sign
                prefix = "fa"
            
            folium.Marker(
                location=[pt["lat"], pt["lng"]],
                tooltip=pt["name"],
                icon=folium.Icon(color=icon_color, icon=icon_symbol, prefix=prefix)
            ).add_to(m)

    # --- High-risk junctions ---
    if "high_risk_junctions" in prediction_data:
        for j in prediction_data["high_risk_junctions"]:
            folium.CircleMarker(
                location=[j["lat"], j["lng"]],
                radius=7,
                color=_risk_color(j["risk_score"]),
                fill=True,
                fill_color=_risk_color(j["risk_score"]),
                fill_opacity=0.9,
                tooltip=f"⚠️ Junction: {j['name']} (Risk: {j['risk_score']})",
            ).add_to(m)

    # st_folium automatically triggers a rerun on zoom/pan events.
    # We update session_state values silently so they are used on the next automatic rerun.
    map_data = st_folium(m, width="100%", height=height, returned_objects=["zoom", "center"])
    
    if map_data:
        if "zoom" in map_data and map_data["zoom"] is not None:
            st.session_state.map_zoom = map_data["zoom"]
        if "center" in map_data and map_data["center"] is not None:
            st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
