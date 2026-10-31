from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from src.analysis.deduplication import (
    run_multilayer_deduplication,
    clean_commercial_name,
    haversine_distance_meters,
    merge_two_leads
)
from src.db.connection import get_db_connection, execute_query

router = APIRouter(prefix="/api/v1/deduplication", tags=["Deduplication"])


class SuspectedResolveRequest(BaseModel):
    action: str = Field(..., pattern="^(merge|whitelist)$")
    lead_a_id: UUID
    lead_b_id: UUID
    master_id: Optional[UUID] = None


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


@router.get("/suspected-duplicates")
def get_suspected_duplicates():
    # 1. Fetch whitelisted pairs
    whitelist_rows = execute_query("SELECT lead_a_id, lead_b_id FROM deduplication_whitelist;")
    whitelisted = {
        frozenset([str(r["lead_a_id"]), str(r["lead_b_id"])])
        for r in whitelist_rows
    }

    # 2. Fetch active leads
    sql = """
    SELECT id, name, category_slug, phone_raw, phone_e164, website, normalized_domain,
           suburb, city, rating, review_count, latitude, longitude,
           acceptance_probability_pct, lifecycle_stage
    FROM leads
    WHERE is_deleted = FALSE
    ORDER BY created_at ASC;
    """
    leads = execute_query(sql)

    suspected = []
    lead_suspected_map = {} # map lead_id to list of pair_ids

    for i in range(len(leads)):
        l1 = leads[i]
        id1 = str(l1["id"])
        c1 = clean_commercial_name(l1["name"] or "")
        if not c1 or len(c1) < 3:
            continue

        for j in range(i + 1, len(leads)):
            l2 = leads[j]
            id2 = str(l2["id"])

            if frozenset([id1, id2]) in whitelisted:
                continue

            c2 = clean_commercial_name(l2["name"] or "")
            if not c2 or len(c2) < 3:
                continue

            sim = fuzz.token_sort_ratio(c1, c2) / 100.0
            # Suspected range: 65% to 84%
            if 0.65 <= sim < 0.85:
                dist = None
                if (l1["latitude"] is not None and l1["longitude"] is not None and
                    l2["latitude"] is not None and l2["longitude"] is not None):
                    dist = haversine_distance_meters(
                        l1["latitude"], l1["longitude"],
                        l2["latitude"], l2["longitude"]
                    )
                
                # Check geographic or category relevance
                is_relevant = (
                    l1["category_slug"] == l2["category_slug"] or
                    (dist is not None and dist <= 1500) or
                    (l1.get("suburb") and l2.get("suburb") and l1["suburb"].lower() == l2["suburb"].lower())
                )

                if is_relevant:
                    pair_id = f"{id1}_{id2}"
                    pair_data = {
                        "pair_id": pair_id,
                        "similarity_score": round(sim, 2),
                        "similarity_pct": int(round(sim * 100)),
                        "distance_meters": round(dist, 1) if dist is not None else None,
                        "lead_a": l1,
                        "lead_b": l2,
                        "suggested_reason": f"Coincidencia lexica ({int(round(sim * 100))}%) en nombres comerciales"
                    }
                    suspected.append(pair_data)
                    lead_suspected_map.setdefault(id1, []).append(pair_id)
                    lead_suspected_map.setdefault(id2, []).append(pair_id)

    return {
        "total_pairs": len(suspected),
        "suspected_pairs": suspected,
        "lead_flags": lead_suspected_map
    }


@router.post("/resolve-suspected")
def resolve_suspected(payload: SuspectedResolveRequest):
    id_a = str(payload.lead_a_id)
    id_b = str(payload.lead_b_id)

    if payload.action == "whitelist":
        # Mark as distinct
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO deduplication_whitelist (lead_a_id, lead_b_id)
                    VALUES (%s, %s)
                    ON CONFLICT (lead_a_id, lead_b_id) DO NOTHING;
                    """,
                    (id_a, id_b)
                )
            conn.commit()
        return {"status": "SUCCESS", "message": "Los prospectos se marcaron como distintos permanentemente."}

    elif payload.action == "merge":
        # Keep master, merge duplicate
        master = str(payload.master_id) if payload.master_id else id_a
        duplicate = id_b if master == id_a else id_a

        merge_two_leads(master, duplicate, "COMBINACION_MANUAL_SOSPECHOSO", 0.75)
        return {"status": "SUCCESS", "message": "Prospectos combinados exitosamente."}

    raise HTTPException(status_code=400, detail="Accion no valida.")
