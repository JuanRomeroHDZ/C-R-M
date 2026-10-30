import math
from typing import List, Dict, Any


def km_to_lat_degrees(km: float) -> float:
    return km / 111.0


def km_to_lon_degrees(km: float, lat: float) -> float:
    rad = math.radians(lat)
    cos_lat = math.cos(rad)
    if cos_lat <= 0.0001:
        cos_lat = 0.0001
    return km / (111.0 * cos_lat)


def generate_initial_grid(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    cell_size_km: float = 1.0
) -> List[Dict[str, Any]]:
    avg_lat = (min_lat + max_lat) / 2.0
    lat_step = km_to_lat_degrees(cell_size_km)
    lon_step = km_to_lon_degrees(cell_size_km, avg_lat)

    cells = []
    row = 0
    current_lat = min_lat
    while current_lat < max_lat:
        next_lat = min(current_lat + lat_step, max_lat)
        col = 0
        current_lon = min_lon
        while current_lon < max_lon:
            next_lon = min(current_lon + lon_step, max_lon)
            cell_code = f"cell_r{row}_c{col}_d0"
            cells.append({
                "cell_code": cell_code,
                "depth": 0,
                "min_lat": current_lat,
                "min_lon": current_lon,
                "max_lat": next_lat,
                "max_lon": next_lon
            })
            current_lon = next_lon
            col += 1
        current_lat = next_lat
        row += 1

    return cells


def split_cell(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    parent_code: str,
    parent_depth: int
) -> List[Dict[str, Any]]:
    mid_lat = (min_lat + max_lat) / 2.0
    mid_lon = (min_lon + max_lon) / 2.0
    depth = parent_depth + 1

    sub_quadrants = [
        ("NW", mid_lat, min_lon, max_lat, mid_lon),
        ("NE", mid_lat, mid_lon, max_lat, max_lon),
        ("SW", min_lat, min_lon, mid_lat, mid_lon),
        ("SE", min_lat, mid_lon, mid_lat, max_lon),
    ]

    result = []
    for suffix, s_min_lat, s_min_lon, s_max_lat, s_max_lon in sub_quadrants:
        cell_code = f"{parent_code}_{suffix}_d{depth}"
        result.append({
            "cell_code": cell_code,
            "depth": depth,
            "min_lat": s_min_lat,
            "min_lon": s_min_lon,
            "max_lat": s_max_lat,
            "max_lon": s_max_lon
        })

    return result
