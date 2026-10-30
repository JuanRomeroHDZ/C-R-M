from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from src.analysis.pipeline import process_and_audit_lead
from src.db.connection import execute_query
from src.queue.redis_queue import queue_manager

router = APIRouter(prefix="/api/v1", tags=["Audits"])


@router.post("/leads/{lead_id}/audit")
async def audit_single_lead(lead_id: UUID):
    res = await process_and_audit_lead(str(lead_id))
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/leads/{lead_id}/audit")
def get_lead_audit(lead_id: UUID):
    rows = execute_query(
        """
        SELECT * FROM lead_web_audits
        WHERE lead_id = %s
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        (str(lead_id),)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No audit found for this lead.")
    return rows[0]


@router.post("/audit/batch")
async def trigger_batch_audit(category_slug: Optional[str] = None):
    sql = "SELECT id FROM leads WHERE is_deleted = FALSE"
    params = []
    if category_slug:
        sql += " AND category_slug = %s"
        params.append(category_slug)
    sql += " AND (lifecycle_stage = 'EXTRACTED' OR audited_at IS NULL);"

    rows = execute_query(sql, tuple(params))
    enqueued = 0
    for r in rows:
        await queue_manager.enqueue_audit(str(r["id"]))
        enqueued += 1

    return {
        "status": "QUEUED",
        "enqueued_leads": enqueued,
        "message": f"Enqueued {enqueued} leads for background technical audit and scoring."
    }
