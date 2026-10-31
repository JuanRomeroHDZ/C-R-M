import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from src.config import settings
from src.db.connection import get_db_connection, execute_query
from src.extractors.osm_engine import OSMExtractor
from src.extractors.gmaps_engine import GoogleMapsExtractor, CircuitBreakerTriggered
from src.geo.quadtree import split_cell
from src.api.events_bus import event_bus
from src.analysis.pipeline import process_and_audit_lead
from src.analysis.channel_enricher import enrich_lead_channels
from src.queue.redis_queue import (
    queue_manager,
    STATE_QUEUED,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_COOLDOWN,
    STATE_COMPLETED,
    STATE_CANCELLED,
    STATE_FAILED
)

logger = logging.getLogger("crm.queue.worker")


def save_lead(lead: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    phone_clean = lead.get("phone_normalized") or lead.get("phone_raw")
    ext_id = lead.get("external_id")
    norm_domain = lead.get("normalized_domain")

    # Immunity check against soft-deleted / blacklisted leads
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM blacklist_identifiers
                WHERE (phone_e164 IS NOT NULL AND phone_e164 = %s)
                   OR (external_id IS NOT NULL AND external_id = %s)
                   OR (normalized_domain IS NOT NULL AND normalized_domain = %s)
                LIMIT 1;
                """,
                (phone_clean, ext_id, norm_domain)
            )
            if cur.fetchone():
                return "skipped", None

    subcategories_json = json.dumps(lead.get("subcategories", []))
    metadata_json = json.dumps(lead.get("extra_metadata", {}))

    query = """
    INSERT INTO leads (
        external_source, external_id, name, category_slug, primary_category, subcategories,
        phone_raw, phone_normalized, website, address_raw, street, house_number, suburb,
        postal_code, city, state, country, latitude, longitude, rating, review_count,
        opening_hours_raw, is_claimed, lifecycle_stage, extra_metadata, last_seen_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, NOW()
    )
    ON CONFLICT (external_source, external_id) DO UPDATE SET
        rating = EXCLUDED.rating,
        review_count = EXCLUDED.review_count,
        last_seen_at = EXCLUDED.last_seen_at,
        updated_at = NOW(),
        extra_metadata = leads.extra_metadata || EXCLUDED.extra_metadata
    WHERE leads.is_deleted = FALSE
    RETURNING id, (xmax = 0) AS inserted;
    """

    params = (
        lead["external_source"],
        lead["external_id"],
        lead["name"],
        lead["category_slug"],
        lead.get("primary_category"),
        subcategories_json,
        lead.get("phone_raw"),
        lead.get("phone_normalized"),
        lead.get("website"),
        lead.get("address_raw"),
        lead.get("street"),
        lead.get("house_number"),
        lead.get("suburb"),
        lead.get("postal_code"),
        lead.get("city", "Tijuana"),
        lead.get("state", "Baja California"),
        lead.get("country", "Mexico"),
        lead.get("latitude"),
        lead.get("longitude"),
        lead.get("rating"),
        lead.get("review_count", 0),
        lead.get("opening_hours_raw"),
        lead.get("is_claimed"),
        lead.get("lifecycle_stage", "EXTRACTED"),
        metadata_json
    )

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if row is None:
                return "skipped", None  # Record was soft-deleted, conflict update skipped
            return ("inserted" if row["inserted"] else "updated"), str(row["id"])


class ExtractionWorker:
    def __init__(self):
        self.osm_extractor = OSMExtractor()
        self.gmaps_extractor = GoogleMapsExtractor()
        self.is_running = False

    async def get_category_data(self, slug: str) -> Dict[str, Any]:
        rows = execute_query("SELECT id, slug, name FROM categories WHERE slug = %s;", (slug,))
        if not rows:
            return {"slug": slug, "keywords": [slug], "osm_tags": []}

        cat = rows[0]
        cat_id = cat["id"]

        kw_rows = execute_query("SELECT keyword FROM category_keywords WHERE category_id = %s;", (cat_id,))
        keywords = [r["keyword"] for r in kw_rows]

        osm_rows = execute_query("SELECT key, value FROM category_osm_tags WHERE category_id = %s;", (cat_id,))
        osm_tags = [(r["key"], r["value"]) for r in osm_rows]

        return {
            "id": cat_id,
            "slug": slug,
            "name": cat["name"],
            "keywords": keywords if keywords else [slug],
            "osm_tags": osm_tags
        }

    async def process_single_cell(
        self,
        job_id: str,
        cell: Dict[str, Any],
        category_data: Dict[str, Any],
        source: str,
        saturation_threshold: int = 20,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        min_lat = float(cell["min_lat"])
        min_lon = float(cell["min_lon"])
        max_lat = float(cell["max_lat"])
        max_lon = float(cell["max_lon"])
        depth = int(cell.get("depth", 0))
        cell_code = cell.get("cell_code", "cell")
        cell_id = cell.get("id")

        collected_leads: List[Dict[str, Any]] = []

        # 1. OpenStreetMap Extraction
        if source in ("osm", "hybrid"):
            try:
                search_kw = category_data.get("name") or category_data["slug"]
                osm_leads = await self.osm_extractor.extract_cell(
                    osm_tags=category_data.get("osm_tags", []),
                    category_slug=category_data["slug"],
                    min_lat=min_lat,
                    min_lon=min_lon,
                    max_lat=max_lat,
                    max_lon=max_lon,
                    search_term=search_kw,
                    target_city=category_data.get("zone_name")
                )
                collected_leads.extend(osm_leads)
            except Exception as e:
                logger.warning(f"Error in OSM extraction for cell {cell_code}: {e}")

        # 2. Google Maps Extraction
        if source in ("google_maps", "hybrid"):
            is_blocked = await queue_manager.is_circuit_breaker_active()
            if not is_blocked:
                keyword = category_data["keywords"][0] if category_data.get("keywords") else category_data["slug"]
                try:
                    gmaps_leads = await self.gmaps_extractor.search_cell(
                        keyword=keyword,
                        category_slug=category_data["slug"],
                        min_lat=min_lat,
                        min_lon=min_lon,
                        max_lat=max_lat,
                        max_lon=max_lon,
                        location_name=category_data.get("zone_name")
                    )
                    collected_leads.extend(gmaps_leads)
                except CircuitBreakerTriggered as cb_err:
                    logger.error(f"Circuit breaker triggered on Google Maps: {cb_err}")
                    await queue_manager.set_circuit_breaker(
                        settings.CIRCUIT_BREAKER_COOLDOWN_SECONDS,
                        reason=str(cb_err)
                    )
                except Exception as e:
                    logger.warning(f"Error in Google Maps extraction for cell {cell_code}: {e}")

        # 3. Adaptive Quadtree Splitting if Saturated
        if len(collected_leads) >= saturation_threshold and depth < max_depth:
            logger.info(
                f"Cell {cell_code} reached saturation ({len(collected_leads)} results >= {saturation_threshold}). "
                f"Splitting into 4 sub-quadrants (depth {depth+1})..."
            )
            sub_cells = split_cell(min_lat, min_lon, max_lat, max_lon, cell_code, depth)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    for sub in sub_cells:
                        cur.execute(
                            """
                            INSERT INTO extraction_grid_cells (
                                job_id, cell_code, parent_cell_id, depth,
                                min_lat, min_lon, max_lat, max_lon, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
                            RETURNING id;
                            """,
                            (
                                job_id, sub["cell_code"], cell_id, sub["depth"],
                                sub["min_lat"], sub["min_lon"], sub["max_lat"], sub["max_lon"]
                            )
                        )
                        row = cur.fetchone()
                        sub["id"] = str(row["id"])
                        await queue_manager.enqueue_cell(job_id, sub)

                    # Update parent status
                    if cell_id:
                        cur.execute(
                            "UPDATE extraction_grid_cells SET status = 'SPLIT', results_count = %s WHERE id = %s;",
                            (len(collected_leads), cell_id)
                        )
                    # Increment total cells on job
                    cur.execute(
                        "UPDATE extraction_jobs SET total_cells = total_cells + 4 WHERE id = %s;",
                        (job_id,)
                    )

            # Save the leads found so far from this saturated overview
            saved_count = 0
            for lead in collected_leads:
                res = save_lead(lead)
                if res in ("inserted", "updated"):
                    saved_count += 1

            return {"status": "SPLIT", "leads_found": len(collected_leads), "leads_saved": saved_count}

        # 4. Save leads to database and chain audit + enrichment + streaming
        saved_count = 0
        skipped_count = 0
        for lead in collected_leads:
            res, lead_id = save_lead(lead)
            if res in ("inserted", "updated") and lead_id:
                saved_count += 1
                try:
                    await event_bus.broadcast("status_update", {
                        "step": f"Analizando oportunidad comercial: {lead['name']}...",
                        "job_id": job_id
                    })
                    # Chain technical web audit and lead scoring
                    await process_and_audit_lead(lead_id)
                    # Chain channel enrichment (socials & emails)
                    enrich_lead_channels(lead_id)

                    from src.analysis.pitch_generator import generate_commercial_pitch
                    from src.analysis.opening_hours import evaluate_opening_hours
                    generated_pitch = generate_commercial_pitch(lead_id)

                    fl_rows = execute_query(
                        """
                        SELECT id, name, category_slug, primary_category, latitude, longitude,
                               phone_e164, phone_raw, has_whatsapp, acceptance_probability_pct,
                               technical_health_score, lifecycle_stage, website, city,
                               opening_hours_raw, tags, deal_value_estimated, commercial_pitch
                        FROM leads WHERE id = %s;
                        """,
                        (lead_id,)
                    )
                    if fl_rows:
                        fl = fl_rows[0]
                        wa_url = None
                        if fl.get("phone_e164"):
                            clean_phone = re.sub(r"[^\d]", "", fl["phone_e164"])
                            wa_url = f"https://wa.me/{clean_phone}?text=Hola%2C%20buen%20d%C3%ADa."

                        is_open, open_label = evaluate_opening_hours(fl.get("opening_hours_raw"))

                        await event_bus.broadcast("lead_captured", {
                            "id": str(fl["id"]),
                            "name": fl["name"],
                            "category": fl["category_slug"],
                            "primary_category": fl.get("primary_category"),
                            "lat": float(fl["latitude"]) if fl.get("latitude") else None,
                            "lon": float(fl["longitude"]) if fl.get("longitude") else None,
                            "phone": fl.get("phone_e164") or fl.get("phone_raw") or "Sin tel",
                            "score": round(float(fl["acceptance_probability_pct"] or 0)),
                            "health_score": round(float(fl["technical_health_score"] or 0)),
                            "stage": fl["lifecycle_stage"],
                            "website": fl.get("website"),
                            "city": fl.get("city"),
                            "whatsapp_url": wa_url,
                            "is_open_now": is_open,
                            "open_status_label": open_label,
                            "commercial_pitch": fl.get("commercial_pitch") or generated_pitch,
                            "deal_value_estimated": float(fl["deal_value_estimated"]) if fl.get("deal_value_estimated") is not None else None,
                            "tags": fl.get("tags") or []
                        })
                except Exception as chain_err:
                    logger.warning(f"Error in chained processing for lead {lead_id}: {chain_err}")
            else:
                skipped_count += 1

        # 5. Update cell status in database
        if cell_id:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE extraction_grid_cells
                        SET status = 'COMPLETED', results_count = %s, last_scanned_at = NOW()
                        WHERE id = %s;
                        """,
                        (len(collected_leads), cell_id)
                    )

        return {
            "status": "COMPLETED",
            "leads_found": len(collected_leads),
            "leads_saved": saved_count,
            "leads_skipped": skipped_count
        }

    async def execute_job(self, job_id: str):
        job_rows = execute_query(
            "SELECT id, category_slug, zone_name, source, config_json, status FROM extraction_jobs WHERE id = %s;",
            (job_id,)
        )
        if not job_rows:
            logger.error(f"Job {job_id} not found in database.")
            return

        job = job_rows[0]
        cat_slug = job["category_slug"]
        source = job["source"]
        config = job.get("config_json", {})
        saturation_threshold = config.get("saturation_threshold", 20)
        max_depth = config.get("max_depth", 3)

        category_data = await self.get_category_data(cat_slug)
        category_data["zone_name"] = job.get("zone_name")

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE extraction_jobs SET status = %s, started_at = NOW() WHERE id = %s;",
                    (STATE_RUNNING, job_id)
                )
        await queue_manager.set_job_status(job_id, STATE_RUNNING)

        while True:
            # Check pause / cancel
            if await queue_manager.is_job_cancelled(job_id):
                logger.info(f"Job {job_id} was cancelled.")
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE extraction_jobs SET status = %s WHERE id = %s;", (STATE_CANCELLED, job_id))
                break

            while await queue_manager.is_job_paused(job_id):
                await asyncio.sleep(2.0)
                if await queue_manager.is_job_cancelled(job_id):
                    break

            cell = await queue_manager.get_next_cell(job_id)
            if not cell:
                # No more cells in queue
                break

            try:
                res = await self.process_single_cell(
                    job_id=job_id,
                    cell=cell,
                    category_data=category_data,
                    source=source,
                    saturation_threshold=saturation_threshold,
                    max_depth=max_depth
                )

                # Update job counters
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE extraction_jobs
                            SET completed_cells = completed_cells + 1,
                                leads_found = leads_found + %s,
                                leads_saved = leads_saved + %s,
                                leads_skipped = leads_skipped + %s
                            WHERE id = %s;
                            """,
                            (res.get("leads_found", 0), res.get("leads_saved", 0), res.get("leads_skipped", 0), job_id)
                        )

            except Exception as cell_err:
                logger.error(f"Error processing cell {cell.get('cell_code')}: {cell_err}")
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE extraction_jobs SET failed_cells = failed_cells + 1 WHERE id = %s;",
                            (job_id,)
                        )

            # Polling delay between cells for residential IP safety
            await asyncio.sleep(1.0)

        # Mark completed if not cancelled
        if not await queue_manager.is_job_cancelled(job_id):
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE extraction_jobs SET status = %s, completed_at = NOW() WHERE id = %s;",
                        (STATE_COMPLETED, job_id)
                    )
            await queue_manager.set_job_status(job_id, STATE_COMPLETED)
            logger.info(f"Extraction job {job_id} successfully completed.")

    async def run_worker_loop(self):
        self.is_running = True
        logger.info("Extraction and analysis background worker loop initialized.")
        while self.is_running:
            # 1. Process Extraction Jobs
            job_id = await queue_manager.get_next_job()
            if job_id:
                logger.info(f"Worker picked up extraction job {job_id} from queue.")
                await self.execute_job(job_id)
                continue

            # 2. Process Deduplication Tasks
            dedup_task = await queue_manager.get_next_dedup()
            if dedup_task is not None:
                from src.analysis.deduplication import run_multilayer_deduplication
                logger.info(f"Worker processing deduplication task (Category: {dedup_task or 'ALL'})")
                cat = dedup_task if dedup_task != "" else None
                run_multilayer_deduplication(cat)
                continue

            # 3. Process Audit Tasks
            audit_lead_id = await queue_manager.get_next_audit()
            if audit_lead_id:
                from src.analysis.pipeline import process_and_audit_lead
                logger.info(f"Worker processing web audit for lead: {audit_lead_id}")
                try:
                    await process_and_audit_lead(audit_lead_id)
                except Exception as audit_err:
                    logger.warning(f"Error in background audit for lead {audit_lead_id}: {audit_err}")
                continue

            await asyncio.sleep(2.0)


worker_instance = ExtractionWorker()
