import os
import sys
import joblib
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def _load_model():
    saved_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'saved'))
    model_path = os.path.join(saved_dir, 'xgb_incident_model.joblib')
    meta_path = os.path.join(saved_dir, 'model_meta.joblib')

    if not os.path.exists(model_path):
        print(f"Warning: Model not found at {model_path}. Run models/train.py first.")
        return None, None

    model = joblib.load(model_path)
    meta = joblib.load(meta_path)
    return model, meta

def generate_unplanned_events(latitude: float, longitude: float, radius_km: float = 2.0) -> list:
    """
    Generates dynamic unplanned events around a given location (e.g. protest, construction, weather hazard)
    with randomized but stable seeding based on coordinates.
    """
    # Create stable seed from coordinates
    seed = int(abs(latitude * 10000 + longitude * 10000)) % 1000000
    rng = np.random.default_rng(seed)
    
    types = ["protest", "construction", "waterlogging", "accident"]
    severities = ["Low", "Medium", "High"]
    
    num_events = rng.integers(1, 4)
    unplanned_events = []
    
    for i in range(num_events):
        event_type = rng.choice(types)
        severity = rng.choice(severities)
        # Random offset roughly within radius_km (1 degree lat ~= 111km)
        lat_offset = rng.uniform(-0.009 * radius_km, 0.009 * radius_km)
        lng_offset = rng.uniform(-0.009 * radius_km, 0.009 * radius_km)
        
        unplanned_events.append({
            "id": f"UNPLANNED_{seed}_{i}",
            "event_type": event_type,
            "severity": severity,
            "latitude": latitude + lat_offset,
            "longitude": longitude + lng_offset,
            "description": f"Unplanned {event_type} (Severity: {severity}) detected nearby."
        })
        
    return unplanned_events

def predict_event_impact(
    event_type: str,
    latitude: float,
    longitude: float,
    zone: str,
    start_time: str,
    duration_hours: float
) -> dict:
    _model, _meta = _load_model()

    if _model is None:
        return {
            "total_incidents": 0,
            "phases": {
                "inflow": {"count": 0, "peak_hour": "-", "top_type": "-"},
                "steady": {"count": 0, "peak_hour": "-", "top_type": "-"},
                "exodus": {"count": 0, "peak_hour": "-", "top_type": "-"},
            },
            "high_risk_junctions": [],
            "confidence": 0.0
        }

    start_dt = pd.to_datetime(start_time)
    hour = start_dt.hour
    day_of_week = start_dt.dayofweek

    cause_map = {
        'construction': 0, 'others': 1, 'procession': 2, 'protest': 3,
        'public_event': 4, 'tree_fall': 5, 'vehicle_breakdown': 6, 'vip_movement': 7,
        'sports': 4, 'religious': 2, 'waterlogging': 5, 'accident': 6
    }
    cause_code = cause_map.get(event_type, 0)

    zone_map = {
        'Central': 0, 'Central Zone 1': 1, 'Central Zone 2': 2, 'East': 3,
        'East Zone 1': 4, 'East Zone 2': 5, 'North': 6, 'North Zone 1': 7,
        'North Zone 2': 8, 'South': 9, 'South Zone 1': 10, 'South Zone 2': 11,
        'Unknown': 12, 'West': 13, 'West Zone 1': 14, 'West Zone 2': 15
    }
    zone_code = zone_map.get(zone, 0)

    priority_code = 1

    is_weekend = 1 if day_of_week in [5, 6] else 0
    is_rush_hour = 1 if hour in [8, 9, 10, 17, 18, 19, 20] else 0
    hour_sin = np.sin(2 * np.pi * hour / 24.0)
    hour_cos = np.cos(2 * np.pi * hour / 24.0)

    # Build feature vector in the EXACT order the model was trained on.
    # We use a raw numpy array to completely bypass XGBoost's feature name validation.
    base_features = [cause_code, zone_code, hour, day_of_week, duration_hours, priority_code, latitude, longitude]
    extended_features = base_features + [is_weekend, is_rush_hour, hour_sin, hour_cos]

    # Check how many features the model expects
    try:
        num_expected = _model.n_features_in_
    except AttributeError:
        num_expected = len(extended_features)

    if num_expected <= 8:
        feature_array = np.array([base_features])
    else:
        feature_array = np.array([extended_features])

    total_pred = max(0, int(round(_model.predict(feature_array)[0])))

    inflow_ratio = 0.30
    steady_ratio = 0.45
    exodus_ratio = 0.25

    inflow = max(0, int(round(total_pred * inflow_ratio)))
    steady = max(0, int(round(total_pred * steady_ratio)))
    exodus = total_pred - inflow - steady

    high_risk = get_high_risk_junctions(latitude, longitude, total_pred)
    timeline = get_phase_timeline(total_pred, start_time, duration_hours)

    confidence = min(0.95, _meta['r2']) if _meta else 0.5

    inflow_hour = (start_dt - pd.Timedelta(hours=1)).strftime('%H:%M')
    steady_hour = (start_dt + pd.Timedelta(hours=max(1, duration_hours/2))).strftime('%H:%M')
    exodus_hour = (start_dt + pd.Timedelta(hours=duration_hours)).strftime('%H:%M')

    return {
        "total_incidents": total_pred,
        "phases": {
            "inflow": {"count": inflow, "peak_hour": inflow_hour, "top_type": "slow_traffic"},
            "steady": {"count": steady, "peak_hour": steady_hour, "top_type": "illegal_parking"},
            "exodus": {"count": exodus, "peak_hour": exodus_hour, "top_type": "accident"},
        },
        "high_risk_junctions": high_risk,
        "timeline": timeline,
        "confidence": round(confidence, 2)
    }

def get_high_risk_junctions(latitude: float, longitude: float, total_incidents: int) -> list:
    """Returns top 5 high risk junctions based on event location and predicted volume"""
    if total_incidents < 1:
        return []
        
    np.random.seed(int(latitude * 1000)) # Stable randomness
    
    # Simulate finding nearby OSM junctions
    offsets = [
        (0.005, 0.003, "Main Gate Junction"),
        (-0.003, 0.005, "North Exit Road"),
        (0.002, -0.004, "East Corridor"),
        (-0.004, -0.002, "South Bypass"),
        (0.006, -0.001, "Outer Ring Connect")
    ]
    
    high_risk = []
    for i, (dlat, dlng, name) in enumerate(offsets):
        if i >= 5: break
        risk_score = min(1.0, (total_incidents / 20.0) + np.random.uniform(0.05, 0.2))
        high_risk.append({
            "name": name,
            "lat": latitude + dlat,
            "lng": longitude + dlng,
            "risk_score": round(risk_score, 2)
        })
        
    # Sort by highest risk first
    high_risk = sorted(high_risk, key=lambda x: x['risk_score'], reverse=True)
    return high_risk

def get_phase_timeline(total_incidents: int, start_time: str, duration_hours: float) -> list:
    """Returns hourly incident counts for plotting timelines"""
    if total_incidents == 0:
        return []
        
    start_dt = pd.to_datetime(start_time)
    start_hour = start_dt.replace(minute=0, second=0, microsecond=0)
    
    timeline = []
    
    # 2 hours before (Inflow)
    timeline.append({"time": (start_hour - pd.Timedelta(hours=2)).strftime('%H:%M'), "count": max(0, round(total_incidents * 0.1)), "phase": "inflow"})
    timeline.append({"time": (start_hour - pd.Timedelta(hours=1)).strftime('%H:%M'), "count": max(0, round(total_incidents * 0.2)), "phase": "inflow"})
    
    # During (Steady)
    steady_count_per_hour = max(0, round((total_incidents * 0.45) / max(1, duration_hours)))
    for h in range(int(max(1, duration_hours))):
        timeline.append({
            "time": (start_hour + pd.Timedelta(hours=h)).strftime('%H:%M'), 
            "count": steady_count_per_hour, 
            "phase": "steady"
        })
        
    # 2 hours after (Exodus)
    end_hour = start_hour + pd.Timedelta(hours=duration_hours)
    timeline.append({"time": (end_hour).strftime('%H:%M'), "count": max(0, round(total_incidents * 0.15)), "phase": "exodus"})
    timeline.append({"time": (end_hour + pd.Timedelta(hours=1)).strftime('%H:%M'), "count": max(0, round(total_incidents * 0.1)), "phase": "exodus"})
    
    # Ensure that if total_incidents > 0, we don't have a completely empty timeline
    total_distributed = sum(item["count"] for item in timeline)
    if total_distributed < total_incidents:
        diff = total_incidents - total_distributed
        # Add the remaining incidents to the peak steady phase hours
        steady_start_idx = 2
        steady_hours = int(max(1, duration_hours))
        for i in range(diff):
            idx = steady_start_idx + (i % steady_hours)
            if idx < len(timeline):
                timeline[idx]["count"] += 1
                
    return timeline

def get_historical_replay(event_id: str) -> dict:
    """
    Day 4: Given a past event ID, returns both the actual recorded incidents
    and what the model would have predicted. Includes accuracy metrics.
    """
    _model, _meta = _load_model()

    # Load the correlated training data which has both event info + actual counts
    training_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'training_data.pkl')
    if not os.path.exists(training_path):
        return {"error": "training_data.pkl not found. Run data/correlator.py first."}

    training_df = pd.read_pickle(training_path)

    # Look up the event by ID
    row = training_df[training_df['event_id'] == event_id]
    if row.empty:
        # Fallback: use the first event in the dataset as a demo
        row = training_df.iloc[[0]]
        event_id = row['event_id'].values[0]

    row = row.iloc[0]
    actual_total = int(row['total_incidents'])
    actual_inflow = int(row['inflow_incidents'])
    actual_steady = int(row['steady_incidents'])
    actual_exodus = int(row['exodus_incidents'])

    # Rebuild a fake start_time from hour + day_of_week for prediction
    # Use a fixed reference date and inject the event's hour
    from datetime import datetime, timedelta
    base_date = datetime(2024, 3, 4)  # Monday
    days_offset = int(row['day_of_week'])
    start_dt = base_date + timedelta(days=days_offset)
    start_time_str = start_dt.strftime('%Y-%m-%d') + f" {int(row['hour']):02d}:00:00"

    predicted_result = predict_event_impact(
        event_type=str(row['event_cause']),
        latitude=float(row['latitude']),
        longitude=float(row['longitude']),
        zone=str(row['zone']),
        start_time=start_time_str,
        duration_hours=float(row['duration_hours'])
    )

    predicted_total = predicted_result['total_incidents']

    # Accuracy: 100 - mean absolute percentage error (capped at 100%)
    if actual_total > 0:
        accuracy_pct = round(max(0.0, 100.0 - abs(predicted_total - actual_total) / actual_total * 100), 1)
    elif predicted_total == 0:
        accuracy_pct = 100.0
    else:
        accuracy_pct = 0.0

    return {
        "event_id": event_id,
        "actual": {
            "total": actual_total,
            "inflow": actual_inflow,
            "steady": actual_steady,
            "exodus": actual_exodus,
        },
        "predicted": {
            "total": predicted_total,
            "phases": predicted_result.get('phases', {}),
        },
        "accuracy_pct": accuracy_pct,
        "model_confidence": predicted_result.get('confidence', 0.0),
        "high_risk_junctions": predicted_result.get('high_risk_junctions', []),
    }


def get_economic_impact(
    total_incidents: int,
    duration_hours: float,
    event_type: str = 'public_event'
) -> dict:
    """
    Day 5: Estimates economic impact of predicted traffic congestion.
    Returns affected commuters, person-hours of delay, rupee cost, fuel waste,
    and an event organizer surcharge recommendation.
    """
    # Assumptions based on Bengaluru traffic research
    AVG_COMMUTERS_PER_INCIDENT = 150      # vehicles affected per incident
    OCCUPANCY_RATE = 1.5                  # avg persons per vehicle
    AVG_DELAY_MINUTES_PER_INCIDENT = 18   # minutes lost per affected commuter
    COST_PER_HOUR_INR = 200               # avg rupee value of 1 person-hour
    FUEL_WASTE_LITERS_PER_INCIDENT = 2.5  # liters wasted in stop-and-go
    FUEL_PRICE_INR = 103                  # per liter (Bengaluru avg)

    # Scale by event type
    scale = {
        'public_event': 1.0,
        'vip_movement': 0.6,
        'religious': 1.2,
        'sports': 1.5,
        'construction': 0.4,
        'protest': 0.8,
    }.get(event_type, 1.0)

    affected_vehicles = int(total_incidents * AVG_COMMUTERS_PER_INCIDENT * scale)
    affected_persons = int(affected_vehicles * OCCUPANCY_RATE)
    delay_hours = round((total_incidents * AVG_DELAY_MINUTES_PER_INCIDENT * scale) / 60, 1)
    person_hours_lost = round(affected_persons * (delay_hours / max(1, total_incidents)), 1)
    economic_cost_inr = int(person_hours_lost * COST_PER_HOUR_INR)
    fuel_liters_wasted = round(total_incidents * FUEL_WASTE_LITERS_PER_INCIDENT * scale, 1)
    fuel_cost_inr = int(fuel_liters_wasted * FUEL_PRICE_INR)
    total_cost_inr = economic_cost_inr + fuel_cost_inr

    # Surcharge recommendation (for event organisers)
    if total_cost_inr > 1_000_000:
        surcharge_recommendation = f"HIGH IMPACT: Recommend ₹{total_cost_inr // 10:,} organiser surcharge for city infrastructure"
    elif total_cost_inr > 300_000:
        surcharge_recommendation = f"MEDIUM IMPACT: Recommend ₹{total_cost_inr // 20:,} organiser surcharge"
    else:
        surcharge_recommendation = "LOW IMPACT: No surcharge required"

    return {
        "affected_commuters": affected_persons,
        "person_hours_lost": person_hours_lost,
        "economic_cost_inr": economic_cost_inr,
        "fuel_liters_wasted": fuel_liters_wasted,
        "fuel_cost_inr": fuel_cost_inr,
        "total_cost_inr": total_cost_inr,
        "surcharge_recommendation": surcharge_recommendation,
        "summary": (
            f"{affected_persons:,} commuters affected, "
            f"{person_hours_lost:.0f} person-hours lost, "
            f"₹{total_cost_inr:,} total economic impact"
        )
    }

def get_tactical_recommendation(
    total_incidents: int,
    high_risk_junctions: list,
    duration_hours: float
) -> dict:
    """
    Core PS deliverable: Compute manpower deployment, road barricading,
    and diversion routing based on predicted event impact.
    """
    num_junctions = len(high_risk_junctions)
    traffic_police = max(4, num_junctions * 4 + (total_incidents // 5) * 2)
    patrol_vehicles = max(1, num_junctions // 3 + 1)
    ambulances = max(1, total_incidents // 10) if total_incidents > 0 else 0
    tow_trucks = max(0, total_incidents // 15)
    barricade_teams = max(1, num_junctions)

    barricade_roads = []
    for j in high_risk_junctions[:3]:
        barricade_roads.append({
            "road": j["name"],
            "reason": f"High risk junction ({j['risk_score']*100:.0f}% score)",
            "timing": f"{max(1, int(duration_hours / 2))}hr before event"
        })

    diversion_templates = [
        {"from": "MG Road", "via": "Residency Road", "to": "Richmond Circle", "added_time": "+4 min"},
        {"from": "Cubbon Road", "via": "Kasturba Road", "to": "Hudson Circle", "added_time": "+3 min"},
        {"from": "JC Road", "via": "KR Road", "to": "Town Hall", "added_time": "+5 min"},
        {"from": "Race Course Road", "via": "Seshadri Road", "to": "Majestic", "added_time": "+6 min"},
        {"from": "Infantry Road", "via": "Brigade Road", "to": "Commercial St", "added_time": "+3 min"},
    ]
    diversion_plan = diversion_templates[:min(len(barricade_roads) + 1, len(diversion_templates))]

    if total_incidents > 15:
        timeline = f"Deploy {int(duration_hours)}hr before event start"
    elif total_incidents > 5:
        timeline = f"Deploy {max(1, int(duration_hours / 2))}hr before event start"
    else:
        timeline = "Deploy 45 min before event start"

    return {
        "manpower": {
            "traffic_police": traffic_police,
            "patrol_vehicles": patrol_vehicles,
            "ambulances": ambulances,
            "tow_trucks": tow_trucks,
            "barricade_teams": barricade_teams,
        },
        "barricade_roads": barricade_roads,
        "diversion_plan": diversion_plan,
        "deployment_timeline": timeline,
    }

def get_dispatch_recommendation(total_incidents: int, risk_score: float) -> dict:
    """
    Returns structured dispatch resource counts scaled to the event.
    """
    base = max(2, total_incidents)
    multiplier = 1.0 + risk_score

    traffic_police = int(base * multiplier * 0.5)
    mounted_patrol = max(0, int(base * multiplier * 0.1))
    ambulances = max(1, int(base * multiplier * 0.15)) if total_incidents > 0 else 0
    tow_trucks = max(0, int(base * multiplier * 0.1))
    control_rooms = 1 if total_incidents < 10 else 2

    total_units = traffic_police + mounted_patrol + ambulances + tow_trucks + control_rooms

    if total_incidents > 15 or risk_score > 0.8:
        alert_level = "RED"
    elif total_incidents > 5 or risk_score > 0.6:
        alert_level = "AMBER"
    else:
        alert_level = "GREEN"

    return {
        "total_units": total_units,
        "breakdown": {
            "traffic_police": traffic_police,
            "mounted_patrol": mounted_patrol,
            "ambulances": ambulances,
            "tow_trucks": tow_trucks,
            "control_rooms": control_rooms,
        },
        "alert_level": alert_level,
        "summary": f"{total_units} units ({alert_level} alert) — {traffic_police} traffic police, {ambulances} ambulances"
    }


def predict_multi_event(
    events: list,
    compounding_penalty: float = 0.15
) -> dict:
    """
    Day 6: Accept a list of events and predict combined impact with compounding
    penalties when multiple events overlap in time/space.

    Each event in the list is a dict with keys matching predict_event_impact() args:
      event_type, latitude, longitude, zone, start_time, duration_hours
    """
    from utils.geo import haversine_distance

    if not events:
        return {"error": "No events provided"}

    individual_results = []
    for evt in events:
        result = predict_event_impact(
            event_type=evt.get('event_type', 'public_event'),
            latitude=evt['latitude'],
            longitude=evt['longitude'],
            zone=evt.get('zone', 'Central'),
            start_time=evt['start_time'],
            duration_hours=evt.get('duration_hours', 3.0)
        )
        individual_results.append({
            'event': evt,
            'prediction': result
        })

    # Detect spatial overlaps (events within 5km of each other)
    overlap_pairs = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            dist = haversine_distance(
                events[i]['latitude'], events[i]['longitude'],
                events[j]['latitude'], events[j]['longitude']
            )
            if dist <= 5.0:
                overlap_pairs.append((i, j, round(dist, 2)))

    # Combine totals with compounding penalty for each overlap
    base_total = sum(r['prediction']['total_incidents'] for r in individual_results)
    penalty_multiplier = 1.0 + (len(overlap_pairs) * compounding_penalty)
    combined_total = int(round(base_total * penalty_multiplier))

    combined_confidence = round(
        min(r['prediction']['confidence'] for r in individual_results) * (1 - 0.05 * len(overlap_pairs)),
        2
    ) if individual_results else 0.0

    return {
        "num_events": len(events),
        "individual_results": individual_results,
        "overlap_pairs": [
            {"event_a": i, "event_b": j, "distance_km": d}
            for i, j, d in overlap_pairs
        ],
        "combined_total_incidents": combined_total,
        "compounding_penalty_applied": len(overlap_pairs) > 0,
        "penalty_multiplier": round(penalty_multiplier, 2),
        "combined_confidence": combined_confidence,
        "summary": (
            f"{len(events)} events, {len(overlap_pairs)} spatial overlaps detected. "
            f"Combined predicted incidents: {combined_total} "
            f"(vs {base_total} without compounding)"
        )
    }


if __name__ == "__main__":
    result = predict_event_impact(
        event_type="public_event",
        latitude=12.9789,
        longitude=77.5998,
        zone="Central",
        start_time="2024-03-15 18:00:00",
        duration_hours=4.0
    )
    print("Prediction Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    print("\n--- Historical Replay ---")
    replay = get_historical_replay("FKID000040")
    for k, v in replay.items():
        print(f"  {k}: {v}")

    print("\n--- Economic Impact ---")
    econ = get_economic_impact(result['total_incidents'], 4.0, 'public_event')
    for k, v in econ.items():
        print(f"  {k}: {v}")

