import os
import osmnx as ox
import networkx as nx

def download_and_cache_graph(place_name="Bengaluru, Karnataka, India", filename="bengaluru_network.graphml", boundary_filename="bengaluru_boundary.geojson"):
    """
    Downloads the drivable road network for the specified place, filters to major roads,
    and caches it locally as a GraphML file. Also caches the city boundary.
    """
    filepath = os.path.join(os.path.dirname(__file__), filename)
    boundary_path = os.path.join(os.path.dirname(__file__), boundary_filename)
    
    # 1. Download and save the city boundary
    print(f"Downloading boundary for {place_name}...")
    try:
        gdf = ox.geocode_to_gdf(place_name)
        gdf.to_file(boundary_path, driver="GeoJSON")
        print(f"Saved boundary to {boundary_path}")
    except Exception as e:
        print(f"Error downloading boundary: {e}")

    # 2. Download and save the road network
    if os.path.exists(filepath):
        print(f"Graph already exists at {filepath}. Skipping download.")
        return ox.load_graphml(filepath)
    
    print(f"Downloading road network for {place_name}...")
    # Filter to only keep major roads to drastically reduce graph size and memory footprint
    custom_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
    
    # Retrieve the network graph
    G = ox.graph_from_place(place_name, network_type='drive', custom_filter=custom_filter)
    
    # Add travel times assuming default speeds if not present
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    print(f"Saving graph to {filepath}...")
    ox.save_graphml(G, filepath)
    print("Done!")
    return G

if __name__ == "__main__":
    download_and_cache_graph()
