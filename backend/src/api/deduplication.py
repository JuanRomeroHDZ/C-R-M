from typing import Optional, List
from fastapi import APIRouter, Query
from src.analysis.deduplication import run_multilayer_deduplication
from src.db.connection import execute_query
from src.queue.redis_queue import queue_manager

router = APIRouter(prefix="/api/v1/deduplication", tags=["Deduplication"])


@router.post("/run")
def trigger_deduplication(category_slug: Optional[str] = None):
    result = run_multilayer_deduplication(category_slug)
    return {
        "status": "COMPLETED",
        "result": result
    }


@router.get("/history")
def list_deduplication_history(limit: int = Query(default=50, ge=1, le=200)):
    rows = execute_query(
        """
        SELECT h.id, h.master_lead_id, h.merged_lead_id, h.merge_reason,
               h.similarity_score, h.details, h.created_at,
               m.name as master_name, m.phone_e164 as master_phone
        FROM deduplication_history h
        JOIN leads m ON m.id = h.master_lead_id
        ORDER BY h.created_at DESC
        LIMIT %s;
        """,
        (limit,)
    )
    return rows
