from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from src.db.connection import execute_query
from src.models.schemas import LeadOut

router = APIRouter(prefix="/api/v1/leads", tags=["Leads"])


def _hydrate_lead(row: dict) -> LeadOut:
    return LeadOut(
        id=row["id"],
        external_source=row["external_source"],
        external_id=row["external_id"],
        name=row["name"],
        category_slug=row["category_slug"],
        primary_category=row.get("primary_category"),
        subcategories=row.get("subcategories") or [],
        phone_raw=row.get("phone_raw"),
        phone_normalized=row.get("phone_normalized"),
        website=row.get("website"),
        address_raw=row.get("address_raw"),
        street=row.get("street"),
        house_number=row.get("house_number"),
        suburb=row.get("suburb"),
        postal_code=row.get("postal_code"),
        city=row["city"],
        state=row["state"],
        country=row["country"],
        latitude=row.get("latitude"),
        longitude=row.get("longitude"),
        rating=float(row["rating"]) if row.get("rating") is not None else None,
        review_count=row.get("review_count", 0),
        opening_hours_raw=row.get("opening_hours_raw"),
        is_claimed=row.get("is_claimed"),
        lifecycle_stage=row["lifecycle_stage"],
        extra_metadata=row.get("extra_metadata") or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_seen_at=row["last_seen_at"],
        is_deleted=row["is_deleted"]
    )


@router.get("", response_model=List[LeadOut])
def list_leads(
    category_slug: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    conditions = []
    params = []

    if not include_deleted:
        conditions.append("is_deleted = FALSE")

    if category_slug:
        conditions.append("category_slug = %s")
        params.append(category_slug)

    if source:
        conditions.append("external_source = %s")
        params.append(source)

    if search:
        conditions.append("(name ILIKE %s OR address_raw ILIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
    SELECT * FROM leads
    {where_clause}
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s;
    """
    params.extend([limit, offset])

    rows = execute_query(sql, tuple(params))
    return [_hydrate_lead(r) for r in rows]


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: UUID):
    rows = execute_query("SELECT * FROM leads WHERE id = %s;", (str(lead_id),))
    if not rows:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return _hydrate_lead(rows[0])
