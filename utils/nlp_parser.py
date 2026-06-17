import re
import datetime

def parse_event_text(text: str) -> dict:
    """
    Parses a natural language description of an event and extracts structured data.
    
    Example: "There is a massive political rally at Freedom Park tomorrow at 5pm for 4 hours"
    Returns:
    {
        "event_type": "protest",
        "venue_name": "Freedom Park",
        "date": "2024-03-15",
        "time": "17:00",
        "duration_hours": 4.0
    }
    """
    text_lower = text.lower()
    
    # Event Type
    event_type = "public_event"
    if any(kw in text_lower for kw in ["rally", "protest", "strike"]):
        event_type = "protest"
    elif any(kw in text_lower for kw in ["construction", "roadwork", "digging"]):
        event_type = "construction"
    elif any(kw in text_lower for kw in ["vip", "minister", "convoy"]):
        event_type = "vip_movement"
    elif any(kw in text_lower for kw in ["sports", "cricket", "match", "marathon"]):
        event_type = "sports"
    elif any(kw in text_lower for kw in ["religious", "festival", "procession"]):
        event_type = "religious"

    # Venue Name
    # Improved venue matching
    venue_map = {
        "chinnaswamy": "M Chinnaswamy Stadium",
        "kanteerava": "Kanteerava Stadium",
        "freedom": "Freedom Park",
        "manyata": "Manyata Tech Park",
        "phoenix": "Phoenix Marketcity Mall",
        "lalbagh": "Lalbagh Botanical Garden",
        "iim": "IIM Bangalore"
    }
    
    venue_name = "M Chinnaswamy Stadium" # default
    for kw, proper_name in venue_map.items():
        if kw in text_lower:
            venue_name = proper_name
            break

    # Duration
    duration_hours = 3.0
    duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hr|h)', text_lower)
    if duration_match:
        duration_hours = float(duration_match.group(1))

    # Time
    time_str = "18:00"
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        time_str = f"{hour:02d}:{minute:02d}"

    # Date
    today = datetime.date.today()
    date_str = today.strftime("%Y-%m-%d")
    if "tomorrow" in text_lower:
        date_str = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    return {
        "event_type": event_type,
        "venue_name": venue_name,
        "date": date_str,
        "time": time_str,
        "duration_hours": duration_hours
    }
