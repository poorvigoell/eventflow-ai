import streamlit as st
from utils.transit_estimator import estimate_transit_diversion

def render_transit_view(venue_name: str, total_incidents: int):
    """
    Renders the Metro Transit Diversion impact in the UI.
    """
    st.markdown("### 🚇 Public Transit Impact")
    
    if total_incidents == 0:
        st.info("No major traffic impact predicted, no metro diversion needed.")
        return
        
    transit_data = estimate_transit_diversion(venue_name, total_incidents)
    
    color_map = {"Purple": "#800080", "Green": "#008000", "None": "var(--text-color)"}
    bg_color = color_map.get(transit_data['line_color'], "gray")
    
    st.markdown(f"""
    <div style='background: var(--secondary-background-color); border-left: 4px solid {bg_color}; padding: 15px; border-radius: 5px; margin-bottom: 12px;'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <strong>Nearest Metro: {transit_data['nearest_station']}</strong>
            <span style='background:{bg_color}; color:white; padding:2px 8px; border-radius:12px; font-size:0.8rem;'>{transit_data['line_color']} Line</span>
        </div>
        <div style='margin-top: 10px; font-size: 0.95rem;'>
            🚶 Distance: <b>{transit_data['distance_km']} km</b><br/>
            👥 Potential Commuters Diverted: <b>{transit_data['divertable_commuters']:,}</b><br/>
            🚗 Cars Removed from Grid: <b>{transit_data['cars_removed_from_road']:,}</b><br/>
            ⚠️ Recommendation: <b style='color:#ff4b2b;'>{transit_data['recommended_frequency_increase']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
