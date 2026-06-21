import os
import httpx
from cachetools import TTLCache
from .config import TOMTOM_API_KEY, TOMTOM_BASE_URL, TOMTOM_ACTIVE

API_KEY = TOMTOM_API_KEY
BASE = TOMTOM_BASE_URL

# Simple TTL caches to limit calls and keep within free tier
_flow_cache = TTLCache(maxsize=500, ttl=180)   # 3 minutes
_inc_cache = TTLCache(maxsize=200, ttl=300)    # 5 minutes


async def _fetch(path, params=None):
    if not TOMTOM_ACTIVE:
        return None
    params = dict(params or {}, key=API_KEY)
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()


async def get_flow_by_point(lat: float, lng: float):
    # Normalize coordinates for caching and repeat lookups on the same road segment.
    lat = round(lat, 6)
    lng = round(lng, 6)
    cache_key = (lat, lng)
    if cache_key in _flow_cache:
        return _flow_cache[cache_key]
    # TomTom Flow Segment example endpoint (public docs specify exact path/version)
    path = '/traffic/services/4/flowSegmentData/absolute/22/json'
    data = await _fetch(path, {'point': f'{lat},{lng}'})
    _flow_cache[cache_key] = data
    return data


async def get_incidents_in_bbox(min_lat: float, min_lng: float, max_lat: float, max_lng: float):
    cache_key = (round(min_lat, 6), round(min_lng, 6), round(max_lat, 6), round(max_lng, 6))
    if cache_key in _inc_cache:
        return _inc_cache[cache_key]
    # TomTom incidents endpoint (adjust path/params to match current API)
    path = '/traffic/services/5/incidentDetails'
    bbox = f"{min_lng},{min_lat},{max_lng},{max_lat}"
    params = {
        'bbox': bbox,
        'fields': '{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,events{description,code},delay,from,to}}}',
        'language': 'en-GB'
    }
    data = await _fetch(path, params)
    _inc_cache[cache_key] = data
    return data
