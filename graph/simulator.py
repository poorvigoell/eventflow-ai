import networkx as nx
import random
import osmnx as ox

_CRITICAL_ROADS_CACHE = {}
_EMERGENCY_ROUTES_CACHE = {}

def simulate_road_closure(G, edge_to_close, num_samples=50, seed=42):
    """
    Simulates the impact of closing a road (edge) on the given networkx graph G.
    Calculates the shortest paths for random O-D pairs before and after the closure.
    """
    random.seed(seed)
    nodes = list(G.nodes())
    
    # Generate origin-destination pairs that actually have paths
    od_pairs = []
    attempts = 0
    while len(od_pairs) < num_samples and attempts < 300:
        u, v = random.sample(nodes, 2)
        try:
            # check if path exists
            _ = nx.shortest_path_length(G, u, v, weight='travel_time')
            od_pairs.append((u, v))
        except nx.NetworkXNoPath:
            pass
        attempts += 1
        
    if not od_pairs:
        return {"error": "Could not find valid OD pairs"}

    # Calculate BEFORE times
    before_times = []
    for u, v in od_pairs:
        t = nx.shortest_path_length(G, u, v, weight='travel_time')
        before_times.append(t)
        
    avg_before = sum(before_times) / len(before_times)
    
    # Copy graph and remove edge
    G_sim = G.copy()
    
    u, v = edge_to_close[0], edge_to_close[1]
    if G_sim.has_edge(u, v):
        keys = list(G_sim[u][v].keys())
        for k in keys:
            G_sim.remove_edge(u, v, key=k)
            
    # Calculate AFTER times
    after_times = []
    impacted_pairs = 0
    for i, (src, dst) in enumerate(od_pairs):
        try:
            t = nx.shortest_path_length(G_sim, src, dst, weight='travel_time')
            after_times.append(t)
            if t > before_times[i] + 1.0: # 1 second tolerance
                impacted_pairs += 1
        except nx.NetworkXNoPath:
            # If path broken completely, give it a large penalty (e.g. 5x original)
            after_times.append(before_times[i] * 5)
            impacted_pairs += 1
            
    avg_after = sum(after_times) / len(after_times)
    
    change_pct = ((avg_after - avg_before) / avg_before) * 100 if avg_before > 0 else 0
    
    return {
        "avg_before_secs": avg_before,
        "avg_after_secs": avg_after,
        "change_pct": change_pct,
        "impacted_routes": impacted_pairs,
        "total_routes": len(od_pairs),
        "recommendation": "⚠️ DO NOT CLOSE" if change_pct > 2.0 else "✅ SAFE TO CLOSE"
    }

def get_major_roads(G, num_roads=10):
    """
    Finds a few major roads in the graph to populate the UI dropdown.
    Returns a dictionary of { Road_Name: (u, v) }
    """
    road_dict = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        name = data.get('name', 'Unknown Road')
        if isinstance(name, list):
            name = name[0]
            
        if name != 'Unknown Road' and 'highway' in data:
            hw = data['highway']
            if hw in ['primary', 'secondary', 'trunk']:
                if name not in road_dict:
                    road_dict[name] = (u, v)
                if len(road_dict) >= num_roads:
                    break
    return road_dict


def get_edge_name(edge_data):
    name = edge_data.get('name')
    if isinstance(name, list):
        name = name[0] if name else None

    if not name or name == 'Unknown Road':
        highway = edge_data.get('highway')
        if isinstance(highway, list):
            highway = highway[0]
        if highway:
            name = f"{highway.title()} Road"
        else:
            name = "Unnamed Road"

    return name


def find_nearest_node(G, lat, lng):
    try:
        return ox.distance.nearest_nodes(G, X=lng, Y=lat)
    except Exception:
        try:
            return ox.distance.nearest_nodes(G, X=lng, Y=lat)
        except Exception:
            return min(
                G.nodes(),
                key=lambda n: (G.nodes[n].get('x', 0) - lng) ** 2 + (G.nodes[n].get('y', 0) - lat) ** 2
            )


def _path_road_names(G, path):
    """Return cleaned road names along a node path."""
    road_names = []
    for u, v in zip(path[:-1], path[1:]):
        edge_data = G.get_edge_data(u, v)
        if not edge_data:
            continue
        # Select the first available edge key
        first_key = next(iter(edge_data))
        name = get_edge_name(edge_data[first_key])
        if name and (not road_names or name != road_names[-1]):
            road_names.append(name)
    return road_names


def _path_travel_time(G, path):
    total = 0.0
    for u, v in zip(path[:-1], path[1:]):
        edge_data = G.get_edge_data(u, v)
        if not edge_data:
            continue
        first_key = next(iter(edge_data))
        total += edge_data[first_key].get('travel_time', 1.0)
    return total


def get_high_risk_junctions_graph(G, lat, lng, total_incidents, max_junctions=5, radius=1000):
    """
    Identify nearby high-risk junctions using graph centrality and event location.
    """
    if total_incidents < 3 or G is None:
        return []

    try:
        center_node = find_nearest_node(G, lat, lng)
        subgraph = nx.ego_graph(G, center_node, radius=radius, distance='length')
        if len(subgraph) < 3:
            return []

        k_val = min(30, len(subgraph.nodes))
        centrality = nx.edge_betweenness_centrality(subgraph, weight='travel_time', k=k_val)
        risk_candidates = []
        seen_names = set()

        for edge_key, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
            if len(edge_key) == 3:
                u, v, k = edge_key
            else:
                u, v = edge_key
                k = 0
            edge_data = subgraph[u][v][k]
            name = get_edge_name(edge_data)
            if name in seen_names:
                continue
            seen_names.add(name)

            try:
                u_data = subgraph.nodes[u]
                v_data = subgraph.nodes[v]
                lat_center = float((u_data.get('y', 0) + v_data.get('y', 0)) / 2)
                lng_center = float((u_data.get('x', 0) + v_data.get('x', 0)) / 2)
            except Exception:
                lat_center = lat
                lng_center = lng

            risk_score = min(0.99, 0.3 + score * 2.0 + min(0.3, total_incidents / 40.0))
            risk_candidates.append({
                "name": name,
                "lat": lat_center,
                "lng": lng_center,
                "risk_score": round(risk_score, 2),
                "u": u,
                "v": v,
                "key": k,
                "centrality": score,
            })
            if len(risk_candidates) >= max_junctions:
                break

        return risk_candidates
    except Exception as e:
        print(f"Error computing graph high-risk junctions: {e}")
        return []


def get_barricade_recommendations(G, high_risk_junctions, duration_hours=3.0, max_barricades=3):
    """
    Build barricade recommendations from high-risk junctions.
    """
    if not high_risk_junctions:
        return []

    barricade_roads = []
    for junction in high_risk_junctions[:max_barricades]:
        barricade_roads.append({
            "road": junction["name"],
            "reason": f"High-risk junction (score: {int(junction['risk_score'] * 100)}%)",
            "timing": f"{max(1, int(duration_hours / 2))}hr before event"
        })
    return barricade_roads


def get_diversion_plan(G, event_lat, event_lng, high_risk_junctions, num_routes=3):
    """
    Derive graph-based alternate routes by penalizing high-risk edges.
    """
    if not high_risk_junctions or G is None:
        return []

    try:
        origin = find_nearest_node(G, event_lat, event_lng)
        blocked_edges = []
        for junction in high_risk_junctions[:num_routes]:
            if all(key in junction for key in ("u", "v", "key")):
                blocked_edges.append((junction["u"], junction["v"], junction["key"]))

        if not blocked_edges:
            return []

        # Temporarily penalize weights to avoid copying the huge graph
        original_weights = {}
        for u, v, k in blocked_edges:
            if G.has_edge(u, v, key=k):
                original_weights[(u, v, k)] = G[u][v][k].get("travel_time", 1.0)
                G[u][v][k]["travel_time"] = original_weights[(u, v, k)] * 8.0
            if G.has_edge(v, u, key=k):
                original_weights[(v, u, k)] = G[v][u][k].get("travel_time", 1.0)
                G[v][u][k]["travel_time"] = original_weights[(v, u, k)] * 8.0

        diversion_plan = []
        seen_targets = set()
        for junction in high_risk_junctions:
            target = junction["v"] if junction["u"] == origin else junction["u"]
            if target == origin or target in seen_targets:
                continue
            seen_targets.add(target)

            # Compute original path
            primary_path = nx.shortest_path(G, origin, target, weight='travel_time')
            
            # Penalize
            original_weights = {}
            for u, v, k in blocked_edges:
                if G.has_edge(u, v, key=k):
                    original_weights[(u, v, k)] = G[u][v][k].get("travel_time", 1.0)
                    G[u][v][k]["travel_time"] = original_weights[(u, v, k)] * 8.0

            try:
                detour_path = nx.shortest_path(G, origin, target, weight='travel_time')
            finally:
                # Restore
                for edge, weight in original_weights.items():
                    u, v, k = edge
                    G[u][v][k]["travel_time"] = weight

            if primary_path == detour_path or len(detour_path) < 2:
                continue

            primary_names = _path_road_names(G, primary_path)
            detour_names = _path_road_names(G, detour_path)
            if not primary_names or not detour_names:
                continue

            travel_primary = _path_travel_time(G, primary_path)
            travel_detour = _path_travel_time(G, detour_path)
            added_minutes = max(1, int(round((travel_detour - travel_primary) / 60)))

            diversion_plan.append({
                "from": primary_names[0],
                "via": detour_names[1] if len(detour_names) > 1 else detour_names[0],
                "to": detour_names[-1],
                "added_time": f"+{added_minutes} min",
                "path": [
                    {"lat": float(G.nodes[n].get('y', 0)), "lng": float(G.nodes[n].get('x', 0))}
                    for n in detour_path
                ],
            })

            if len(diversion_plan) >= num_routes:
                break

        # Restore original weights
        for edge, weight in original_weights.items():
            u, v, k = edge
            G[u][v][k]["travel_time"] = weight

        return diversion_plan
    except Exception as e:
        # Attempt to restore original weights on error
        if 'original_weights' in locals():
            for edge, weight in original_weights.items():
                u, v, k = edge
                if G.has_edge(u, v, key=k):
                    G[u][v][k]["travel_time"] = weight
        print(f"Error building graph diversion plan: {e}")
        return []


def get_critical_roads(G, lat, lng, radius=1000):
    """
    Day 5: Cascading Failure Detector.
    Finds critical roads around the venue using edge betweenness centrality.
    """
    grid_key = (round(lat, 3), round(lng, 3), radius)
    if grid_key in _CRITICAL_ROADS_CACHE:
        return _CRITICAL_ROADS_CACHE[grid_key]
        
    try:
        center_node = find_nearest_node(G, lat, lng)
        # Create a small subgraph for fast computation (within ~1.5km walking distance)
        subgraph = nx.ego_graph(G, center_node, radius=radius, distance='length')
        
        # Calculate edge betweenness (approximated for speed)
        k_val = min(30, len(subgraph.nodes))
        centrality = nx.edge_betweenness_centrality(subgraph, weight='travel_time', k=k_val)
        
        # Sort edges by centrality
        sorted_edges = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        critical_paths = []
        seen_road_names = set()
        
        # Get top critical roads
        for edge_key, score in sorted_edges:
            if len(edge_key) == 3:
                u, v, k = edge_key
            else:
                u, v = edge_key
                k = 0
            
            edge_data = subgraph[u][v][k]
            road_name = get_edge_name(edge_data)
            
            # Ensure we only pick one segment per unique road name
            if road_name in seen_road_names and road_name != "Unnamed Road":
                continue
            seen_road_names.add(road_name)
            
            if 'geometry' in edge_data:
                coords = list(edge_data['geometry'].coords)
            else:
                u_data = subgraph.nodes[u]
                v_data = subgraph.nodes[v]
                coords = [(u_data['x'], u_data['y']), (v_data['x'], v_data['y'])]
            
            # Leaflet expects [lat, lng], but osmnx gives (x, y) which is (lng, lat)
            flipped_coords = [[y, x] for x, y in coords]
            
            critical_paths.append({
                "road_name": road_name,
                "coordinates": flipped_coords,
                "weight": score
            })
            if len(critical_paths) >= 5:
                break
        
        _CRITICAL_ROADS_CACHE[grid_key] = critical_paths
        return critical_paths
    except Exception as e:
        print(f"Error calculating critical roads: {e}")
        return []

def get_emergency_routes(G, lat, lng, blockade_edges=None):
    """
    Day 6: Emergency Routing.
    Finds primary routes to mock hospitals and dynamic detours that avoid specified blockade edges.
    """
    blockade_key = tuple(sorted((u, v) for u, v in blockade_edges)) if blockade_edges else None
    grid_key = (round(lat, 3), round(lng, 3), blockade_key)
    if grid_key in _EMERGENCY_ROUTES_CACHE:
        return _EMERGENCY_ROUTES_CACHE[grid_key]
        
    try:
        center_node = find_nearest_node(G, lat, lng)
        nodes = list(G.nodes())
        
        routes = []
        # Mock 2 hospitals by picking nodes from the graph if no real ones found
        random.seed(101)  # Fixed seed for consistent routes
        
        # We will dynamically penalize edges instead of copying G
        original_weights = {}
        if blockade_edges:
            for u, v in blockade_edges:
                if G.has_edge(u, v):
                    for k in G[u][v]:
                        original_weights[(u, v, k)] = G[u][v][k].get('travel_time', 1.0)
                if G.has_edge(v, u):
                    for k in G[v][u]:
                        original_weights[(v, u, k)] = G[v][u][k].get('travel_time', 1.0)

        targets = []
        try:
            import osmnx as ox
            ox.settings.timeout = 2
            # Search within 3km to prevent hanging on external Overpass API calls
            tags = {"amenity": ["hospital", "police", "fire_station"]}
            gdf = ox.features_from_point((lat, lng), tags, dist=3000)
            
            if not gdf.empty:
                for idx, row in gdf.iterrows():
                    geom = row.get("geometry")
                    if not geom: continue
                    h_lat, h_lng = (geom.y, geom.x) if geom.geom_type == 'Point' else (geom.centroid.y, geom.centroid.x)
                    name = row.get("name")
                    amenity = row.get("amenity")
                    if not isinstance(name, str) or str(name) == 'nan':
                        name = f"Local {str(amenity).title()}"
                        
                    dist_val = ((h_lat - lat)**2 + (h_lng - lng)**2)**0.5
                    targets.append((dist_val, h_lat, h_lng, name, amenity))
                
        except Exception as e:
            print(f"Failed to fetch real emergency services: {e}")

        # Sort by distance
        targets.sort(key=lambda x: x[0])

        # Filter to ensure we get a diverse set of real ones (max 2 of each type), up to 5 total
        final_targets = []
        counts = {"hospital": 0, "police": 0, "fire_station": 0}
        
        for dist, t_lat, t_lng, t_name, amenity in targets:
            if counts.get(amenity, 0) < 2:
                # Only compute nearest node for the chosen targets
                t_node = find_nearest_node(G, t_lat, t_lng)
                if t_node != center_node:
                    final_targets.append((t_node, t_name, amenity))
                    counts[amenity] = counts.get(amenity, 0) + 1
            if len(final_targets) >= 5:
                break
                
        # Fallback: if absolutely nothing is found (e.g. Overpass API timeout),
        # we still want to show something so the UI doesn't look broken.
        if not final_targets:
            # Only pick nodes that have valid lat/lng attributes
            valid_nodes = [n for n in nodes if G.nodes[n].get('y') and G.nodes[n].get('x')]
            if len(valid_nodes) >= 3:
                hospital_node = random.choice(valid_nodes)
                police_node = random.choice(valid_nodes)
                fire_node = random.choice(valid_nodes)
                final_targets = [
                    (hospital_node, "City General Hospital (Mock)", "hospital"),
                    (police_node, "Central Police Station (Mock)", "police"),
                    (fire_node, "Central Fire Station (Mock)", "fire_station")
                ]

        for target_node, target_name, amenity in final_targets:
            try:
                # Find primary shortest path
                path_nodes_primary = nx.shortest_path(G, center_node, target_node, weight='travel_time')

                # Temporarily penalize blockade edges to find a detour
                for edge, weight in original_weights.items():
                    u, v, k = edge
                    G[u][v][k]['travel_time'] = weight * 10.0

                try:
                    path_nodes_detour = nx.shortest_path(G, center_node, target_node, weight='travel_time')
                finally:
                    # Always restore weights
                    for edge, weight in original_weights.items():
                        u, v, k = edge
                        G[u][v][k]['travel_time'] = weight

                # Filter out any coordinates with NaN or zero lat/lng values
                def _sanitize(coords):
                    return [
                        c for c in coords
                        if c[0] and c[1] and not (c[0] != c[0]) and not (c[1] != c[1])
                    ]

                path_coords_primary = _sanitize([(G.nodes[n].get('y', 0), G.nodes[n].get('x', 0)) for n in path_nodes_primary])
                path_coords_detour = _sanitize([(G.nodes[n].get('y', 0), G.nodes[n].get('x', 0)) for n in path_nodes_detour])

                if len(path_coords_primary) < 2 or len(path_coords_detour) < 2:
                    continue

                # Prepend the actual pin location to ensure routes visually start from the pin
                # (nearest_nodes snaps to nearest graph node, which may be offset)
                pin_coord = [lat, lng]
                if path_coords_primary and path_coords_primary[0] != pin_coord:
                    path_coords_primary.insert(0, pin_coord)
                if path_coords_detour and path_coords_detour[0] != pin_coord:
                    path_coords_detour.insert(0, pin_coord)

                routes.append({
                    "primary_path": path_coords_primary,
                    "detour_path": path_coords_detour,
                    "name": target_name,
                    "type": "fire" if amenity == "fire_station" else amenity
                })

            except nx.NetworkXNoPath:
                continue
                
        _EMERGENCY_ROUTES_CACHE[grid_key] = routes
        return routes
    except Exception as e:
        print(f"Error calculating emergency routes: {e}")
        return []

def get_transit_infrastructure(lat: float, lng: float, radius: float = 1500) -> list[dict]:
    """
    Day 7: Multi-modal Transit Hub Finder.
    Queries OSMnx for metro stations, bus stops, and parking lots near the venue.
    Returns a list of infrastructure features with coordinates, types, and labels.
    """
    infra_points = []
    
    # 1. Try fetching real geospatial POIs using OSMnx geometries
    try:
        import osmnx as ox
        tags = {
            "railway": ["subway", "station"],
            "highway": "bus_stop",
            "amenity": "parking"
        }
        # Fetch features within venue radius
        gdf = ox.features_from_point((lat, lng), tags, dist=radius)
        if not gdf.empty:
            for idx, row in gdf.iterrows():
                # Extract point geometry
                geom = row.get("geometry")
                if not geom:
                    continue
                
                # Get centroid coordinates
                if geom.geom_type == 'Point':
                    p_lat, p_lng = geom.y, geom.x
                else:
                    centroid = geom.centroid
                    p_lat, p_lng = centroid.y, centroid.x
                
                # Determine type
                infra_type = "bus"
                label = row.get("name", "Bus Stop")
                
                if row.get("railway") in ["subway", "station"]:
                    infra_type = "metro"
                    label = row.get("name", "Metro Station")
                elif row.get("amenity") == "parking":
                    infra_type = "parking"
                    label = row.get("name", "Parking Lot")
                
                if not isinstance(label, str):
                    label = f"{infra_type.title()} Point"

                dist = ((p_lat - lat)**2 + (p_lng - lng)**2)**0.5
                infra_points.append({
                    "lat": p_lat,
                    "lng": p_lng,
                    "type": infra_type,
                    "name": label,
                    "dist": dist
                })
                
            # Sort by distance to find nearest
            infra_points.sort(key=lambda x: x["dist"])
            
            # Filter limits to prevent UI clutter
            metros = [p for p in infra_points if p["type"] == "metro"][:3]
            buses = [p for p in infra_points if p["type"] == "bus"][:3]
            parking = [p for p in infra_points if p["type"] == "parking"][:5]
            
            infra_points = metros + buses + parking
            
    except Exception as e:
        print(f"OSMnx POI lookup skipped or failed: {e}. No mock fallback generated.")

    return infra_points


def compute_junction_adjacency(G, junctions, max_dist_m=500):
    """
    Given a list of junctions (each with 'u' node ID from the osmnx graph),
    compute a boolean adjacency matrix based on real road-network
    shortest-path distance. Two junctions are neighbors if the road
    distance between them is <= max_dist_m.
    
    Returns:
        adjacency: list[list[bool]] — NxN adjacency matrix
        distances: list[list[float]] — NxN distance matrix (meters), -1 if unreachable
    """
    n = len(junctions)
    adjacency = [[False] * n for _ in range(n)]
    distances = [[-1.0] * n for _ in range(n)]
    
    # Extract source nodes for each junction
    nodes = []
    for j in junctions:
        # Use the 'u' node from the junction data if available
        node = j.get('u')
        if node is None:
            # Fallback: find nearest node from lat/lng
            lat = j.get('lat', j.get('latitude', 12.97))
            lng = j.get('lng', j.get('longitude', 77.59))
            node = find_nearest_node(G, lat, lng)
        nodes.append(node)
    
    # Compute pairwise shortest-path distances
    for i in range(n):
        for k in range(i + 1, n):
            try:
                dist = nx.shortest_path_length(G, nodes[i], nodes[k], weight='length')
                distances[i][k] = dist
                distances[k][i] = dist
                if dist <= max_dist_m:
                    adjacency[i][k] = True
                    adjacency[k][i] = True
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                # Nodes are unreachable from each other
                distances[i][k] = -1.0
                distances[k][i] = -1.0
    
    return adjacency, distances
