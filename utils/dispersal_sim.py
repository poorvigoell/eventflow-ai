import math
import random

def simulate_dispersal(
    lat: float, lng: float,
    crowd_size: int = 30000,
    G=None,
    duration_minutes: int = 120,
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

    # 2. Fallback: If graph G is unavailable or paths are empty, build Bangalore-specific corridor network
    if not paths_coords:
        # Real Bangalore major corridors and arteries (not radial spokes)
        # Mimics major road axes: N-S corridors, E-W corridors, diagonal arteries
        
        # Primary N-S corridors (Bangalore orientation)
        ns_corridors = [
            {'direction': (0, 1), 'offset': -0.015},      # Western corridor (MG Road-like)
            {'direction': (0, 1), 'offset': 0},           # Central corridor (Brigade Road)
            {'direction': (0, 1), 'offset': 0.015},       # Eastern corridor (Koramangala-like)
        ]
        
        # Primary E-W corridors
        ew_corridors = [
            {'direction': (1, 0), 'offset': -0.02},       # Northern corridor (Whitefield)
            {'direction': (1, 0), 'offset': 0},           # Central E-W (Bangalore-Mysore Road)
            {'direction': (1, 0), 'offset': 0.02},        # Southern corridor (HSR Layout)
        ]
        
        # Diagonal arterial roads (mimics ORR, peripheral highways)
        diagonal_corridors = [
            {'direction': (1, 1), 'offset': -0.01},       # NE-SW diagonal
            {'direction': (1, -1), 'offset': -0.01},      # NW-SE diagonal
        ]
        
        all_corridors = ns_corridors + ew_corridors + diagonal_corridors
        
        for corridor in all_corridors:
            direction = corridor['direction']
            offset = corridor['offset']
            path_c = []
            
            # Create 20-node path extending 4 km along each corridor
            # With jitter to represent street-level zigzags
            for step in range(21):
                dist_km = step * 0.2
                
                # Base corridor movement
                p_lat = lat + dist_km * direction[0] / 111.0 + offset
                p_lng = lng + dist_km * direction[1] / (111.0 * math.cos(math.radians(lat)))
                
                # Add realistic street jitter (crossroads, turns)
                jitter_scale = 0.003
                jitter_lat = jitter_scale * math.sin(step * 0.5) * math.cos(step * 0.3)
                jitter_lng = jitter_scale * math.cos(step * 0.5) * math.sin(step * 0.3)
                
                p_lat += jitter_lat
                p_lng += jitter_lng
                
                path_c.append((p_lat, p_lng))
            
            paths_coords.append(path_c)
        
        # Secondary roads branching off main corridors (minor dispersal routes)
        for i in range(6):
            angle = math.radians(i * 60)  # 6 branching angles
            path_c = []
            
            for step in range(12):
                dist_km = step * 0.25
                
                # Branch from center at an angle
                p_lat = lat + dist_km * math.cos(angle) / 111.0
                p_lng = lng + dist_km * math.sin(angle) / (111.0 * math.cos(math.radians(lat)))
                
                # Curved branch effect
                curve_factor = 0.005 * math.sin(step * 0.4)
                p_lat += curve_factor * math.sin(angle)
                p_lng += curve_factor * math.cos(angle)
                
                path_c.append((p_lat, p_lng))
            
            paths_coords.append(path_c)

    # 3. Simulate crowd movement timestep snapshot by snapshot
    # Pedestrian speed under crowd pressure: ~2-4 km/h, average ~3 km/h -> 0.05 km per minute
    # Faster initial exodus, then slowing as distance increases
    base_speed_km_min = 0.05 

    for t in range(0, duration_minutes + 1, step_minutes):
        # Exponential decay in crowd density at venue over time
        tau = max(15.0, min(120.0, 30.0 * (crowd_size / 30000.0) ** 0.5))
        decay = math.exp(-t / tau)
        remaining_pct = round(max(0, decay * 100), 1)
        
        points = []
        
        # Variable speed: faster early on (crowd panic), slower later (steady state)
        time_factor = 1.0 if t < 15 else 0.7
        
        # Crowd front propagates along roads
        # At t=0, crowd is at venue; spreads outward at 0.05 km/min = 3 km/hr
        crowd_front_km = t * base_speed_km_min * time_factor
        crowd_start_km = max(0, crowd_front_km - 0.2)  # Crowd occupies 200m wide band
        
        people_per_road = crowd_size / max(1, len(paths_coords))
        
        for path in paths_coords:
            # Traverse each road path and place density points
            accumulated_dist = 0.0
            for idx in range(len(path) - 1):
                p1 = path[idx]
                p2 = path[idx+1]
                
                # Equirectangular distance approximation
                d_lat = (p2[0] - p1[0]) * 111.0
                d_lng = (p2[1] - p1[1]) * (111.0 * math.cos(math.radians(p1[0])))
                seg_len = math.sqrt(d_lat**2 + d_lng**2)
                
                # Only render crowd that has reached this road segment
                if accumulated_dist <= crowd_front_km + 0.3:
                    # Interpolate density points densely along active road segments
                    steps = max(3, int(seg_len / 0.1))  # More points for better coverage
                    for step_idx in range(steps):
                        frac = step_idx / steps
                        interp_lat = p1[0] + frac * (p2[0] - p1[0])
                        interp_lng = p1[1] + frac * (p2[1] - p1[1])
                        
                        # Distance along this specific road from the venue
                        dist_along_road = accumulated_dist + frac * seg_len
                        
                        # Density is highest where crowd front is, tapers ahead and behind
                        if crowd_start_km <= dist_along_road <= crowd_front_km:
                            # Crowd is actively on this segment
                            density_factor = (people_per_road / crowd_size) * decay
                            # Peak at front, fade behind
                            dist_from_front = crowd_front_km - dist_along_road
                            density = density_factor * (1.0 - (dist_from_front / 0.3)) * math.exp(-t / 40.0)
                        elif dist_along_road < crowd_start_km:
                            # Behind the crowd front, lighter dispersed population
                            density = (people_per_road / crowd_size) * 0.3 * decay * math.exp(-dist_along_road / 1.5)
                        else:
                            # Ahead of crowd front, sparse scouts
                            density = (people_per_road / crowd_size) * 0.05 * math.exp(-(dist_along_road - crowd_front_km) / 0.5)
                        
                        density = max(0, round(density, 4))
                        
                        if density > 0.0005:  # Lower threshold for more visibility
                            points.append({
                                "lat": round(interp_lat, 6),
                                "lng": round(interp_lng, 6),
                                "density": density
                            })
                
                accumulated_dist += seg_len
                if accumulated_dist > crowd_front_km + 0.5:
                    break

        snapshots.append({
            "time_min": t,
            "points": points,
            "remaining_pct": remaining_pct
        })

    return snapshots
