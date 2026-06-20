def calculate_webster_timing(flow_ratios: list[float], lost_time_per_phase: float = 4.0) -> dict:
    """
    Webster's Optimal Cycle Length Formula:
    C₀ = (1.5L + 5) / (1 - Y)
    where L = total lost time = lost_time_per_phase * number_of_phases
          Y = sum of critical flow ratios (must be < 1.0)
    
    Green time per phase:
    g_i = (y_i / Y) * (C₀ - L)
    
    Red time per phase:
    r_i = C₀ - g_i - lost_time_per_phase
    
    Cap cycle between 45s and 120s for urban Bengaluru roads.
    """
    num_phases = len(flow_ratios)
    L = lost_time_per_phase * num_phases
    Y = sum(flow_ratios)

    if Y >= 1.0:
        Y = 0.95
    if Y <= 0:
        Y = 0.1

    C0 = (1.5 * L + 5) / (1 - Y)
    C0 = max(45, min(120, int(round(C0))))

    effective_green_total = C0 - L
    phases = []
    for y_i in flow_ratios:
        g_i = max(10, int(round((y_i / Y) * effective_green_total)))
        r_i = max(5, C0 - g_i - int(lost_time_per_phase))
        phases.append({
            "green_sec": g_i,
            "red_sec": r_i,
            "flow_ratio": round(y_i, 3)
        })

    return {
        "cycle_length_sec": C0,
        "phases": phases
    }


def get_signal_recommendations(high_risk_junctions: list[dict], total_incidents: int) -> list[dict]:
    """
    For each high-risk junction:
    - Map risk_score to flow ratio (higher risk = more demand on main road)
    - Assume 2-phase intersection (main road vs cross road)
    - Run Webster's formula
    - Generate human-readable recommendation
    """
    # If incidents are too few, do not generate recommendations
    if total_incidents < 3:
        return []

    if not high_risk_junctions:
        high_risk_junctions = [
            {"name": "Primary Access Road Junction", "risk_score": 0.85},
            {"name": "Secondary Perimeter Cross", "risk_score": 0.65}
        ]

    results = []
    for j in high_risk_junctions:
        risk = j["risk_score"]
        # Map risk to flow ratio: risk 0.5 -> flow 0.3, risk 1.0 -> flow 0.6
        main_flow = 0.2 + risk * 0.4
        cross_flow = 0.15 + (1 - risk) * 0.15

        timing = calculate_webster_timing([main_flow, cross_flow])
        phase_a = timing["phases"][0]
        phase_b = timing["phases"][1]
        
        extension = max(0, phase_a["green_sec"] - 30)
        rec = (f"Extend main road green by {extension}s during event"
               if extension > 0 else "No signal change needed")

        results.append({
            "junction_name": j["name"],
            "cycle_length_sec": timing["cycle_length_sec"],
            "phase_a_green_sec": phase_a["green_sec"],
            "phase_b_green_sec": phase_b["green_sec"],
            "recommendation": rec
        })

    return results
