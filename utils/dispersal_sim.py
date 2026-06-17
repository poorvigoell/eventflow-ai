import math
import random

def simulate_dispersal(
    lat: float, lng: float,
    crowd_size: int = 30000,
    num_exits: int = 4,
    duration_minutes: int = 60,
    step_minutes: int = 5
) -> list[dict]:
    """
    Simple radial diffusion model:
    - Place crowd_size people at venue center
    - Define num_exits as evenly-spaced radial directions
    - Each timestep: people flow outward along exit directions
    - Density decays exponentially with distance and time
    - Gaussian spread perpendicular to exit direction
    """
    if crowd_size <= 0:
        return [{"time_min": 0, "points": [], "remaining_pct": 0.0}]

    random.seed(42)
    snapshots = []
    exit_angles = [2 * math.pi * i / num_exits for i in range(num_exits)]
    
    DEG_PER_KM_LAT = 1 / 111.0
    DEG_PER_KM_LNG = 1 / (111.0 * math.cos(math.radians(lat)))

    for t in range(0, duration_minutes + 1, step_minutes):
        decay = math.exp(-t / 25.0)
        remaining_pct = round(max(0, decay * 100), 1)
        
        points = []
        people_per_exit = crowd_size / num_exits
        
        for angle in exit_angles:
            max_dist_km = min(3.0, (t / 12.0) * 1.0)
            
            for d in [x * 0.1 for x in range(1, int(max_dist_km * 10) + 1)]:
                p_lat = lat + d * math.cos(angle) * DEG_PER_KM_LAT
                p_lng = lng + d * math.sin(angle) * DEG_PER_KM_LNG
                
                density = (people_per_exit / max(1, crowd_size)) * math.exp(-d / 0.8) * decay
                density = max(0, round(density, 4))
                
                if density > 0.001:
                    points.append({"lat": round(p_lat, 6), "lng": round(p_lng, 6), "density": density})
                    
                    spread = 0.1 * d
                    for offset in [-spread, spread]:
                        s_lat = p_lat + offset * math.sin(angle) * DEG_PER_KM_LAT
                        s_lng = p_lng - offset * math.cos(angle) * DEG_PER_KM_LNG
                        s_density = density * 0.4
                        if s_density > 0.001:
                            points.append({"lat": round(s_lat, 6), "lng": round(s_lng, 6), "density": round(s_density, 4)})
        
        snapshots.append({
            "time_min": t,
            "points": points,
            "remaining_pct": remaining_pct
        })

    return snapshots
