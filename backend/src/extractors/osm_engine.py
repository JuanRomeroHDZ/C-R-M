import asyncio
import logging
from typing import List, Dict, Any, Tuple, Optional
import httpx
from src.config import settings

logger = logging.getLogger("crm.extractors.osm")

OVERPASS_MIRRORS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter"
]


class OSMExtractor:
    def __init__(self):
        self.mirrors = OVERPASS_MIRRORS
        self.current_mirror_idx = 0
        self.user_agent = f"{settings.SCRAPER_USER_AGENT} (CRM-Local-OSM-Engine/1.0)"

    def get_current_mirror(self) -> str:
        return self.mirrors[self.current_mirror_idx % len(self.mirrors)]

    def rotate_mirror(self):
        self.current_mirror_idx = (self.current_mirror_idx + 1) % len(self.mirrors)
        logger.info(f"Rotated Overpass mirror to: {self.get_current_mirror()}")

    def build_query(
        self,
        osm_tags: List[Tuple[str, str]],
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        search_term: Optional[str] = None,
        timeout_seconds: int = 25
    ) -> str:
        bbox_str = f"{min_lat:.5f},{min_lon:.5f},{max_lat:.5f},{max_lon:.5f}"
        statements = []
        for k, v in osm_tags:
            statements.append(f'  node["{k}"="{v}"]({bbox_str});')
            statements.append(f'  way["{k}"="{v}"]({bbox_str});')
            statements.append(f'  relation["{k}"="{v}"]({bbox_str});')

        if search_term and search_term.strip():
            clean_term = search_term.strip().replace('"', '')
            statements.append(f'  node["name"~"{clean_term}",i]({bbox_str});')
            statements.append(f'  way["name"~"{clean_term}",i]({bbox_str});')
            statements.append(f'  relation["name"~"{clean_term}",i]({bbox_str});')

        if not statements:
            statements.append(f'  node["amenity"]({bbox_str});')
            statements.append(f'  node["shop"]({bbox_str});')
            statements.append(f'  node["office"]({bbox_str});')

        query_body = "\n".join(statements)
        query = f"""[out:json][timeout:{timeout_seconds}];
(
{query_body}
);
out center tags;"""
        return query

    async def fetch_elements(
        self,
        query: str,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        backoff = 2.0
        last_error = None

        for attempt in range(max_retries):
            mirror_url = self.get_current_mirror()
            try:
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        mirror_url,
                        data={"data": query},
                        headers=headers
                    )

                if response.status_code == 200:
                    data = response.json()
                    elements = data.get("elements", [])
                    logger.info(f"Overpass fetched {len(elements)} elements from {mirror_url}")
                    return elements
                elif response.status_code in (429, 504, 502, 503):
                    logger.warning(
                        f"Mirror {mirror_url} returned HTTP {response.status_code}. "
                        f"Backoff {backoff}s and rotating..."
                    )
                    self.rotate_mirror()
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                else:
                    logger.warning(f"Mirror {mirror_url} unexpected status {response.status_code}")
                    self.rotate_mirror()
            except Exception as exc:
                last_error = exc
                logger.warning(f"Error connecting to {mirror_url}: {type(exc).__name__} {str(exc)}")
                self.rotate_mirror()
                await asyncio.sleep(backoff)
                backoff *= 2.0

        if last_error:
            logger.error(f"Failed to fetch from Overpass after {max_retries} retries: {last_error}")
        return []

    def parse_element(self, element: Dict[str, Any], category_slug: str, target_city: Optional[str] = None) -> Dict[str, Any]:
        tags = element.get("tags", {})
        el_type = element.get("type", "node")
        el_id = element.get("id")
        external_id = f"osm:{el_type}:{el_id}"

        name = tags.get("name") or tags.get("brand") or tags.get("operator") or "Negocio Local Sin Nombre"

        # Coordinates
        lat = None
        lon = None
        if el_type == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        elif "center" in element:
            lat = element["center"].get("lat")
            lon = element["center"].get("lon")

        # Contact info
        phone = tags.get("phone") or tags.get("contact:phone") or tags.get("telephone")
        website = tags.get("website") or tags.get("contact:website") or tags.get("url")

        # Address
        street = tags.get("addr:street")
        house_num = tags.get("addr:housenumber")
        suburb = tags.get("addr:suburb") or tags.get("addr:neighbourhood")
        postcode = tags.get("addr:postcode")
        city = tags.get("addr:city") or target_city or "Tijuana"

        address_parts = [p for p in [street, house_num, suburb, postcode, city] if p]
        address_raw = ", ".join(address_parts) if address_parts else None

        # Social links & extra tags
        social_links = {}
        for k in ("contact:facebook", "contact:instagram", "contact:linkedin", "facebook", "instagram"):
            if k in tags:
                social_links[k] = tags[k]

        return {
            "external_source": "osm",
            "external_id": external_id,
            "name": name.strip(),
            "category_slug": category_slug,
            "primary_category": tags.get("amenity") or tags.get("healthcare") or tags.get("office") or category_slug,
            "subcategories": [v for k, v in tags.items() if k in ("healthcare:speciality", "office", "craft", "shop")],
            "phone_raw": phone.strip() if phone else None,
            "phone_normalized": None,
            "website": website.strip() if website else None,
            "address_raw": address_raw,
            "street": street,
            "house_number": house_num,
            "suburb": suburb,
            "postal_code": postcode,
            "city": city,
            "state": tags.get("addr:state") or "Baja California",
            "country": "Mexico",
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lon) if lon is not None else None,
            "rating": None,
            "review_count": 0,
            "opening_hours_raw": tags.get("opening_hours"),
            "is_claimed": None,
            "lifecycle_stage": "EXTRACTED",
            "extra_metadata": {
                "osm_tags": tags,
                "social_links": social_links,
                "osm_type": el_type,
                "osm_id": el_id
            }
        }

    async def extract_cell(
        self,
        osm_tags: List[Tuple[str, str]],
        category_slug: str,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        search_term: Optional[str] = None,
        target_city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = self.build_query(
            osm_tags,
            min_lat,
            min_lon,
            max_lat,
            max_lon,
            search_term=search_term
        )
        raw_elements = await self.fetch_elements(query)

        parsed_leads = []
        for el in raw_elements:
            parsed = self.parse_element(el, category_slug, target_city=target_city)
            # Require at least name
            if parsed["name"] and parsed["name"] != "Negocio Local Sin Nombre":
                parsed_leads.append(parsed)

        return parsed_leads

        return parsed_leads
