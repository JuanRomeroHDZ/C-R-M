from typing import Dict, Tuple

# Bounding Box Coordinates: (min_lat, min_lon, max_lat, max_lon)
MACRO_ZONES: Dict[str, Tuple[float, float, float, float]] = {
    "zona-rio": (32.5150, -117.0300, 32.5380, -117.0050),
    "centro": (32.5250, -117.0480, 32.5450, -117.0300),
    "otay": (32.5200, -116.9950, 32.5520, -116.9300),
    "la-mesa": (32.4850, -116.9900, 32.5150, -116.9450),
    "playas": (32.5000, -117.1300, 32.5350, -117.0950),
    "chapultepec-hipodromo": (32.5000, -117.0250, 32.5200, -116.9950),
    "el-florido": (32.4400, -116.8900, 32.4800, -116.8200),
    "insurgentes": (32.4800, -116.9400, 32.5100, -116.8900),
    "santa-fe": (32.4200, -117.0600, 32.4600, -117.0000),
    "tijuana-full": (32.4000, -117.1350, 32.5550, -116.8200),
}


def get_zone_bounds(zone_name: str) -> Tuple[float, float, float, float]:
    zone_key = zone_name.lower().strip()
    if zone_key in MACRO_ZONES:
        return MACRO_ZONES[zone_key]
    return MACRO_ZONES["zona-rio"]
