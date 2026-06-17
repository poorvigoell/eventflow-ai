import streamlit as st

def render_signal_timing(signal_recommendations: list[dict]):
    """
    Renders the Adaptive Signal Control panel:
    - For each junction: junction name, cycle length, green/red progress bar, recommendation text
    """
    st.markdown("### 🚥 Adaptive Signal Control")
    st.markdown("""
    > [!TIP]
    > **How this works:** This module dynamically alters the green-light timing at critical junctions surrounding the venue to actively flush traffic based on the current event phase (e.g., extending green lights towards highways during the Exodus phase).
    """)
    st.caption("Optimal timing computed using Webster's Traffic Engineering Formula")

    if not signal_recommendations:
        st.info("Signal adjustments not required for low-impact events.")
        return

    for rec in signal_recommendations:
        cycle = rec["cycle_length_sec"]
        green_a = rec["phase_a_green_sec"]
        green_b = rec["phase_b_green_sec"]
        green_pct = green_a / cycle if cycle > 0 else 0.5

        st.markdown(f"""
        <div style='background: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2);
                    padding: 15px; border-radius: 10px; margin-bottom: 12px;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <strong style='color: var(--text-color);'>{rec['junction_name']}</strong>
                <span style='color: #00d2ff; font-size: 0.9rem;'>Cycle: {cycle}s</span>
            </div>
            <div style='display:flex; margin-top: 10px; border-radius: 4px; overflow: hidden; height: 12px;'>
                <div style='width:{green_pct*100:.0f}%; background: #00e676; box-shadow: 0 0 8px #00e676;'></div>
                <div style='width:{(1-green_pct)*100:.0f}%; background: #ff4b2b; box-shadow: 0 0 8px #ff4b2b;'></div>
            </div>
            <div style='display:flex; justify-content:space-between; margin-top:5px; font-size:0.8rem; color:var(--text-color); opacity:0.7;'>
                <span>🟢 Main: {green_a}s</span>
                <span>🔴 Cross: {green_b}s</span>
            </div>
            <div style='margin-top:8px; font-size:0.85rem; color:#00d2ff;'>💡 {rec['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)
