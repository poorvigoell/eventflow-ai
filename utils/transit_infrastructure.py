"""
transit_infrastructure.py
Static dataset of Bengaluru transit POIs (metro stations, BMTC bus stops, parking lots).
Provides a helper to fetch nearby POIs for any lat/lng within the city.
"""

import math

# ---------------------------------------------------------------------------
# Static POI dataset — organised by area cluster
# Each entry: { name, lat, lng, type }   type ∈ {"metro", "bus", "parking"}
# ---------------------------------------------------------------------------

_ALL_POIS = [
    # ── Purple Line metro stations ──────────────────────────────────────────
    {"name": "Baiyappanahalli Metro",       "lat": 12.9987, "lng": 77.6693, "type": "metro", "line": "Purple"},
    {"name": "Swami Vivekananda Road Metro","lat": 12.9950, "lng": 77.6580, "type": "metro", "line": "Purple"},
    {"name": "Indiranagar Metro",           "lat": 12.9784, "lng": 77.6408, "type": "metro", "line": "Purple"},
    {"name": "Halasuru Metro",              "lat": 12.9800, "lng": 77.6218, "type": "metro", "line": "Purple"},
    {"name": "Trinity Metro",               "lat": 12.9722, "lng": 77.6080, "type": "metro", "line": "Purple"},
    {"name": "MG Road Metro",               "lat": 12.9756, "lng": 77.6084, "type": "metro", "line": "Purple"},
    {"name": "Cubbon Park Metro",           "lat": 12.9788, "lng": 77.5940, "type": "metro", "line": "Purple"},
    {"name": "Vidhana Soudha Metro",        "lat": 12.9794, "lng": 77.5850, "type": "metro", "line": "Purple"},
    {"name": "Sir M Visvesvaraya Metro",    "lat": 12.9770, "lng": 77.5730, "type": "metro", "line": "Purple"},
    {"name": "City Railway Station Metro",  "lat": 12.9773, "lng": 77.5698, "type": "metro", "line": "Purple"},
    {"name": "Magadi Road Metro",           "lat": 12.9747, "lng": 77.5580, "type": "metro", "line": "Purple"},
    {"name": "Mysore Road Metro",           "lat": 12.9628, "lng": 77.5310, "type": "metro", "line": "Purple"},
    # ── Green Line metro stations ────────────────────────────────────────────
    {"name": "Nagasandra Metro",            "lat": 13.0523, "lng": 77.5131, "type": "metro", "line": "Green"},
    {"name": "Dasarahalli Metro",           "lat": 13.0392, "lng": 77.5249, "type": "metro", "line": "Green"},
    {"name": "Jalahalli Metro",             "lat": 13.0310, "lng": 77.5358, "type": "metro", "line": "Green"},
    {"name": "Peenya Industry Metro",       "lat": 13.0234, "lng": 77.5431, "type": "metro", "line": "Green"},
    {"name": "Peenya Metro",                "lat": 13.0194, "lng": 77.5483, "type": "metro", "line": "Green"},
    {"name": "Goraguntepalya Metro",        "lat": 13.0127, "lng": 77.5557, "type": "metro", "line": "Green"},
    {"name": "Yeshwanthpur Metro",          "lat": 13.0251, "lng": 77.5544, "type": "metro", "line": "Green"},
    {"name": "Sandal Soap Factory Metro",   "lat": 13.0022, "lng": 77.5666, "type": "metro", "line": "Green"},
    {"name": "Mahalakshmi Metro",           "lat": 12.9940, "lng": 77.5680, "type": "metro", "line": "Green"},
    {"name": "Rajajinagar Metro",           "lat": 12.9891, "lng": 77.5655, "type": "metro", "line": "Green"},
    {"name": "Kuvempu Road Metro",          "lat": 12.9837, "lng": 77.5661, "type": "metro", "line": "Green"},
    {"name": "Srirampura Metro",            "lat": 12.9800, "lng": 77.5660, "type": "metro", "line": "Green"},
    {"name": "Mantri Square Sampige Road",  "lat": 12.9861, "lng": 77.5740, "type": "metro", "line": "Green"},
    {"name": "Majestic (Nadaprabhu)",       "lat": 12.9767, "lng": 77.5713, "type": "metro", "line": "Green"},
    {"name": "Chickpete Metro",             "lat": 12.9697, "lng": 77.5757, "type": "metro", "line": "Green"},
    {"name": "Krishna Rajendra Market",     "lat": 12.9624, "lng": 77.5762, "type": "metro", "line": "Green"},
    {"name": "National College Metro",      "lat": 12.9557, "lng": 77.5759, "type": "metro", "line": "Green"},
    {"name": "Lalbagh Metro",               "lat": 12.9507, "lng": 77.5844, "type": "metro", "line": "Green"},
    {"name": "South End Circle Metro",      "lat": 12.9462, "lng": 77.5918, "type": "metro", "line": "Green"},
    {"name": "Jayanagar Metro",             "lat": 12.9393, "lng": 77.5934, "type": "metro", "line": "Green"},
    {"name": "Rashtreeya Vidyalaya Road",   "lat": 12.9262, "lng": 77.5968, "type": "metro", "line": "Green"},
    {"name": "JP Nagar Metro",              "lat": 12.9100, "lng": 77.5918, "type": "metro", "line": "Green"},
    {"name": "Yelachenahalli Metro",        "lat": 12.8987, "lng": 77.5972, "type": "metro", "line": "Green"},

    # ── BMTC Bus Stops (representative major stops) ──────────────────────────
    {"name": "Majestic Bus Terminal",       "lat": 12.9767, "lng": 77.5700, "type": "bus"},
    {"name": "Shivajinagar Bus Stand",      "lat": 12.9860, "lng": 77.6012, "type": "bus"},
    {"name": "Kempegowda Bus Stand",        "lat": 12.9767, "lng": 77.5700, "type": "bus"},
    {"name": "KR Market Bus Stop",          "lat": 12.9624, "lng": 77.5762, "type": "bus"},
    {"name": "Domlur Bus Stop",             "lat": 12.9600, "lng": 77.6400, "type": "bus"},
    {"name": "Silk Board Junction Stop",    "lat": 12.9170, "lng": 77.6228, "type": "bus"},
    {"name": "Koramangala Bus Stop",        "lat": 12.9352, "lng": 77.6245, "type": "bus"},
    {"name": "Hebbal Bus Stop",             "lat": 13.0450, "lng": 77.5980, "type": "bus"},
    {"name": "Yeshwanthpur Bus Depot",      "lat": 13.0251, "lng": 77.5505, "type": "bus"},
    {"name": "Jayanagar Bus Stop",          "lat": 12.9250, "lng": 77.5930, "type": "bus"},
    {"name": "Indiranagar 100ft Road Stop", "lat": 12.9784, "lng": 77.6408, "type": "bus"},
    {"name": "Banashankari Bus Stop",       "lat": 12.9250, "lng": 77.5480, "type": "bus"},
    {"name": "Whitefield Bus Depot",        "lat": 12.9600, "lng": 77.7500, "type": "bus"},
    {"name": "Electronic City Bus Stop",    "lat": 12.8550, "lng": 77.6640, "type": "bus"},
    {"name": "Manyata Tech Bus Stop",       "lat": 13.0450, "lng": 77.6200, "type": "bus"},

    # ── Parking Lots ─────────────────────────────────────────────────────────
    {"name": "Kanteerava Stadium Parking",  "lat": 12.9694, "lng": 77.5900, "type": "parking"},
    {"name": "MG Road Multi-Level Parking", "lat": 12.9756, "lng": 77.6100, "type": "parking"},
    {"name": "Garuda Mall Parking",         "lat": 12.9740, "lng": 77.6096, "type": "parking"},
    {"name": "UB City Parking",             "lat": 12.9718, "lng": 77.5985, "type": "parking"},
    {"name": "Phoenix Mall Parking",        "lat": 12.9958, "lng": 77.6963, "type": "parking"},
    {"name": "Orion Mall Parking",          "lat": 13.0120, "lng": 77.5560, "type": "parking"},
    {"name": "Brigade Metropolis Parking",  "lat": 12.9795, "lng": 77.7129, "type": "parking"},
    {"name": "Indiranagar CMH Road Parking","lat": 12.9762, "lng": 77.6413, "type": "parking"},
    {"name": "Lalbagh Gate Parking",        "lat": 12.9507, "lng": 77.5820, "type": "parking"},
    {"name": "Manyata Parking Complex",     "lat": 13.0455, "lng": 77.6220, "type": "parking"},
    {"name": "Silk Board Fly-over Parking", "lat": 12.9170, "lng": 77.6200, "type": "parking"},
    {"name": "Freedom Park Parking",        "lat": 12.9782, "lng": 77.5800, "type": "parking"},
]

# ── Metro line corridor polylines ────────────────────────────────────────────
# Used to weight the heatmap darker along active metro corridors.
# Format: list of (lat, lng) tuples representing the line centre
METRO_CORRIDORS = {
    "Purple": [
        (12.9987, 77.6693), (12.9950, 77.6580), (12.9784, 77.6408),
        (12.9800, 77.6218), (12.9722, 77.6080), (12.9756, 77.6084),
        (12.9788, 77.5940), (12.9794, 77.5850), (12.9770, 77.5730),
        (12.9773, 77.5698), (12.9747, 77.5580), (12.9628, 77.5310),
    ],
    "Green": [
        (13.0523, 77.5131), (13.0392, 77.5249), (13.0234, 77.5431),
        (13.0251, 77.5544), (13.0022, 77.5666), (12.9940, 77.5680),
        (12.9891, 77.5655), (12.9861, 77.5740), (12.9767, 77.5713),
        (12.9697, 77.5757), (12.9557, 77.5759), (12.9507, 77.5844),
        (12.9462, 77.5918), (12.9393, 77.5934), (12.9262, 77.5968),
        (12.9100, 77.5918), (12.8987, 77.5972),
    ],
    "Yellow": [
        (12.9262, 77.5968), (12.9180, 77.5980), (12.9100, 77.6040),
        (12.9030, 77.6180), (12.8950, 77.6290), (12.8870, 77.6410),
        (12.8760, 77.6530), (12.8640, 77.6620), (12.8550, 77.6640),
        (12.8360, 77.6710), (12.8100, 77.6850)
    ],
    "Pink": [
        (12.8930, 77.5980), (12.9050, 77.6000), (12.9150, 77.6020),
        (12.9250, 77.6050), (12.9370, 77.6100), (12.9490, 77.6150),
        (12.9600, 77.6190), (12.9720, 77.6150), (12.9840, 77.6100),
        (12.9950, 77.6050), (13.0070, 77.6000), (13.0200, 77.5950),
        (13.0300, 77.5920), (13.0450, 77.5980)
    ]
}


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in kilometres between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_transit_pois(lat: float, lng: float, radius_km: float = 2.5) -> list[dict]:
    """
    Return all transit POIs within `radius_km` kilometres of (lat, lng).
    Each item: { name, lat, lng, type, line? }
    """
    nearby = []
    for poi in _ALL_POIS:
        dist = _haversine_km(lat, lng, poi["lat"], poi["lng"])
        if dist <= radius_km:
            nearby.append({**poi, "dist_km": round(dist, 2)})
    return sorted(nearby, key=lambda p: p["dist_km"])


def get_metro_corridor_points(lat: float, lng: float, radius_km: float = 3.0) -> list[dict]:
    """
    Return corridor waypoints from any metro line that passes within radius_km
    of the given location.  Used to inject extra heatmap weight along metro routes.
    Each item: { lat, lng, line }
    """
    results = []
    for line, waypoints in METRO_CORRIDORS.items():
        for (wlat, wlng) in waypoints:
            if _haversine_km(lat, lng, wlat, wlng) <= radius_km:
                results.append({"lat": wlat, "lng": wlng, "line": line})
    return results

def get_metro_corridors_lines() -> list[dict]:
    """
    Return all metro corridors formatted as Polylines for the frontend map.
    Each item: { name, color, coordinates: [[lat, lng], ...] }
    """
    results = []
    colors = {"Purple": "#800080", "Green": "#008000", "Yellow": "#FFD700", "Pink": "#FF69B4"}
    for line, waypoints in METRO_CORRIDORS.items():
        results.append({
            "name": f"{line} Line",
            "color": colors.get(line, "#00d2ff"),
            "coordinates": [[lat, lng] for lat, lng in waypoints]
        })
    return results
