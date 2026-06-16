import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def is_within_bbox(lat, lng, bbox):
    """
    Helper function to check if coordinates are within a bounding box.
    bbox format: {'lat_min': float, 'lat_max': float, 'lng_min': float, 'lng_max': float}
    """
    if bbox['lat_min'] <= lat <= bbox['lat_max'] and bbox['lng_min'] <= lng <= bbox['lng_max']:
        return True
    return False
