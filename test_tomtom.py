import asyncio
import sys
sys.path.append('.')
from api.tomtom_client import get_incidents_in_bbox

async def test():
    print("Fetching incidents from TomTom API...")
    data = await get_incidents_in_bbox(12.8, 77.4, 13.1, 77.8)
    incidents = data.get('incidents', [])
    print(f'Total incidents found: {len(incidents)}')
    
    max_delay = 0
    worst = None
    for inc in incidents:
        delay = inc.get('properties', {}).get('delay') or 0
        if delay > max_delay:
            max_delay = delay
            worst = inc
            
    print(f'Max delay found: {max_delay} seconds')
    if worst:
        props = worst['properties']
        print(f'Worst Incident ID: {props.get("id")}')
        print(f'From: {props.get("from")} to {props.get("to")}')
        print(f'Delay: {max_delay}s')
        if max_delay > 180:
            print("=> Alert would be triggered successfully!")
        else:
            print("=> Max delay is under 3 minutes, no alert triggered (this is correct behavior).")

if __name__ == '__main__':
    asyncio.run(test())
