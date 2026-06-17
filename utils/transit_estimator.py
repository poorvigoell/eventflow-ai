def estimate_transit_diversion(venue_name: str, total_incidents: int) -> dict:
    """
    Estimates the number of commuters that can be diverted to Namma Metro.
    Based on venue proximity to metro lines.
    """
    # Partial matching for robust resolution
    v = venue_name.lower()
    if "chinnaswamy" in v:
        station_info = {"station": "Cubbon Park", "dist": 0.2, "line": "Purple"}
    elif "kanteerava" in v or "soudha" in v:
        station_info = {"station": "Vidhana Soudha", "dist": 0.5, "line": "Purple"}
    elif "freedom" in v:
        station_info = {"station": "Sir M Visvesvaraya", "dist": 0.6, "line": "Purple"}
    elif "manyata" in v:
        station_info = {"station": "Hebbal (Planned)", "dist": 3.0, "line": "Blue"}
    elif "phoenix" in v or "whitefield" in v:
        station_info = {"station": "Baiyappanahalli", "dist": 2.5, "line": "Purple"}
    elif "lalbagh" in v:
        station_info = {"station": "Lalbagh", "dist": 0.1, "line": "Green"}
    elif "iim" in v:
        station_info = {"station": "JP Nagar", "dist": 2.1, "line": "Green"}
    elif "mg road" in v:
        station_info = {"station": "MG Road", "dist": 0.0, "line": "Purple"}
    else:
        station_info = {"station": "City Railway Station", "dist": 4.0, "line": "Purple"}
    
    # If the venue is far from metro, diversion is low
    if station_info["dist"] <= 1.0:
        diversion_rate = 0.35  # 35% of affected people can take metro
    elif station_info["dist"] <= 3.0:
        diversion_rate = 0.15
    else:
        diversion_rate = 0.05

    affected_commuters = total_incidents * 150 # assumption from economic impact
    divertable_commuters = int(affected_commuters * diversion_rate)
    cars_removed = int(divertable_commuters / 1.5) # 1.5 persons per car

    freq_increase = "Normal schedule"
    if divertable_commuters > 5000:
        freq_increase = "Increase frequency to 1 train / 3 mins"
    elif divertable_commuters > 2000:
        freq_increase = "Increase frequency to 1 train / 5 mins"

    return {
        "nearest_station": station_info["station"],
        "distance_km": station_info["dist"],
        "line_color": station_info["line"],
        "divertable_commuters": divertable_commuters,
        "cars_removed_from_road": cars_removed,
        "recommended_frequency_increase": freq_increase
    }
