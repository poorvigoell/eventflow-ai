import os
import osmnx as ox
import networkx as nx

def download_and_cache_graph(lat=12.9788, lng=77.5996, dist=5000, filename="bengaluru_network.graphml"):
    """
    Downloads the drivable road network within a specified radius of a coordinate
    and caches it locally as a GraphML file.
    Default coordinate is M Chinnaswamy Stadium.
    """
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        print(f"Graph already exists at {filepath}. Skipping download.")
        return ox.load_graphml(filepath)
    
    print(f"Downloading road network within {dist}m of ({lat}, {lng})...")
    # Retrieve the network graph
    G = ox.graph_from_point((lat, lng), dist=dist, network_type='drive')
    
    # Add travel times assuming default speeds if not present
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    print(f"Saving graph to {filepath}...")
    ox.save_graphml(G, filepath)
    print("Done!")
    return G

if __name__ == "__main__":
    download_and_cache_graph()
