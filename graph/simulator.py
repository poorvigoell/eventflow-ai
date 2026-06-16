import networkx as nx
import random
import osmnx as ox

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
