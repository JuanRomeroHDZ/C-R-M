import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from src.db.connection import get_db_connection, execute_query
from src.geo.bounds import get_zone_bounds
from src.geo.quadtree import generate_initial_grid
from src.models.schemas import ExtractionJobCreate, ExtractionJobTelemetry
from src.queue.redis_queue import queue_manager, STATE_QUEUED, STATE_PAUSED, STATE_RUNNING, STATE_CANCELLED

router = APIRouter(prefix="/api/v1/extraction/jobs", tags=["Jobs"])


def _hydrate_telemetry(row: dict) -> ExtractionJobTelemetry:
    total = row["total_cells"]
    completed = row["completed_cells"]
    pct = round((completed / total * 100.0), 2) if total > 0 else 0.0

    started = row["started_at"]
    finished = row["completed_at"]
    elapsed = None
    eta = None

    if started:
        now = datetime.now(timezone.utc)
        ref_end = finished if finished else now
        # make sure started has tz
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed = round((ref_end - started).total_seconds(), 1)

        if completed > 0 and total > completed:
            avg_per_cell = elapsed / completed
            remaining_cells = total - completed
            eta = round(avg_per_cell * remaining_cells, 1)

    return ExtractionJobTelemetry(
        id=row["id"],
        category_slug=row["category_slug"],
        source=row["source"],
        zone_name=row["zone_name"],
        status=row["status"],
        total_cells=total,
        completed_cells=completed,
        failed_cells=row["failed_cells"],
        progress_percentage=pct,
        leads_found=row["leads_found"],
        leads_saved=row["leads_saved"],
        leads_skipped=row["leads_skipped"],
        active_source=row["source"],
        elapsed_seconds=elapsed,
        estimated_remaining_seconds=eta,
        created_at=row["created_at"],
        started_at=started,
        completed_at=finished,
        error_message=row["error_message"]
    )


@router.post("", response_model=ExtractionJobTelemetry, status_code=status.HTTP_201_CREATED)
async def create_job(payload: ExtractionJobCreate):
    # Verify or dynamically register category
    cat_rows = execute_query(
        "SELECT id, slug FROM categories WHERE slug = %s AND is_active = TRUE;",
        (payload.category_slug,)
    )
    if not cat_rows:
        clean_name = payload.category_slug.replace("-", " ").title()
        slug = payload.category_slug.strip().lower()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO categories (name, slug, is_active)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (slug) DO UPDATE SET is_active = TRUE
                    RETURNING id, slug;
                    """,
                    (clean_name, slug)
                )
                inserted = cur.fetchone()
                cat_id = inserted["id"]
                cur.execute(
                    """
                    INSERT INTO category_keywords (category_id, keyword)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (cat_id, clean_name.lower())
                )
            conn.commit()
    else:
        cat_id = cat_rows[0]["id"]

    # Determine Bounding Box
    if payload.custom_bbox:
        min_lat = payload.custom_bbox.min_lat
        min_lon = payload.custom_bbox.min_lon
        max_lat = payload.custom_bbox.max_lat
        max_lon = payload.custom_bbox.max_lon
    else:
        min_lat, min_lon, max_lat, max_lon = get_zone_bounds(payload.zone_name)

    # Generate initial grid cells
    cells = generate_initial_grid(
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        cell_size_km=payload.cell_size_km
    )

    config_dict = {
        "cell_size_km": payload.cell_size_km,
        "max_depth": payload.max_depth,
        "saturation_threshold": payload.saturation_threshold,
        "bbox": [min_lat, min_lon, max_lat, max_lon]
    }

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO extraction_jobs (
                    category_id, category_slug, source, zone_name,
                    status, total_cells, config_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, category_slug, source, zone_name, status,
                          total_cells, completed_cells, failed_cells,
                          leads_found, leads_saved, leads_skipped,
                          created_at, started_at, completed_at, error_message;
                """,
                (
                    cat_id, payload.category_slug, payload.source, payload.zone_name,
                    STATE_QUEUED, len(cells), json.dumps(config_dict)
                )
            )
            job_row = cur.fetchone()
            job_id = str(job_row["id"])

            for cell in cells:
                cur.execute(
                    """
                    INSERT INTO extraction_grid_cells (
                        job_id, cell_code, depth, min_lat, min_lon, max_lat, max_lon, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING')
                    RETURNING id;
                    """,
                    (
                        job_id, cell["cell_code"], cell["depth"],
                        cell["min_lat"], cell["min_lon"], cell["max_lat"], cell["max_lon"]
                    )
                )
                cell_row = cur.fetchone()
                cell["id"] = str(cell_row["id"])
                await queue_manager.enqueue_cell(job_id, cell)

    await queue_manager.enqueue_job(job_id)
    return _hydrate_telemetry(job_row)


@router.get("", response_model=List[ExtractionJobTelemetry])
def list_jobs(limit: int = 20):
    rows = execute_query(
        """
        SELECT id, category_slug, source, zone_name, status,
               total_cells, completed_cells, failed_cells,
               leads_found, leads_saved, leads_skipped,
               created_at, started_at, completed_at, error_message
        FROM extraction_jobs
        ORDER BY created_at DESC
        LIMIT %s;
        """,
        (limit,)
    )
    return [_hydrate_telemetry(r) for r in rows]


@router.get("/{job_id}", response_model=ExtractionJobTelemetry)
def get_job(job_id: UUID):
    rows = execute_query(
        """
        SELECT id, category_slug, source, zone_name, status,
               total_cells, completed_cells, failed_cells,
               leads_found, leads_saved, leads_skipped,
               created_at, started_at, completed_at, error_message
        FROM extraction_jobs
        WHERE id = %s;
        """,
        (str(job_id),)
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return _hydrate_telemetry(rows[0])


@router.post("/{job_id}/pause", response_model=ExtractionJobTelemetry)
async def pause_job(job_id: UUID):
    job_str = str(job_id)
    rows = execute_query("SELECT id FROM extraction_jobs WHERE id = %s;", (job_str,))
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    await queue_manager.pause_job(job_str)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE extraction_jobs SET status = %s WHERE id = %s;", (STATE_PAUSED, job_str))

    return get_job(job_id)


@router.post("/{job_id}/resume", response_model=ExtractionJobTelemetry)
async def resume_job(job_id: UUID):
    job_str = str(job_id)
    rows = execute_query("SELECT id FROM extraction_jobs WHERE id = %s;", (job_str,))
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    await queue_manager.resume_job(job_str)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE extraction_jobs SET status = %s WHERE id = %s;", (STATE_RUNNING, job_str))

    return get_job(job_id)


@router.post("/{job_id}/cancel", response_model=ExtractionJobTelemetry)
async def cancel_job(job_id: UUID):
    job_str = str(job_id)
    rows = execute_query("SELECT id FROM extraction_jobs WHERE id = %s;", (job_str,))
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    await queue_manager.cancel_job(job_str)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE extraction_jobs SET status = %s WHERE id = %s;", (STATE_CANCELLED, job_str))

    return get_job(job_id)
