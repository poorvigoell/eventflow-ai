import math
import random

def simulate_dispersal(
    lat: float, lng: float,
    crowd_size: int = 30000,
    G=None,
    duration_minutes: int = 60,
    step_minutes: int = 5
) -> list[dict]:
    """
    Graph-based crowd dispersal model:
    - Finds nearest node to the venue in G.
    - Spreads crowd outwards along real road network edges using Dijkstra-style distance traversal.
    - If G is None, dynamically creates a simulated local grid network based on coordinates.
    """
    if crowd_size <= 0:
        return [{"time_min": 0, "points": [], "remaining_pct": 0.0}]

    snapshots = []
    
    # 1. Identify paths along actual road network G or construct a synthetic grid fallback
    paths_coords = []
    if G:
        try:
            import osmnx as ox
            import networkx as nx
            center_node = ox.distance.nearest_nodes(G, X=lng, Y=lat)
            n_data = G.nodes[center_node]
            
            # Check if nearest node is too far (e.g., > 1.5 km) indicating venue is outside graph bounds
            d_lat = (n_data['y'] - lat) * 111.0
            d_lng = (n_data['x'] - lng) * 111.0 * math.cos(math.radians(lat))
            dist_km = math.sqrt(d_lat**2 + d_lng**2)
            
            if dist_km > 1.5:
                # Too far, fall back to synthetic grid simulation centered on exact coordinates
                paths_coords = []
            else:
                # Find all reachable nodes within 3km of venue using shortest path distance
                sub_g = nx.ego_graph(G, center_node, radius=3000, distance='length')
                
                # Extract paths from ego graph center to boundary nodes
                boundary_nodes = [n for n, d in sub_g.nodes(data=True) if sub_g.degree(n) == 1 and n != center_node]
                if not boundary_nodes:
                    # If ego graph is small or closed, pick nodes at random levels
                    boundary_nodes = list(sub_g.nodes())[::min(5, len(sub_g))]
                
                for target in boundary_nodes[:20]: # Limit to 20 representative outbound paths
                    try:
                        path = nx.shortest_path(sub_g, center_node, target, weight='length')
                        path_c = []
                        for node in path:
                            node_data = sub_g.nodes[node]
                            path_c.append((node_data['y'], node_data['x']))
                        if len(path_c) > 1:
                            # Always prepend the exact venue coords so the
                            # heatmap originates from the venue pin, not the
                            # nearest graph node (which may be offset).
                            if path_c[0] != (lat, lng):
                                path_c.insert(0, (lat, lng))
                            paths_coords.append(path_c)
                    except nx.NetworkXNoPath:
                        continue
        except Exception as e:
            print(f"Error building graph dispersal: {e}")
            paths_coords = []

    # 2. Fallback: If graph G is unavailable or paths are empty, build a detailed grid-based road simulator
    if not paths_coords:
        # Standard Bangalore street grid (8 major road vectors starting from center)
        # Coordinates offsets representing realistic street routes
        num_spokes = 8
        for i in range(num_spokes):
            angle = math.radians(i * (360 / num_spokes))
            path_c = []
            # Create a path with 15 nodes extending 3 km outwards along this road angle
            # Add subtle curves to represent natural street alignment
            for step in range(16):
                d_km = (step * 0.2)
                curve = 0.02 * math.sin(step * 0.8) # S-curve offset
                p_lat = lat + d_km * (math.cos(angle) + curve * math.sin(angle)) / 111.0
                p_lng = lng + d_km * (math.sin(angle) - curve * math.cos(angle)) / (111.0 * math.cos(math.radians(lat)))
                path_c.append((p_lat, p_lng))
            paths_coords.append(path_c)

    # 3. Simulate crowd movement timestep snapshot by snapshot
    # Speed of pedestrians under crowd density: average ~3 km/h -> 0.05 km per minute
    base_speed_km_min = 0.06 

    for t in range(0, duration_minutes + 1, step_minutes):
        decay = math.exp(-t / 25.0)
        remaining_pct = round(max(0, decay * 100), 1)
        
        points = []
        # Group crowd to flow down identified road channels
        people_per_road = crowd_size / max(1, len(paths_coords))
        
        # Calculate crowd front distance at time t
        crowd_dist_km = t * base_speed_km_min
        
        for path in paths_coords:
            # Accumulate distances along path segment vertices
            accumulated_dist = 0.0
            for idx in range(len(path) - 1):
                p1 = path[idx]
                p2 = path[idx+1]
                
                # Approximate distance in km using Equirectangular projection
                d_lat = (p2[0] - p1[0]) * 111.0
                d_lng = (p2[1] - p1[1]) * (111.0 * math.cos(math.radians(p1[0])))
                seg_len = math.sqrt(d_lat**2 + d_lng**2)
                
                # Crowd fills this road segment
                if accumulated_dist <= crowd_dist_km:
                    # Interpolate density points along this active road segment
                    steps = max(2, int(seg_len / 0.15))
                    for step_idx in range(steps):
                        frac = step_idx / steps
                        interp_lat = p1[0] + frac * (p2[0] - p1[0])
                        interp_lng = p1[1] + frac * (p2[1] - p1[1])
                        
                        dist_from_venue = accumulated_dist + frac * seg_len
                        # Density fades exponentially as crowd spreads away from core venue
                        density = (people_per_road / max(1, crowd_size)) * math.exp(-dist_from_venue / 0.9) * decay
                        density = max(0, round(density, 4))
                        
                        if density > 0.001:
                            points.append({
                                "lat": round(interp_lat, 6),
                                "lng": round(interp_lng, 6),
                                "density": density
                            })
                
                accumulated_dist += seg_len
                if accumulated_dist > crowd_dist_km + 0.3: # Stop rendering past front boundary
                    break

        snapshots.append({
            "time_min": t,
            "points": points,
            "remaining_pct": remaining_pct
        })

    return snapshots
