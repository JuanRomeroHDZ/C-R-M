import json
import logging
import re
import urllib.parse
from typing import Dict, Any, Optional
import httpx
from src.geo.bounds import MACRO_ZONES
from src.queue.redis_queue import queue_manager

logger = logging.getLogger("crm.geo.geocoder")

GEOCODE_CACHE_TTL_SECONDS = 30 * 86400  # 30 days cache
USER_AGENT = "CRM-Local-Prospeccion-Tijuana/7.0 (contact@crm.local)"


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


async def geocode_location(query: str) -> Optional[Dict[str, Any]]:
    if not query or not query.strip():
        query = "Tijuana, Baja California"

    norm_query = query.strip()
    cache_key = f"crm:geocode:{_slugify(norm_query)}"

    # 1. Check Redis Cache
    try:
        r = await queue_manager.get_client()
        cached = await r.get(cache_key)
        if cached:
            logger.info(f"Geocoding cache hit for '{norm_query}'")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis cache check failed: {e}")

    # 2. Check Static Macro Zones fallback if it matches
    zone_slug = _slugify(norm_query)
    if zone_slug in MACRO_ZONES:
        min_lat, min_lon, max_lat, max_lon = MACRO_ZONES[zone_slug]
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0
        result = {
            "query": norm_query,
            "display_name": f"{norm_query.title()}, Tijuana, Baja California, Mexico",
            "center": {"lat": center_lat, "lon": center_lon},
            "bbox": {
                "min_lat": min_lat,
                "min_lon": min_lon,
                "max_lat": max_lat,
                "max_lon": max_lon
            },
            "bounds": [min_lat, min_lon, max_lat, max_lon],
            "source": "preset_macro_zone"
        }
        return result

    # 3. Query OpenStreetMap Nominatim API
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": norm_query,
        "format": "jsonv2",
        "polygon_geojson": 1,
        "limit": 1,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    item = data[0]
                    bbox = item.get("boundingbox", [])
                    if len(bbox) == 4:
                        min_lat = float(bbox[0])
                        max_lat = float(bbox[1])
                        min_lon = float(bbox[2])
                        max_lon = float(bbox[3])
                        center_lat = float(item.get("lat", (min_lat + max_lat) / 2))
                        center_lon = float(item.get("lon", (min_lon + max_lon) / 2))

                        result = {
                            "query": norm_query,
                            "display_name": item.get("display_name", norm_query),
                            "center": {"lat": center_lat, "lon": center_lon},
                            "bbox": {
                                "min_lat": min_lat,
                                "min_lon": min_lon,
                                "max_lat": max_lat,
                                "max_lon": max_lon
                            },
                            "bounds": [min_lat, min_lon, max_lat, max_lon],
                            "geojson": item.get("geojson"),
                            "source": "nominatim_live"
                        }

                        # Save to Redis with 30 days TTL
                        try:
                            r = await queue_manager.get_client()
                            await r.setex(cache_key, GEOCODE_CACHE_TTL_SECONDS, json.dumps(result))
                        except Exception as cache_err:
                            logger.warning(f"Failed to cache geocode result: {cache_err}")

                        return result
    except Exception as exc:
        logger.error(f"Nominatim geocoding error for '{norm_query}': {exc}")

    # 4. Fallback to Tijuana default if nothing found
    default_bounds = MACRO_ZONES["tijuana-full"]
    return {
        "query": norm_query,
        "display_name": f"{norm_query} (Fallback Tijuana)",
        "center": {"lat": 32.5149, "lon": -117.0382},
        "bbox": {
            "min_lat": default_bounds[0],
            "min_lon": default_bounds[1],
            "max_lat": default_bounds[2],
            "max_lon": default_bounds[3]
        },
        "bounds": list(default_bounds),
        "source": "fallback"
    }
