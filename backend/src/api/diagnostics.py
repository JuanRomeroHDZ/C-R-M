import asyncio
import datetime
import logging
import time
from typing import Dict, Any
import httpx
from fastapi import APIRouter
from playwright.async_api import async_playwright
from src.db.connection import get_db_connection, execute_query
from src.queue.redis_queue import queue_manager

logger = logging.getLogger("crm.api.diagnostics")
router = APIRouter(prefix="/api/v1/diagnostics", tags=["Diagnostics & Self-Check"])


@router.get("/health-check")
async def run_diagnostics() -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "HEALTHY",
        "services": {}
    }

    # 1. PostgreSQL Check
    t0 = time.perf_counter()
    try:
        leads_res = execute_query("SELECT count(*) as count FROM leads WHERE is_deleted = FALSE;")
        pg_ms = round((time.perf_counter() - t0) * 1000, 1)
        results["services"]["postgres"] = {
            "status": "OK",
            "active_leads_count": leads_res[0]["count"] if leads_res else 0,
            "latency_ms": pg_ms
        }
    except Exception as e:
        results["status"] = "DEGRADED"
        results["services"]["postgres"] = {"status": "ERROR", "error": str(e)}

    # 2. Redis Check
    t0 = time.perf_counter()
    try:
        r = await queue_manager.get_client()
        pong = await r.ping()
        redis_ms = round((time.perf_counter() - t0) * 1000, 1)
        queue_len = await r.llen("crm:queue:jobs")
        results["services"]["redis"] = {
            "status": "OK" if pong else "WARN",
            "latency_ms": redis_ms,
            "pending_jobs_queue": queue_len
        }
    except Exception as e:
        results["status"] = "DEGRADED"
        results["services"]["redis"] = {"status": "ERROR", "error": str(e)}

    # 3. Headless Chromium in Container Test
    t0 = time.perf_counter()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            context = await browser.new_context(
                locale="es-MX",
                extra_http_headers={"Accept-Language": "es-MX,es;q=0.9,en;q=0.8"}
            )
            page = await context.new_page()
            await page.goto("about:blank", timeout=8000)
            val = await page.evaluate("1 + 1")
            await browser.close()

            chrom_ms = round((time.perf_counter() - t0) * 1000, 1)
            results["services"]["chromium_headless"] = {
                "status": "OK" if val == 2 else "WARN",
                "execution_ms": chrom_ms,
                "sandbox": "in-memory (no-sandbox / dev-shm 2gb)"
            }
    except Exception as e:
        results["status"] = "DEGRADED"
        results["services"]["chromium_headless"] = {"status": "ERROR", "error": str(e)}

    # 4. Outbound Nominatim API
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": "Tijuana", "format": "jsonv2", "limit": 1},
                headers={"User-Agent": "CRM-Local-Diagnostics/7.0"}
            )
            nom_ms = round((time.perf_counter() - t0) * 1000, 1)
            results["services"]["nominatim_api"] = {
                "status": "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}",
                "latency_ms": nom_ms
            }
    except Exception as e:
        results["services"]["nominatim_api"] = {"status": "ERROR", "error": str(e)}

    # 5. Outbound Overpass API Status
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                "https://overpass-api.de/api/status",
                headers={"User-Agent": "Mozilla/5.0 (CRM-Local-Diagnostics/7.0)"}
            )
            over_ms = round((time.perf_counter() - t0) * 1000, 1)
            results["services"]["overpass_api"] = {
                "status": "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}",
                "latency_ms": over_ms
            }
    except Exception as e:
        results["services"]["overpass_api"] = {
            "status": "BUSY",
            "message": "Espejos Overpass con alta latencia (conmutacion automatica a Google Maps)"
        }

    # 6. Outbound Google Maps
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.head(
                "https://www.google.com/maps",
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            )
            gmaps_ms = round((time.perf_counter() - t0) * 1000, 1)
            results["services"]["google_maps"] = {
                "status": "OK" if resp.status_code in (200, 301, 302) else f"HTTP {resp.status_code}",
                "latency_ms": gmaps_ms
            }
    except Exception as e:
        results["services"]["google_maps"] = {"status": "ERROR", "error": str(e)}

    return results
