"""
dispersal_view.py
Enhanced Crowd Dispersal tab:
  - Slider-driven heatmap, darkened near metro corridors based on economic score
  - Transit POIs (metro / bus / parking) overlaid as markers
  - Economic score panel + transport-mode breakdown
"""
import streamlit as st
import folium
from folium.plugins import HeatMap
import math

from utils.dispersal_sim import simulate_dispersal
from utils.transit_infrastructure import get_transit_pois, get_metro_corridor_points
from utils.economic_scorer import get_economic_score


# ── Distance helper ───────────────────────────────────────────────────────────

def _haversine_approx(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Fast equirectangular distance approximation in km."""
    d_lat = (lat2 - lat1) * 111.0
    d_lng = (lng2 - lng1) * 111.0 * math.cos(math.radians(lat1))
    return math.sqrt(d_lat * d_lat + d_lng * d_lng)


# ── Colour helpers ────────────────────────────────────────────────────────────

_SEGMENT_COLORS = {
    "Premium": ("#f7b731", "#f0932b"),   # gold → orange
    "Middle":  ("#00d2ff", "#3a7bd5"),   # cyan → blue
    "Mass":    ("#6c5ce7", "#a29bfe"),   # purple → lavender
}

_SEGMENT_ICONS = {
    "Premium": "💎",
    "Middle":  "🧑‍💼",
    "Mass":    "👥",
}

_TRANSPORT_COLORS = {
    "metro_pct": "#9b59b6",
    "cab_pct":   "#f39c12",
    "bus_pct":   "#27ae60",
    "walk_pct":  "#3498db",
}

_TRANSPORT_LABELS = {
    "metro_pct": "🚇 Metro",
    "cab_pct":   "🚕 Cab/Auto",
    "bus_pct":   "🚌 Bus",
    "walk_pct":  "🚶 Walk",
}


# ── POI marker helper ─────────────────────────────────────────────────────────

def _add_poi_markers(m: folium.Map, pois: list[dict]):
    """Add metro / bus / parking markers to a Folium map."""
    icon_cfg = {
        "metro":   ("purple", "subway",  "fa"),
        "bus":     ("blue",   "bus",     "fa"),
        "parking": ("green",  "car",     "fa"),
    }
    for pt in pois:
        cfg = icon_cfg.get(pt["type"], ("gray", "info-sign", "glyphicon"))
        line_label = f" ({pt.get('line', '')} Line)" if pt["type"] == "metro" and pt.get("line") else ""
        folium.Marker(
            location=[pt["lat"], pt["lng"]],
            tooltip=f"{pt['name']}{line_label} — {pt['dist_km']} km",
            icon=folium.Icon(color=cfg[0], icon=cfg[1], prefix=cfg[2]),
        ).add_to(m)


# ── Metro corridor weight injection ──────────────────────────────────────────

def _inject_metro_weights(
    heat_data: list[list],
    corridor_points: list[dict],
    weight_multiplier: float = 3.0,
):
    """
    Append extra high-weight heat points along metro corridors so the
    heatmap appears darker near metro lines.
    """
    for pt in corridor_points:
        heat_data.append([pt["lat"], pt["lng"], weight_multiplier])
    return heat_data


# ── Economic score card ───────────────────────────────────────────────────────

def _render_economic_panel(eco: dict):
    """Display the crowd economic profile as a styled card + transport bars."""
    segment = eco["segment"]
    c1, c2 = _SEGMENT_COLORS[segment]
    icon = _SEGMENT_ICONS[segment]

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {c1}22, {c2}11);
        border: 1px solid {c1}55;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 16px;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <p style="margin:0; font-size:0.8rem; opacity:0.7; text-transform:uppercase; letter-spacing:1px;">
                    Crowd Economic Segment
                </p>
                <h3 style="margin:4px 0 0 0; font-size:1.5rem; font-weight:800;">
                    {icon} {segment}
                </h3>
            </div>
            <div style="
                background: {c1};
                color: #fff;
                border-radius: 50%;
                width: 54px; height: 54px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.6rem; font-weight: 800;
            ">{int(eco['score'] * 100)}</div>
        </div>
        <div style="display:flex; gap:16px; margin-top:14px; font-size:0.88rem;">
            <span>💰 Rich: <b>{eco['rich_pct']}%</b></span>
            <span>🧑‍💼 Middle: <b>{eco['middle_pct']}%</b></span>
            <span>👷 Lower: <b>{eco['lower_pct']}%</b></span>
        </div>
        <div style="margin-top:6px; font-size:0.88rem;">
            🏆 Primary Mode: <b>{eco['primary_mode']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Transport split bar chart (pure CSS)
    st.markdown("**📊 Expected Transport Mode Split**")
    split = eco["transport_split"]
    bar_html = '<div style="display:flex; height:22px; border-radius:8px; overflow:hidden; margin-bottom:10px;">'
    for key, label in _TRANSPORT_LABELS.items():
        pct = split[key]
        if pct > 0:
            bar_html += (
                f'<div title="{label}: {pct}%" style="'
                f'width:{pct}%; background:{_TRANSPORT_COLORS[key]}; '
                f'display:flex; align-items:center; justify-content:center; '
                f'font-size:0.7rem; color:#fff; font-weight:700;">'
                + (f"{pct}%" if pct >= 10 else "") +
                "</div>"
            )
    bar_html += "</div>"
    st.markdown(bar_html, unsafe_allow_html=True)

    # Mode breakdown metric grid
    cols = st.columns(4)
    for i, (key, label) in enumerate(_TRANSPORT_LABELS.items()):
        cols[i].metric(label, f"{split[key]}%")


# ── Main render function ──────────────────────────────────────────────────────

def render_dispersal_tab(
    lat: float,
    lng: float,
    crowd_size: int = 30000,
    G=None,
    event_type: str = "sports",
    venue_name: str = "Venue",
    total_incidents: int = 200,
):
    """
    Full-page crowd dispersal visualization with:
    - Slider-driven heatmap weighted by economic score along metro corridors
    - Transit POI markers (metro / bus / parking)
    - Economic crowd profile + transport mode split
    """
    st.markdown("### 🏃 Crowd Dispersal Simulation")
    st.caption("Post-event crowd movement with economic-weighted transport corridors")

    # ── Compute economic profile (cached per event config) ───────────────────
    @st.cache_data
    def _cached_eco(et, vn, ti):
        return get_economic_score(et, vn, ti)

    eco = _cached_eco(event_type, venue_name, total_incidents)

    # ── Fetch nearby transit POIs ────────────────────────────────────────────
    @st.cache_data
    def _cached_pois(lt, lg):
        return get_transit_pois(lt, lg, radius_km=2.5)

    pois = _cached_pois(lat, lng)

    # ── Fetch metro corridor points (for heatmap weighting) ─────────────────
    @st.cache_data
    def _cached_corridors(lt, lg):
        return get_metro_corridor_points(lt, lg, radius_km=3.0)

    corridor_pts = _cached_corridors(lat, lng)

    # ── Controls: slider + metrics at the top ───────────────────────────────
    time_min = st.slider(
        "⏱️ Minutes after event ends",
        min_value=0, max_value=60, value=15, step=5,
        help="Slide to see crowd disperse over time",
    )

    @st.cache_data
    def get_dispersal(lt, lg, cs, _G=None, _version="v3"):
        return simulate_dispersal(lt, lg, cs, G=_G)

    snapshots = get_dispersal(lat, lng, crowd_size, _G=G)
    snapshot  = next((s for s in snapshots if s["time_min"] == time_min), snapshots[0])

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Crowd Near Venue (<500 m)", f"{snapshot['remaining_pct']:.0f}%")

    clearance_min = 60
    for s in snapshots:
        if s["remaining_pct"] < 10:
            clearance_min = s["time_min"]
            break
    m_col2.metric("Est. Road Clearance", f"{clearance_min} min")

    # Show POI counts in the remaining metric slots
    metro_ct = sum(1 for p in pois if p["type"] == "metro")
    bus_ct   = sum(1 for p in pois if p["type"] == "bus")
    park_ct  = sum(1 for p in pois if p["type"] == "parking")
    m_col3.metric("🟣 Metro Stations", metro_ct)
    m_col4.metric("🅿️ Bus + Parking", f"{bus_ct + park_ct}")

    # ── Build Folium map (FULL WIDTH — not inside st.columns) ────────────
    m = folium.Map(location=[lat, lng], zoom_start=14, tiles="CartoDB dark_matter", prefer_canvas=True)

    # Venue pin
    folium.CircleMarker(
        location=[lat, lng], radius=9,
        color="#ff416c", fill=True, fill_opacity=1.0,
        tooltip="📍 Event Venue",
    ).add_to(m)

    # Transit POI markers
    _add_poi_markers(m, pois)

    # Heatmap with optional metro corridor weighting
    if snapshot["points"]:
        heat_data = [[p["lat"], p["lng"], p["density"]] for p in snapshot["points"]]

        # Metro corridor injection — TIME-DEPENDENT
        # At t=0 nobody has left the venue, so inject zero metro weight.
        # Weight ramps linearly from 0 at t=0 to full strength by t=30 min.
        # Only inject at stations within walking distance (≈3 km/h walk speed).
        if time_min > 0 and eco["transport_split"]["metro_pct"] >= 30 and corridor_pts:
            time_ramp = min(1.0, time_min / 30.0)  # 0→1 over 30 minutes
            base_mult = 1.5 + (eco["transport_split"]["metro_pct"] - 30) * 0.065
            metro_weight = base_mult * time_ramp

            # Walking reach: ~0.05 km per minute
            walk_reach_km = time_min * 0.05
            reachable_pts = [
                pt for pt in corridor_pts
                if _haversine_approx(lat, lng, pt["lat"], pt["lng"]) <= walk_reach_km
            ]
            if reachable_pts:
                heat_data = _inject_metro_weights(heat_data, reachable_pts, metro_weight)

        HeatMap(
            heat_data,
            radius=20, blur=15, max_zoom=16,
            gradient={0.2: "#00d2ff", 0.5: "#ffbb00", 0.8: "#ff4b2b", 1.0: "#ff0000"},
        ).add_to(m)

    # Render map as raw HTML via st.components to guarantee correct sizing
    from streamlit.components.v1 import html as st_html
    map_html = m._repr_html_()
    st_html(map_html, height=480)

    # ── Economic panel + corridor info below the map ─────────────────────
    st.markdown("---")
    col_eco, col_transit = st.columns([1, 1])

    with col_eco:
        _render_economic_panel(eco)

    with col_transit:
        st.markdown("**🗺️ Nearby Transit Infrastructure (2.5 km)**")
        st.markdown(
            f"🟣 **{metro_ct}** Metro stations &nbsp;|&nbsp; "
            f"🔵 **{bus_ct}** Bus stops &nbsp;|&nbsp; "
            f"🟢 **{park_ct}** Parking lots",
            unsafe_allow_html=True,
        )

        if corridor_pts:
            lines_present = list({p["line"] for p in corridor_pts})
            st.info(
                f"Metro lines within 3 km: **{', '.join(lines_present)}** — "
                "heatmap is darker near these corridors."
            )
        else:
            st.caption("No metro corridors within 3 km of this venue.")
