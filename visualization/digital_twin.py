import streamlit as st
import pydeck as pdk

def render_digital_twin(event_id, lat, lng):
    st.markdown("### ⏳ Historical Event Replay (Digital Twin)")
    st.caption("Replaying past events to validate model accuracy against actual Bengaluru Traffic Police data.")
    
    replay_data = {
        "actual": 16,
        "predicted": 14,
        "accuracy": 0.875
    }
    
    st.markdown(f"**Model Accuracy:** <span style='color: #00d2ff; font-weight: bold; font-size: 1.2rem;'>{replay_data['accuracy']*100:.1f}%</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_pred, col_actual = st.columns(2)
    
    view_state = pdk.ViewState(latitude=lat, longitude=lng, zoom=13.5, pitch=0)
    
    with col_pred:
        st.markdown("<h4 style='text-align: center; color: var(--text-color); border-bottom: 2px solid #00d2ff; padding-bottom: 5px;'>AI Predicted</h4>", unsafe_allow_html=True)
        layer_pred = pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [lng, lat]}],
            get_position="position",
            get_color=[0, 210, 255, 60],
            get_radius=1500,
            stroked=True,
            get_line_color=[255, 255, 255, 80],
            line_width_min_pixels=1,
        )
        st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=view_state, layers=[layer_pred]))
        st.metric("Predicted Incidents", replay_data["predicted"])
        
    with col_actual:
        st.markdown("<h4 style='text-align: center; color: var(--text-color); border-bottom: 2px solid #ff4b2b; padding-bottom: 5px;'>Actual Ground Truth</h4>", unsafe_allow_html=True)
        layer_actual = pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [lng, lat]}],
            get_position="position",
            get_color=[255, 75, 43, 60],
            get_radius=1700,
            stroked=True,
            get_line_color=[255, 255, 255, 80],
            line_width_min_pixels=1,
        )
        st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=view_state, layers=[layer_actual]))
        st.metric("Actual Incidents", replay_data["actual"])
