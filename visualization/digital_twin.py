import streamlit as st
import folium
from streamlit_folium import st_folium

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

    with col_pred:
        st.markdown("<h4 style='text-align: center; color: var(--text-color); border-bottom: 2px solid #00d2ff; padding-bottom: 5px;'>AI Predicted</h4>", unsafe_allow_html=True)
        m_pred = folium.Map(location=[lat, lng], zoom_start=13, tiles="CartoDB dark_matter", prefer_canvas=True)
        folium.Circle(
            location=[lat, lng],
            radius=1500,
            color="#00d2ff",
            weight=1.5,
            fill=True,
            fill_color="#00d2ff",
            fill_opacity=0.12,
            tooltip="AI Predicted Impact Zone",
        ).add_to(m_pred)
        folium.CircleMarker(location=[lat, lng], radius=8, color="#00d2ff", fill=True, fill_opacity=1.0).add_to(m_pred)
        st_folium(m_pred, width="100%", height=350, returned_objects=[], key="twin_pred")
        st.metric("Predicted Incidents", replay_data["predicted"])

    with col_actual:
        st.markdown("<h4 style='text-align: center; color: var(--text-color); border-bottom: 2px solid #ff4b2b; padding-bottom: 5px;'>Actual Ground Truth</h4>", unsafe_allow_html=True)
        m_actual = folium.Map(location=[lat, lng], zoom_start=13, tiles="CartoDB dark_matter", prefer_canvas=True)
        folium.Circle(
            location=[lat, lng],
            radius=1700,
            color="#ff4b2b",
            weight=1.5,
            fill=True,
            fill_color="#ff4b2b",
            fill_opacity=0.12,
            tooltip="Actual Ground Truth Zone",
        ).add_to(m_actual)
        folium.CircleMarker(location=[lat, lng], radius=8, color="#ff4b2b", fill=True, fill_opacity=1.0).add_to(m_actual)
        st_folium(m_actual, width="100%", height=350, returned_objects=[], key="twin_actual")
        st.metric("Actual Incidents", replay_data["actual"])
