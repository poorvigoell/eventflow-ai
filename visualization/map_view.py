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

    import os
    import json
    boundary_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "graph", "bengaluru_boundary.geojson")
    if os.path.exists(boundary_path):
        try:
            with open(boundary_path, "r") as f:
                boundary_data = json.load(f)
            folium.GeoJson(
                boundary_data,
                name="Bengaluru Boundary",
                style_function=lambda x: {'color': '#00d2ff', 'weight': 2, 'fillColor': 'transparent', 'dashArray': '5, 5'},
                interactive=False
            ).add_to(m)
        except Exception as e:
            pass



    # --- Impact zone rings ---
    zones = [
        {"radius": 2500, "color": "#ff4b2b", "fill_opacity": 0.05, "label": "Outer Risk Zone (2.5km)"},
        {"radius": 1500, "color": "#00d2ff", "fill_opacity": 0.08, "label": "Event Inflow Zone (1.5km)"},
        {"radius": 800,  "color": "#ffbb00", "fill_opacity": 0.12, "label": "Critical Congestion Zone (800m)"},
    ]
    for z in zones:
        circle = folium.Circle(
            location=[lat, lng],
            radius=z["radius"],
            color=z["color"],
            weight=1.5,
            fill=True,
            fill_color=z["color"],
            fill_opacity=z["fill_opacity"],
            tooltip=z["label"],
        )
        # Prevent circle overlays from capturing pointer events
        circle.options['interactive'] = False
        circle.add_to(m)

    # --- Venue pin (emoji marker) ---
    pin_icon = folium.DivIcon(
        html='<div style="font-size: 32px; line-height: 1; text-shadow: 0 2px 6px rgba(0,0,0,0.5); transform: translate(-12px, -32px);">📍</div>',
        icon_size=(32, 32),
        icon_anchor=(0, 0),
    )
    folium.Marker(
        location=[lat, lng],
        icon=pin_icon,
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
        _transit_emoji = {"metro": "🚇", "bus": "🚌", "parking": "🅿️"}
        _transit_colors = {"metro": "#a855f7", "bus": "#3b82f6", "parking": "#22c55e"}
        for pt in transit_points:
            pt_type = pt.get("type", "bus")
            emoji = _transit_emoji.get(pt_type, "📌")
            bg = _transit_colors.get(pt_type, "#666")
            dist_label = f" ({pt['dist_km']} km)" if "dist_km" in pt else ""
            poi_icon = folium.DivIcon(
                html=f'<div style="font-size:18px;background:{bg};border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.4);border:2px solid #fff;">{emoji}</div>',
                icon_size=(28, 28),
                icon_anchor=(14, 14),
            )
            folium.Marker(
                location=[pt["lat"], pt["lng"]],
                tooltip=f"{emoji} {pt['name']}{dist_label}",
                icon=poi_icon,
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

    # st_folium automatically triggers a rerun on zoom/pan/click events.
    # We update session_state values silently so they are used on the next automatic rerun.
    map_data = st_folium(m, width="100%", height=height, returned_objects=["zoom", "center", "last_clicked"], key="main_map")
    
    if map_data:
        if "zoom" in map_data and map_data["zoom"] is not None:
            st.session_state.map_zoom = map_data["zoom"]
        if "center" in map_data and map_data["center"] is not None:
            st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]

    return map_data

