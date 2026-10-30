import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.db.connection import get_db_connection, execute_query
from src.geo.bounds import MACRO_ZONES
from src.queue.redis_queue import queue_manager

logger = logging.getLogger("crm.api.geo_map")
router = APIRouter(prefix="/api/v1/geo", tags=["Geo & Interactive Map"])


class SweepRequest(BaseModel):
    zone_slug: Optional[str] = "zona-rio"
    category_slug: str = "dentistas"
    custom_bbox: Optional[Dict[str, float]] = None
    cell_size_km: float = 1.0


@router.get("/zones")
def list_tijuana_zones():
    zones_list = []
    zone_centers = {
        "zona-rio": {"lat": 32.5270, "lon": -117.0220},
        "centro": {"lat": 32.5340, "lon": -117.0390},
        "otay": {"lat": 32.5360, "lon": -116.9750},
        "la-mesa": {"lat": 32.5020, "lon": -116.9750},
        "playas": {"lat": 32.5230, "lon": -117.1150},
        "chapultepec-hipodromo": {"lat": 32.5090, "lon": -117.0050},
        "tijuana-full": {"lat": 32.5149, "lon": -117.0382}
    }

    zone_display_names = {
        "zona-rio": "Zona Rio",
        "centro": "Zona Centro",
        "otay": "Mesa de Otay",
        "la-mesa": "La Mesa",
        "playas": "Playas de Tijuana",
        "chapultepec-hipodromo": "Chapultepec / Hipodromo",
        "tijuana-full": "Tijuana Completa"
    }

    for slug, bbox_tuple in MACRO_ZONES.items():
        min_lat, min_lon, max_lat, max_lon = bbox_tuple
        center = zone_centers.get(slug, {"lat": (min_lat + max_lat) / 2, "lon": (min_lon + max_lon) / 2})
        zones_list.append({
            "slug": slug,
            "name": zone_display_names.get(slug, slug.replace("-", " ").title()),
            "center": center,
            "bbox": {
                "min_lat": min_lat,
                "min_lon": min_lon,
                "max_lat": max_lat,
                "max_lon": max_lon
            }
        })

    return {"zones": zones_list, "default_center": [32.5149, -117.0382]}


@router.get("/leads-markers")
def get_leads_markers(category_slug: Optional[str] = None):
    conditions = ["is_deleted = FALSE", "latitude IS NOT NULL", "longitude IS NOT NULL"]
    params = []
    if category_slug:
        conditions.append("category_slug = %s")
        params.append(category_slug)

    sql = f"""
    SELECT id, name, category_slug, primary_category, latitude, longitude,
           phone_e164, phone_raw, has_whatsapp, acceptance_probability_pct,
           lifecycle_stage
    FROM leads
    WHERE {' AND '.join(conditions)}
    ORDER BY created_at DESC
    LIMIT 300;
    """
    rows = execute_query(sql, tuple(params))

    # WhatsApp template
    tmpl_row = execute_query("SELECT value FROM system_settings WHERE key = 'whatsapp_template';")
    tmpl = tmpl_row[0]["value"] if tmpl_row else "Hola, buen día."

    markers = []
    for r in rows:
        phone_clean = (r.get("phone_e164") or r.get("phone_raw") or "").replace("+", "").replace(" ", "").replace("-", "")
        wa_url = None
        if r.get("has_whatsapp") and phone_clean:
            import urllib.parse
            msg = tmpl.replace("{nombre}", r["name"])
            wa_url = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(msg)}"

        markers.append({
            "id": str(r["id"]),
            "name": r["name"],
            "category": r["primary_category"] or r["category_slug"],
            "lat": float(r["latitude"]),
            "lon": float(r["longitude"]),
            "phone": r.get("phone_e164") or r.get("phone_raw") or "Sin tel",
            "score": round(float(r["acceptance_probability_pct"] or 0)),
            "stage": r["lifecycle_stage"],
            "whatsapp_url": wa_url
        })

    return {"markers": markers, "count": len(markers)}


@router.post("/sweep")
async def trigger_geo_sweep(payload: SweepRequest):
    from src.api.jobs import create_job
    from src.models.schemas import ExtractionJobCreate, BoundingBox

    custom_bb = None
    if payload.custom_bbox:
        custom_bb = BoundingBox(
            min_lat=payload.custom_bbox["min_lat"],
            min_lon=payload.custom_bbox["min_lon"],
            max_lat=payload.custom_bbox["max_lat"],
            max_lon=payload.custom_bbox["max_lon"]
        )

    job_create = ExtractionJobCreate(
        category_slug=payload.category_slug,
        zone_name=payload.zone_slug or "zona-rio",
        custom_bbox=custom_bb,
        cell_size_km=payload.cell_size_km
    )

    job_telemetry = await create_job(job_create)
    return {
        "status": "QUEUED",
        "job_id": str(job_telemetry.id),
        "zone": payload.zone_slug,
        "category": payload.category_slug
    }


@router.get("/jobs/active")
def get_active_job():
    rows = execute_query(
        """
        SELECT id, category_slug, source, zone_name, status, total_cells,
               completed_cells, failed_cells, leads_found, leads_saved,
               leads_skipped, created_at, started_at
        FROM extraction_jobs
        ORDER BY created_at DESC
        LIMIT 1;
        """
    )
    if not rows:
        return {"has_active_job": False}

    j = rows[0]
    job_id = j["id"]

    # Fetch cells for polygon rendering
    cell_rows = execute_query(
        """
        SELECT cell_code, depth, min_lat, min_lon, max_lat, max_lon, status, results_count
        FROM extraction_grid_cells
        WHERE job_id = %s;
        """,
        (str(job_id),)
    )

    pct = 0.0
    if j["total_cells"] > 0:
        pct = round((j["completed_cells"] / j["total_cells"]) * 100, 1)

    return {
        "has_active_job": True,
        "job": {
            "id": str(j["id"]),
            "category_slug": j["category_slug"],
            "source": j["source"],
            "zone_name": j["zone_name"],
            "status": j["status"],
            "total_cells": j["total_cells"],
            "completed_cells": j["completed_cells"],
            "failed_cells": j["failed_cells"],
            "progress_pct": pct,
            "leads_found": j["leads_found"],
            "leads_saved": j["leads_saved"],
            "leads_skipped": j["leads_skipped"]
        },
        "cells": [
            {
                "code": c["cell_code"],
                "depth": c["depth"],
                "bounds": [
                    [float(c["min_lat"]), float(c["min_lon"])],
                    [float(c["max_lat"]), float(c["max_lon"])]
                ],
                "status": c["status"],
                "count": c["results_count"]
            }
            for c in cell_rows
        ]
    }
