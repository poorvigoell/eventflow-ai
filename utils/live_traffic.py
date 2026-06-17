import random

def fetch_live_traffic(lat: float, lng: float, radius_km: float = 2.0) -> list[dict]:
    """
    Mocks a TomTom API call for live traffic flow around a venue.
    Returns a list of PolyLines with congestion levels.
    """
    # Use deterministic random seed based on coordinates so the "live" traffic
    # looks stable for the same venue during the demo
    random.seed(int(lat * 10000 + lng * 10000))
    lines = []
    
    num_roads = random.randint(8, 15)
    for _ in range(num_roads):
        # Start point near venue
        dlat = (random.random() - 0.5) * (radius_km / 111.0) * 2
        dlng = (random.random() - 0.5) * (radius_km / 111.0) * 2
        start_lat = lat + dlat
        start_lng = lng + dlng
        
        # End point (short distance away to form a line segment)
        end_lat = start_lat + (random.random() - 0.5) * 0.015
        end_lng = start_lng + (random.random() - 0.5) * 0.015
        
        # Weighted random choice for congestion
        congestion_level = random.choices(
            ["low", "moderate", "high", "severe"], 
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        
        color_map = {"low": "#00e676", "moderate": "#ffbb00", "high": "#ff4b2b", "severe": "#8b0000"}
        
        lines.append({
            "path": [(start_lat, start_lng), (end_lat, end_lng)],
            "level": congestion_level,
            "color": color_map[congestion_level]
        })
        
    return lines
