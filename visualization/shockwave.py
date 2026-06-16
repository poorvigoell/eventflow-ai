import pydeck as pdk

def get_shockwave_layers(lat, lng, prediction_data, critical_roads=None, emergency_routes=None):
    layers = []
    
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [lng, lat], "name": "Venue"}],
        get_position="position",
        get_color=[255, 65, 108, 255],
        get_radius=150,
        pickable=True,
    ))
    
    phases = [
        {"radius": 1500, "color": [0, 210, 255, 40]},
        {"radius": 800, "color": [255, 187, 0, 60]},
        {"radius": 2500, "color": [255, 75, 43, 30]},
    ]
    
    for phase in phases:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [lng, lat]}],
            get_position="position",
            get_color=phase["color"],
            get_radius=phase["radius"],
            stroked=True,
            get_line_color=[255, 255, 255, 80],
            line_width_min_pixels=1,
            pickable=False,
        ))
        
    if "high_risk_junctions" in prediction_data:
        junctions = prediction_data["high_risk_junctions"]
        
        def get_risk_color(score):
            if score > 0.8: return [255, 0, 0, 200]
            if score > 0.6: return [255, 165, 0, 200]
            return [255, 255, 0, 200]
            
        for j in junctions:
            j["color"] = get_risk_color(j["risk_score"])
            
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=junctions,
            get_position="[lng, lat]",
            get_color="color",
            get_radius=80,
            pickable=True,
        ))
        
    if critical_roads:
        layers.append(pdk.Layer(
            "PathLayer",
            data=critical_roads,
            pickable=True,
            get_color=[255, 0, 0, 200], # Glowing red
            width_scale=20,
            width_min_pixels=4,
            get_path="path",
            get_width=5,
        ))
        
    if emergency_routes:
        layers.append(pdk.Layer(
            "PathLayer",
            data=emergency_routes,
            pickable=True,
            get_color=[0, 255, 0, 200], # Glowing green for ambulance
            width_scale=20,
            width_min_pixels=3,
            get_path="path",
            get_width=5,
        ))
        
    return layers
