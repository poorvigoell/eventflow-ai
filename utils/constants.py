# Constants for EventFlow AI

# Bengaluru Approximate Zone Bounding Boxes
# Format: { 'ZoneName': {'lat_min': float, 'lat_max': float, 'lng_min': float, 'lng_max': float} }
ZONES = {
    'North': {'lat_min': 13.0100, 'lat_max': 13.1500, 'lng_min': 77.4500, 'lng_max': 77.7000},
    'South': {'lat_min': 12.8000, 'lat_max': 12.9400, 'lng_min': 77.4500, 'lng_max': 77.7000},
    'East':  {'lat_min': 12.9400, 'lat_max': 13.0100, 'lng_min': 77.6300, 'lng_max': 77.8000},
    'West':  {'lat_min': 12.9400, 'lat_max': 13.0100, 'lng_min': 77.4000, 'lng_max': 77.5600},
    'Central': {'lat_min': 12.9400, 'lat_max': 13.0100, 'lng_min': 77.5600, 'lng_max': 77.6300}
}

# Core columns to retain from the Astram CSV
KEEP_COLUMNS = [
    'id',
    'event_type',
    'latitude',
    'longitude',
    'event_cause',
    'start_datetime',
    'end_datetime',
    'veh_type',
    'priority',
    'zone'
]

# Vehicle Size Weights (multiplier for traffic impact)
VEHICLE_WEIGHTS = {
    'two_wheeler': 1.0,
    'auto': 1.5,
    'private_car': 2.0,
    'private_bus': 4.0,
    'bmtc_bus': 5.0,
    'ksrtc_bus': 5.0,
    'lcv': 3.0,
    'heavy_vehicle': 6.0,
    'truck': 6.0,
    'tractor': 4.0,
    'unknown': 1.0
}

# Standard Color Palette for UI and Visualizations
COLOR_PALETTE = {
    'primary': '#00d2ff',
    'secondary': '#3a7bd5',
    'warning': '#ffbb00',
    'danger': '#ff4b2b',
    'success': '#00e676',
    'dark_bg': '#12141d',
    'light_bg': '#ffffff'
}
