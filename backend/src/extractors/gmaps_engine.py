import asyncio
import logging
import random
import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from src.config import settings

logger = logging.getLogger("crm.extractors.gmaps")

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
]

VIEWPORTS = [
    {"width": 1280, "height": 800},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864}
]

BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
BLOCKED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".mp4", ".gif"]
BLOCKED_DOMAINS = ["google-analytics.com", "googletagmanager.com", "doubleclick.net", "facebook.net"]


class CircuitBreakerTriggered(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class GoogleMapsExtractor:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None

    async def _init_browser(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser or not self.browser.is_connected():
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def _get_random_jitter(self, base_low: float = 0.8, base_high: float = 2.2) -> float:
        # Non-uniform log-normal distribution for human-like pauses
        return random.uniform(base_low, base_high) + (random.random() * 0.5)

    async def _setup_page(self) -> Tuple[BrowserContext, Page]:
        await self._init_browser()
        ua = random.choice(USER_AGENTS)
        vp = random.choice(VIEWPORTS)

        context = await self.browser.new_context(
            user_agent=ua,
            viewport=vp,
            locale="es-MX",
            timezone_id="America/Tijuana",
            extra_http_headers={
                "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"
            }
        )
        page = await context.new_page()

        # Intercept and block heavy media & trackers
        async def route_interceptor(route):
            req = route.request
            url = req.url.lower()

            if req.resource_type in BLOCKED_RESOURCE_TYPES:
                await route.abort()
                return

            if any(ext in url for ext in BLOCKED_EXTENSIONS):
                await route.abort()
                return

            if any(domain in url for domain in BLOCKED_DOMAINS):
                await route.abort()
                return

            await route.continue_()

        await page.route("**/*", route_interceptor)
        return context, page

    async def _check_circuit_breaker(self, page: Page):
        title = await page.title()
        content = await page.content()

        if "recaptcha" in content.lower() or "unusual traffic" in content.lower():
            logger.error("Circuit breaker triggered: Captcha or unusual traffic challenge detected.")
            raise CircuitBreakerTriggered("Captcha detected on Google Maps page")

        if "sorry" in title.lower() and "google" in title.lower():
            logger.error("Circuit breaker triggered: Google rate limit block detected.")
            raise CircuitBreakerTriggered("Rate limit block detected on Google Maps")

    def _clean_website_url(self, raw_url: Optional[str]) -> Optional[str]:
        if not raw_url:
            return None
        if "google.com/url?" in raw_url:
            parsed = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if "q" in qs and qs["q"]:
                return qs["q"][0]
        return raw_url

    def _extract_coords_from_url(self, url: str) -> Tuple[Optional[float], Optional[float]]:
        match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None

    def _extract_cid_from_url(self, url: str) -> Optional[str]:
        match = re.search(r"0x[0-9a-fA-F]+:(0x[0-9a-fA-F]+)", url)
        if match:
            return match.group(1)
        match_hex = re.search(r"!1s(0x[0-9a-fA-F]+:[0-9a-zA-Z_]+)", url)
        if match_hex:
            return match_hex.group(1)
        return None

    async def search_cell(
        self,
        keyword: str,
        category_slug: str,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        max_results: int = 15,
        location_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0
        full_query = f"{keyword} en {location_name}" if location_name else keyword
        search_query = urllib.parse.quote(full_query)
        url = f"https://www.google.com/maps/search/{search_query}/@{center_lat:.6f},{center_lon:.6f},15z?hl=es"

        logger.info(f"Google Maps scrape query '{full_query}' at ({center_lat:.4f}, {center_lon:.4f})")
        context, page = await self._setup_page()

        leads = []
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._check_circuit_breaker(page)

            # Wait for feed or no-results
            await asyncio.sleep(self._get_random_jitter(2.0, 3.5))
            await self._check_circuit_breaker(page)

            feed_locator = page.locator("div[role='feed']")
            if await feed_locator.count() == 0:
                logger.info("No result feed found on this coordinate.")
                return []

            # Smooth scrolling over feed
            feed = feed_locator.first
            scroll_attempts = 0
            max_scrolls = 4
            while scroll_attempts < max_scrolls:
                await feed.evaluate("node => node.scrollTop = node.scrollHeight")
                await asyncio.sleep(self._get_random_jitter(1.0, 2.0))
                scroll_attempts += 1

            # Select individual business link anchors
            items = await page.locator("div[role='feed'] > div > div > a").all()
            logger.info(f"Detected {len(items)} items in Google Maps feed.")

            limit = min(len(items), max_results)
            for idx in range(limit):
                try:
                    item_anchor = items[idx]
                    label = await item_anchor.get_attribute("aria-label")
                    href = await item_anchor.get_attribute("href") or ""

                    if not label or not href:
                        continue

                    # Click to load card details
                    await item_anchor.click()
                    await asyncio.sleep(self._get_random_jitter(1.5, 2.5))
                    await self._check_circuit_breaker(page)

                    detail_url = page.url
                    lat, lon = self._extract_coords_from_url(detail_url)
                    if lat is None:
                        lat, lon = center_lat, center_lon

                    cid = self._extract_cid_from_url(detail_url) or f"gmaps:{abs(hash(label + href))}"
                    external_id = f"gmaps:{cid}"

                    # Address
                    addr = None
                    addr_locator = page.locator("button[data-item-id='address']")
                    if await addr_locator.count() > 0:
                        addr = await addr_locator.first.get_attribute("aria-label")
                        if addr and addr.startswith("Dirección:"):
                            addr = addr.replace("Dirección:", "").strip()

                    # Phone
                    phone = None
                    phone_locator = page.locator("button[data-item-id^='phone:']")
                    if await phone_locator.count() > 0:
                        phone = await phone_locator.first.get_attribute("aria-label")
                        if phone and phone.startswith("Teléfono:"):
                            phone = phone.replace("Teléfono:", "").strip()

                    # Website
                    website = None
                    web_locator = page.locator("a[data-item-id='authority']")
                    if await web_locator.count() > 0:
                        raw_web = await web_locator.first.get_attribute("href")
                        website = self._clean_website_url(raw_web)

                    # Rating and reviews
                    rating = None
                    review_count = 0
                    stars_locator = page.locator("div.F7nice")
                    if await stars_locator.count() > 0:
                        stars_text = await stars_locator.first.inner_text()
                        rating_match = re.search(r"(\d+[\.,]\d+)", stars_text)
                        if rating_match:
                            rating = float(rating_match.group(1).replace(",", "."))
                        rev_match = re.search(r"\((\d+[\d,.]*)\)", stars_text)
                        if rev_match:
                            cleaned_rev = rev_match.group(1).replace(".", "").replace(",", "")
                            review_count = int(cleaned_rev)

                    # Operating status
                    opening_hours = None
                    hours_locator = page.locator("button[data-item-id*='oh']")
                    if await hours_locator.count() > 0:
                        opening_hours = await hours_locator.first.get_attribute("aria-label")

                    # Primary category shown in header
                    category_name = None
                    cat_locator = page.locator("button[jsaction*='category']")
                    if await cat_locator.count() > 0:
                        category_name = await cat_locator.first.inner_text()

                    # Unclaimed business check
                    unclaimed_locator = page.locator("text='Reclamar esta empresa'")
                    is_claimed = True
                    if await unclaimed_locator.count() > 0:
                        is_claimed = False

                    leads.append({
                        "external_source": "google_maps",
                        "external_id": external_id,
                        "name": label.strip(),
                        "category_slug": category_slug,
                        "primary_category": category_name or keyword,
                        "subcategories": [category_name] if category_name else [],
                        "phone_raw": phone,
                        "phone_normalized": None,
                        "website": website,
                        "address_raw": addr,
                        "street": None,
                        "house_number": None,
                        "suburb": None,
                        "postal_code": None,
                        "city": "Tijuana",
                        "state": "Baja California",
                        "country": "Mexico",
                        "latitude": lat,
                        "longitude": lon,
                        "rating": rating,
                        "review_count": review_count,
                        "opening_hours_raw": opening_hours,
                        "is_claimed": is_claimed,
                        "lifecycle_stage": "EXTRACTED",
                        "extra_metadata": {
                            "google_cid": cid,
                            "search_keyword": keyword,
                            "detail_url": detail_url
                        }
                    })

                except Exception as item_err:
                    logger.warning(f"Error parsing item {idx}: {item_err}")
                    continue

        finally:
            await context.close()

        return leads
