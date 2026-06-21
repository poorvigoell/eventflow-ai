import random
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class TrafficProvider(ABC):
    """
    Abstract interface for traffic data. 
    Allows hot-swapping between simulated anomalies and a real commercial API later.
    """
    @abstractmethod
    def get_live_traffic(self, junction_name: str) -> Dict[str, Any]:
        pass

class RealTrafficAPI(TrafficProvider):
    """
    Stub for a future real API integration (e.g., TomTom, Google Maps, HERE).
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_live_traffic(self, junction_name: str) -> Dict[str, Any]:
        # TODO: Implement actual HTTP call to traffic provider
        # Example: 
        # response = requests.get(f"https://api.tomtom.com/traffic/services/...&key={self.api_key}")
        # return response.json()
        pass

class SimulatedTrafficAPI(TrafficProvider):
    """
    Simulates traffic data matching the format of a commercial API.
    Can artificially inject anomalies (gridlock) into specific junctions.
    """
    def __init__(self):
        self.active_anomalies = {}  # junction_name -> anomaly details
        self.anomaly_id_counter = 1
        
    def inject_anomaly(self, junction_name: str, is_accident: bool = None, is_emergency_stuck: bool = None, is_real: bool = False, source_id: str = None) -> Dict[str, Any]:
        """Manually trigger a severe traffic jam at a specific location."""
        # Simulated API values for a severe jam
        free_flow_time = random.randint(45, 90) # seconds
        jam_factor = round(random.uniform(8.5, 10.0), 1) # 0 to 10 scale
        current_speed = random.randint(2, 8) # km/h
        
        # calculate severe delay
        current_travel_time = int(free_flow_time * (1 + jam_factor))
        
        # Calculate Severity Factors
        emergency_stuck = is_emergency_stuck if is_emergency_stuck is not None else random.random() < 0.25
        accident = is_accident if is_accident is not None else random.random() < 0.35
        
        # Score calculation (Max 100)
        # Jam factor: up to 40 points
        score_jam = (jam_factor / 10.0) * 40
        # Emergency: 30 points
        score_emg = 30 if emergency_stuck else 0
        # Accident: 30 points
        score_acc = 30 if accident else 0
        
        severity_score = int(score_jam + score_emg + score_acc)
        
        if severity_score > 85:
            severity_level = "CRITICAL"
        elif severity_score > 65:
            severity_level = "HIGH"
        else:
            severity_level = "MODERATE"
        
        anomaly = {
            "id": source_id if source_id else f"ANO-{self.anomaly_id_counter}",
            "junction": junction_name,
            "is_real": is_real,
            "source_id": source_id,
            "jam_factor": jam_factor,
            "current_speed_kmh": current_speed,
            "free_flow_travel_time_sec": free_flow_time,
            "current_travel_time_sec": current_travel_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "emergency_vehicle_stuck": emergency_stuck,
            "accident_reported": accident,
            "severity_score": severity_score,
            "severity_level": severity_level,
            "status": "active"
        }
        self.active_anomalies[anomaly["id"]] = anomaly
        self.anomaly_id_counter += 1
        return anomaly
        
    def clear_anomaly(self, anomaly_id: str):
        """Clear an active anomaly"""
        if anomaly_id in self.active_anomalies:
            self.active_anomalies[anomaly_id]["status"] = "resolved"
            self.active_anomalies[anomaly_id]["resolved_at"] = datetime.datetime.now().isoformat()
            
    def get_live_traffic(self, junction_name: str) -> Dict[str, Any]:
        """Returns either the active anomaly or default free-flow traffic."""
        # Find if this junction has an active anomaly
        active = [v for v in self.active_anomalies.values() if v["junction"] == junction_name and v["status"] == "active"]
        if active:
            return active[0]
            
        # Default free-flow traffic
        free_flow_time = random.randint(45, 90)
        return {
            "junction": junction_name,
            "jam_factor": round(random.uniform(0.0, 2.0), 1),
            "current_speed_kmh": random.randint(35, 55),
            "free_flow_travel_time_sec": free_flow_time,
            "current_travel_time_sec": int(free_flow_time * random.uniform(1.0, 1.2)),
            "timestamp": datetime.datetime.now().isoformat()
        }

# Global singleton instance for the simulator
traffic_simulator = SimulatedTrafficAPI()
