"""
economic_scorer.py
Computes a Crowd Economic Score for an event based on:
  - Event type (vip_movement → premium; protest → mass)
  - Venue (UB City area → premium; Lalbagh → middle/mass)
  - Crowd size proxy (total_incidents)

Returns:
  {
    "score":          float 0.0–1.0   (0 = pure lower-income, 1 = pure premium),
    "segment":        "Premium" | "Middle" | "Mass",
    "rich_pct":       int   # % likely high-income attendees
    "middle_pct":     int
    "lower_pct":      int
    "transport_split": {
        "metro_pct":  int,
        "cab_pct":    int,
        "bus_pct":    int,
        "walk_pct":   int,
    },
    "primary_mode":  str   # dominant expected mode
  }
"""

# ─── Event-type base scores (0–1, higher = wealthier audience) ───────────────
_EVENT_BASE = {
    "vip_movement":  1.0,
    "sports":        0.55,   # Cricket has broad cross-section
    "public_event":  0.50,
    "construction":  0.35,
    "tree_fall":     0.30,
    "religious":     0.25,
    "protest":       0.15,
}

# ─── Venue modifier (additive to base, clamped 0–1) ─────────────────────────
_VENUE_MOD = {
    # Premium / Central luxury zones
    "phoenix":       +0.20,
    "manyata":       +0.15,
    "iim":           +0.10,
    "chinnaswamy":    0.00,
    "kanteerava":    -0.05,
    "freedom":       -0.10,
    "lalbagh":       -0.15,
}

# ─── Transport mix lookup table (by segment) ─────────────────────────────────
# Values must sum to 100
_TRANSPORT_MIX = {
    "Premium": {"metro_pct": 10, "cab_pct": 65, "bus_pct":  5, "walk_pct": 20},
    "Middle":  {"metro_pct": 45, "cab_pct": 25, "bus_pct": 20, "walk_pct": 10},
    "Mass":    {"metro_pct": 20, "cab_pct":  5, "bus_pct": 55, "walk_pct": 20},
}

_DEMOG_MIX = {
    # segment → (rich_pct, middle_pct, lower_pct)
    "Premium": (65, 30,  5),
    "Middle":  (20, 60, 20),
    "Mass":    ( 5, 25, 70),
}


def get_economic_score(
    event_type: str,
    venue_name: str,
    total_incidents: int = 0,
) -> dict:
    """
    Compute economic crowd profile for an event.

    Parameters
    ----------
    event_type     : Internal key, e.g. "sports", "vip_movement", "protest"
    venue_name     : Display name, e.g. "M Chinnaswamy Stadium (Central)"
    total_incidents: Predicted incident count (used to scale crowd size proxy)

    Returns
    -------
    dict with score, segment, demographic split, transport split, primary_mode
    """
    base = _EVENT_BASE.get(event_type, 0.40)

    # Venue modifier — partial-match on lowercased venue name
    mod = 0.0
    vn = venue_name.lower()
    for key, delta in _VENUE_MOD.items():
        if key in vn:
            mod = delta
            break

    # Crowd density modifier: very large events (incidents > 400) trend toward mass
    if total_incidents > 400:
        mod -= 0.10
    elif total_incidents < 100:
        mod += 0.05

    score = max(0.0, min(1.0, base + mod))

    # Classify into segment
    if score >= 0.65:
        segment = "Premium"
    elif score >= 0.35:
        segment = "Middle"
    else:
        segment = "Mass"

    rich_pct, middle_pct, lower_pct = _DEMOG_MIX[segment]
    transport = _TRANSPORT_MIX[segment]

    # Determine primary mode
    primary_mode = max(transport, key=transport.get)
    primary_label = {
        "metro_pct": "🚇 Metro",
        "cab_pct":   "🚕 Cab / Auto",
        "bus_pct":   "🚌 BMTC Bus",
        "walk_pct":  "🚶 Walking",
    }[primary_mode]

    return {
        "score":          round(score, 3),
        "segment":        segment,
        "rich_pct":       rich_pct,
        "middle_pct":     middle_pct,
        "lower_pct":      lower_pct,
        "transport_split": transport,
        "primary_mode":   primary_label,
    }
