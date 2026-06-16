import streamlit as st
import graph.simulator as sim

def render_command_center(prediction_data, G, road_options, economic_impact=None, critical_roads=None):
    st.markdown("### 🎯 Tactical Command")
    
    st.markdown("#### Phase Analysis")
    phases = prediction_data.get("phases", {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='background: rgba(0, 210, 255, 0.1); border-left: 3px solid #00d2ff; padding: 10px; border-radius: 4px; font-size: 0.85rem;'><b>Inflow</b><br>Peak: {}<br>{}</div>".format(phases.get("inflow", {}).get("peak_hour", "-"), phases.get("inflow", {}).get("top_type", "-").replace("_", " ").title()), unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='background: rgba(255, 187, 0, 0.1); border-left: 3px solid #ffbb00; padding: 10px; border-radius: 4px; font-size: 0.85rem;'><b>Steady</b><br>Peak: {}<br>{}</div>".format(phases.get("steady", {}).get("peak_hour", "-"), phases.get("steady", {}).get("top_type", "-").replace("_", " ").title()), unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='background: rgba(255, 75, 43, 0.1); border-left: 3px solid #ff4b2b; padding: 10px; border-radius: 4px; font-size: 0.85rem;'><b>Exodus</b><br>Peak: {}<br>{}</div>".format(phases.get("exodus", {}).get("peak_hour", "-"), phases.get("exodus", {}).get("top_type", "-").replace("_", " ").title()), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### 🚨 High Risk Junctions")
    junctions = prediction_data.get("high_risk_junctions", [])
    
    for idx, j in enumerate(junctions):
        score = j["risk_score"] * 100
        color = "#ff4b2b" if score > 80 else "#ffbb00" if score > 60 else "#00d2ff"
        
        st.markdown(f"""
        <div style='background: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); padding: 12px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='color: var(--text-color); font-size: 0.95rem;'>{j['name']}</strong>
                <span style='color: {color}; font-weight: bold; font-size: 0.9rem;'>{score:.0f}% Risk</span>
            </div>
            <div style='width: 100%; background: rgba(128,128,128,0.2); border-radius: 4px; height: 6px; margin-top: 8px;'>
                <div style='width: {score}%; background: {color}; height: 100%; border-radius: 4px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    if economic_impact:
        st.markdown("#### 💰 Economic Impact Estimate")
        st.markdown(f"""
        <div style='background: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                <span style='color: var(--text-color);'>Estimated Cost:</span>
                <strong style='color: #ff4b2b; font-size: 1.1rem;'>₹{economic_impact['cost_lakhs']} Lakhs</strong>
            </div>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                <span style='color: var(--text-color);'>Lost Productivity:</span>
                <strong style='color: var(--text-color);'>{economic_impact['person_hours']} hrs</strong>
            </div>
            <hr style='border: none; border-top: 1px solid rgba(128,128,128,0.2); margin: 10px 0;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='color: var(--text-color); font-weight: bold;'>Recommended Surcharge:</span>
                <strong style='color: #00d2ff;'>₹{economic_impact['surcharge_lakhs']} Lakhs</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    if critical_roads:
        st.markdown("#### ⚡ Cascading Failure Warning")
        st.error(f"{len(critical_roads)} critical choke points detected! See glowing red routes on the map.")
        
    st.markdown("---")
    st.markdown("### 🚧 What-If Simulator")
    st.caption("Powered by NetworkX Dijkstra Algorithm")
    road_name = st.selectbox("Target Edge for Closure", list(road_options.keys()), key="cmd_road_select")
    
    simulate_btn = st.button("Execute Simulation", type="primary", use_container_width=True, key="cmd_sim_btn")
    
    if simulate_btn and road_name != "None" and G is not None:
        with st.spinner(f"Simulating closure of {road_name}..."):
            edge_to_close = road_options[road_name]
            results = sim.simulate_road_closure(G, edge_to_close)
            
            st.markdown("#### Simulation Results")
            if "error" in results:
                st.error(results["error"])
            else:
                pct = results["change_pct"]
                st.metric(label="Network Travel Time Change", value=f"{pct:+.1f}%")
                st.write(f"Impacted Routes: **{results['impacted_routes']} / {results['total_routes']}**")
                
                if "DO NOT CLOSE" in results["recommendation"]:
                    st.error(results["recommendation"])
                else:
                    st.success(results["recommendation"])
    elif simulate_btn and road_name == "None":
        st.warning("Please select a road to simulate.")
