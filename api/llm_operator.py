import json
import httpx
import asyncio
from datetime import datetime
from groq import AsyncGroq

from api.config import GROQ_API_KEY, LLM_MODEL, LLM_ACTIVE
from models.predict import predict_event_impact
from api.traffic_api import traffic_simulator

client = AsyncGroq(api_key=GROQ_API_KEY) if LLM_ACTIVE else None

async def geocode_location(location_name: str) -> dict:
    """Geocodes a location name to its latitude and longitude in Bengaluru.
    Use this to get coordinates for a named place before calling predict_event_impact.
    
    Args:
        location_name: The name of the place, e.g. "Cubbon Park"
    """
    query = location_name
    if "bengaluru" not in query.lower() and "bangalore" not in query.lower():
        query = f"{query}, Bengaluru"

    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "EventFlowAI/1.0"}
        )
        data = resp.json()
        if data:
            return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"]),
                    "display_name": data[0]["display_name"]}
        raise ValueError(f"Could not geocode: {location_name}")

async def analyze_event(location_name: str, event_type: str, duration_hours: float = 4.0) -> dict:
    """Runs a full traffic impact prediction for an event. Returns predicted incidents, risk score, and timeline.
    Automatically geocodes the location name internally.
    
    Args:
        location_name: The name of the location, e.g. "Cubbon Park"
        event_type: The type of event (e.g. "protest", "sports", "public_event")
        duration_hours: Expected duration in hours
    """
    coords = await geocode_location(location_name)
    start_time = datetime.now().isoformat()
    
    pred = predict_event_impact(
        event_type=event_type,
        latitude=coords["lat"],
        longitude=coords["lng"],
        zone="Central",
        start_time=start_time,
        duration_hours=duration_hours
    )
    # tag the result with location name for the frontend
    pred["_locationName"] = coords["display_name"]
    pred["_duration"] = duration_hours
    pred["_eventType"] = event_type

    # Build the full response structure to match /api/predict
    from api.main import G
    from graph.simulator import get_high_risk_junctions_graph, get_critical_roads, get_emergency_routes
    from models.predict import get_tactical_recommendation, get_dispatch_recommendation, get_economic_impact, get_phase_timeline
    from utils.traffic_signals import get_signal_recommendations
    from utils.geo import haversine_distance

    if G:
        high_risk = get_high_risk_junctions_graph(G, coords["lat"], coords["lng"], pred['total_incidents'], radius=1000)
    else:
        high_risk = []
        
    pred['high_risk_junctions'] = high_risk
    
    tactical = get_tactical_recommendation(
        total_incidents=pred['total_incidents'],
        high_risk_junctions=high_risk,
        duration_hours=duration_hours,
        G=G,
        latitude=coords["lat"],
        longitude=coords["lng"]
    )
    
    dispatch = get_dispatch_recommendation(pred['total_incidents'], pred['confidence'])
    real_econ = get_economic_impact(pred['total_incidents'], duration_hours, event_type)
    econ = {
        "cost_lakhs": round(real_econ['total_cost_inr'] / 100000, 2),
        "person_hours": f"{int(real_econ['person_hours_lost']):,}",
        "affected_commuters": real_econ.get('affected_commuters', 0),
        "fuel_liters_wasted": real_econ.get('fuel_liters_wasted', 0),
        "surcharge_lakhs": round((real_econ['total_cost_inr'] / 10) / 100000, 2) if real_econ['total_cost_inr'] > 1000000 else 0.0,
        "surcharge_recommendation": real_econ['surcharge_recommendation']
    }
    
    critical_roads = get_critical_roads(G, coords["lat"], coords["lng"], radius=600) if G else []
    emergency_routes = get_emergency_routes(G, coords["lat"], coords["lng"]) if G else []
    timeline_raw = get_phase_timeline(pred['total_incidents'], start_time, duration_hours)
    
    emergency_services = []
    for er in emergency_routes:
        if len(er.get("primary_path", [])) > 0:
            target_pt = er["primary_path"][-1]
            dist = haversine_distance(coords["lat"], coords["lng"], target_pt[0], target_pt[1])
            emergency_services.append({"type": er.get("type", "hospital"), "name": er["name"], "distance_km": round(dist, 1)})
            
    emergency_services.sort(key=lambda x: x["distance_km"])
    
    signals = get_signal_recommendations(high_risk, pred['total_incidents'])
    
    result = {
        "prediction": pred,
        "tactical": tactical,
        "dispatch": dispatch,
        "economic_impact": econ,
        "critical_roads": critical_roads,
        "emergency_routes": emergency_routes,
        "emergency_services": emergency_services,
        "timeline": timeline_raw,
        "signals": signals,
        # LLM UI state bindings
        "_locationName": coords["display_name"],
        "_duration": duration_hours,
        "_eventType": event_type
    }
    
    return result

async def trigger_anomaly(junction_name: str) -> dict:
    """Injects a simulated traffic gridlock anomaly at a specific junction.
    
    Args:
        junction_name: The name of the junction (e.g., "Silk Board", "Madiwala")
    """
    anomaly = traffic_simulator.inject_anomaly(junction_name)
    return anomaly

SYSTEM_INSTRUCTION = """You are the City AI Operator for EventFlow, an advanced traffic management system for Bengaluru.
You assist city planners and traffic police by responding to natural language commands.
You have access to tools that can geocode locations, run predictive traffic simulations, and inject anomalies.
When asked to analyze or simulate an event, always call the `analyze_event` tool.
When asked to cause a traffic jam or gridlock, call `trigger_anomaly`.
Always be concise, professional, and report the findings back to the user clearly."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_event",
            "description": "Runs a full traffic impact prediction for an event. Automatically geocodes the location name internally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {"type": "string", "description": "The name of the location, e.g. 'Cubbon Park'"},
                    "event_type": {"type": "string", "description": "The type of event (e.g. 'protest', 'sports', 'public_event')"},
                    "duration_hours": {"type": "number", "description": "Expected duration in hours"}
                },
                "required": ["location_name", "event_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_anomaly",
            "description": "Injects a simulated traffic gridlock anomaly at a specific junction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "junction_name": {"type": "string", "description": "The name of the junction (e.g., 'Silk Board', 'Madiwala')"}
                },
                "required": ["junction_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": "Geocodes a location name to its latitude and longitude in Bengaluru.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {"type": "string", "description": "The name of the place, e.g. 'Cubbon Park'"}
                },
                "required": ["location_name"]
            }
        }
    }
]

async def process_chat_stream(message: str, history: list):
    """
    Generator that yields Server-Sent Events (SSE) string chunks.
    It takes a message and a history of previous messages.
    """
    if not client:
        yield f"data: {json.dumps({'error': 'LLM is not active. Please set GROQ_API_KEY in .env.'})}\n\n"
        return

    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    for msg in history:
        if msg.get("role") != "system":
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    messages.append({"role": "user", "content": message})
    
    yield f"event: thinking\ndata: {json.dumps({'text': 'Processing request...'})}\n\n"
    
    for _ in range(5):
        try:
            print(f"Calling Groq LLM API (loop {_})...")
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2
            )
            print("Groq LLM API returned.")
        except Exception as e:
            error_msg = str(e).replace('"', '\\"').replace('\n', ' ')
            print(f"LLM API Error: {error_msg}")
            yield f"event: error\ndata: {json.dumps({'text': f'API Error: {error_msg}'})}\n\n"
            break
            
        message_resp = response.choices[0].message
        
        # Groq might return None for content instead of empty string
        content = message_resp.content if message_resp.content else ""
        
        # Append assistant message
        assistant_msg = {"role": "assistant", "content": content}
        if message_resp.tool_calls:
            assistant_msg["tool_calls"] = []
            for tc in message_resp.tool_calls:
                assistant_msg["tool_calls"].append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
        messages.append(assistant_msg)
        
        if message_resp.tool_calls:
            for tool_call in message_resp.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    args = {}
                
                yield f"event: tool_call\ndata: {json.dumps({'tool': tool_name, 'args': args})}\n\n"
                
                print(f"Executing tool {tool_name}...")
                try:
                    if tool_name == "analyze_event":
                        result = await analyze_event(**args)
                    elif tool_name == "trigger_anomaly":
                        result = await trigger_anomaly(**args)
                    elif tool_name == "geocode_location":
                        result = await geocode_location(**args)
                    else:
                        result = {"error": "Unknown tool"}
                except Exception as e:
                    print(f"Tool execution error: {e}")
                    result = {"error": str(e)}
                
                print(f"Tool {tool_name} executed successfully. Yielding result...")
                yield f"event: tool_result\ndata: {json.dumps({'tool': tool_name, 'result': result})}\n\n"
                
                print(f"Appending tool result to messages...")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result)
                })
            continue
            
        else:
            text = content
            yield f"event: message\ndata: {json.dumps({'text': text})}\n\n"
            break
            
    print("Request completed.")
    yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
