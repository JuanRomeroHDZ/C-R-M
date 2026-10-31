import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from src.db.connection import get_db_connection, execute_query
from src.analysis.pipeline import process_and_audit_lead
from src.pipeline.state_machine import (
    STAGES,
    VALID_STAGES,
    REGRET_REASONS,
    LOSS_REASONS,
    STAGNATION_THRESHOLD_HOURS,
    get_stagnation_info,
    transition_stage,
    check_duplicate,
    soft_delete_lead,
    restore_lead,
    purge_lead_permanent,
    reset_lead_history,
)
from src.analysis.opening_hours import evaluate_opening_hours
from src.analysis.pitch_generator import build_commercial_pitch

router = APIRouter(prefix="/api/v1", tags=["Pipeline & CRM"])


class StageTransitionRequest(BaseModel):
    stage: str
    notes: Optional[str] = None
    reactivation_date: Optional[str] = None
    regret_reason: Optional[str] = None
    regret_details: Optional[str] = None
    regret_amount: Optional[float] = None
    regret_service: Optional[str] = None
    loss_reason: Optional[str] = None


class LeadNoteRequest(BaseModel):
    content: str
    author: Optional[str] = "Usuario"


class DuplicateCheckRequest(BaseModel):
    name: Optional[str] = None
    phone_e164: Optional[str] = None
    normalized_domain: Optional[str] = None
    exclude_id: Optional[UUID] = None


class ManualLeadCreateRequest(BaseModel):
    name: str
    category_slug: str = "dentistas"
    primary_category: Optional[str] = None
    phone_raw: Optional[str] = None
    phone_e164: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    address_raw: Optional[str] = None
    city: str = "Tijuana"
    state: str = "Baja California"
    country: str = "Mexico"
    social_links: Optional[Dict[str, Any]] = None
    proposal_service: Optional[str] = None
    deal_value_estimated: Optional[float] = None
    proposal_currency: Optional[str] = "MXN"
    proposal_notes: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    name: Optional[str] = None
    category_slug: Optional[str] = None
    primary_category: Optional[str] = None
    phone_raw: Optional[str] = None
    phone_e164: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    address_raw: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = None
    proposal_service: Optional[str] = None
    deal_value_estimated: Optional[float] = None
    proposal_currency: Optional[str] = None
    proposal_notes: Optional[str] = None


@router.get("/pipeline/stages")
def list_pipeline_stages():
    return {
        "stages": STAGES,
        "regret_reasons": REGRET_REASONS,
        "loss_reasons": LOSS_REASONS,
        "stagnation_threshold_hours": STAGNATION_THRESHOLD_HOURS
    }


@router.get("/pipeline/board")
def get_pipeline_board(
    category_slug: Optional[str] = None,
    only_open_now: bool = False,
    tag: Optional[str] = None
):
    # Fetch all non-deleted leads
    conditions = ["is_deleted = FALSE"]
    params = []
    if category_slug:
        conditions.append("category_slug = %s")
        params.append(category_slug)

    if tag:
        conditions.append("tags @> %s::jsonb")
        import json
        params.append(json.dumps([tag.strip()]))

    where_clause = "WHERE " + " AND ".join(conditions)
    sql = f"""
    SELECT
        id, name, category_slug, primary_category, phone_e164, phone_raw, website,
        email, has_whatsapp, channels_status, lifecycle_stage, acceptance_probability_pct,
        technical_health_score, sales_arguments, address_raw, rating, review_count,
        opening_hours_raw, tags, deal_value_estimated, commercial_pitch,
        stage_entered_at, last_activity_at, postponed_until, postponed_note,
        regret_reason, loss_reason, social_links, proposal_service, proposal_currency,
        proposal_notes, created_at, updated_at
    FROM leads
    {where_clause}
    ORDER BY created_at DESC;
    """
    leads_rows = execute_query(sql, tuple(params))

    # Fetch settings for whatsapp url generation
    settings_rows = execute_query("SELECT value FROM system_settings WHERE key = 'whatsapp_template';")
    wa_template = settings_rows[0]["value"] if settings_rows else "Hola, buen día."

    # Group leads by stage
    board: Dict[str, Dict[str, Any]] = {}
    for st in STAGES:
        board[st["slug"]] = {
            "slug": st["slug"],
            "name": st["name"],
            "step": st["step"],
            "leads": [],
            "count": 0
        }

    total_matched = 0
    for row in leads_rows:
        is_open, open_label = evaluate_opening_hours(row.get("opening_hours_raw"))
        if only_open_now and not is_open:
            continue

        lead_stage = row["lifecycle_stage"]
        if lead_stage not in board:
            lead_stage = "EXTRACTED"

        stag_info = get_stagnation_info(row)

        # Formulate whatsapp url
        clean_phone = (row.get("phone_e164") or row.get("phone_raw") or "").replace("+", "").replace(" ", "").replace("-", "")
        wa_url = None
        if row.get("has_whatsapp") and clean_phone:
            msg = wa_template.replace("{nombre}", row["name"])
            import urllib.parse
            wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

        tags_val = row.get("tags") or []
        if isinstance(tags_val, str):
            import json
            try:
                tags_val = json.loads(tags_val)
            except Exception:
                tags_val = []

        card = {
            "id": str(row["id"]),
            "name": row["name"],
            "category_slug": row["category_slug"],
            "primary_category": row.get("primary_category"),
            "phone_e164": row.get("phone_e164"),
            "phone_raw": row.get("phone_raw"),
            "website": row.get("website"),
            "email": row.get("email"),
            "has_whatsapp": row.get("has_whatsapp", True),
            "channels_status": row.get("channels_status") or {},
            "lifecycle_stage": row["lifecycle_stage"],
            "acceptance_probability_pct": float(row["acceptance_probability_pct"]) if row.get("acceptance_probability_pct") is not None else 0.0,
            "technical_health_score": float(row["technical_health_score"]) if row.get("technical_health_score") is not None else 0.0,
            "sales_arguments": row.get("sales_arguments") or [],
            "address_raw": row.get("address_raw"),
            "rating": float(row["rating"]) if row.get("rating") is not None else None,
            "review_count": row.get("review_count", 0),
            "whatsapp_url": wa_url,
            "is_open_now": is_open,
            "open_status_label": open_label,
            "commercial_pitch": row.get("commercial_pitch") or build_commercial_pitch(row),
            "tags": tags_val if isinstance(tags_val, list) else [],
            "deal_value_estimated": float(row["deal_value_estimated"]) if row.get("deal_value_estimated") is not None else None,
            "proposal_service": row.get("proposal_service"),
            "proposal_currency": row.get("proposal_currency") or "MXN",
            "proposal_notes": row.get("proposal_notes"),
            "social_links": row.get("social_links") or {},
            "stage_entered_at": row.get("stage_entered_at"),
            "last_activity_at": row.get("last_activity_at"),
            "postponed_until": row.get("postponed_until"),
            "postponed_note": row.get("postponed_note"),
            "regret_reason": row.get("regret_reason"),
            "loss_reason": row.get("loss_reason"),
            "is_stagnant": stag_info["is_stagnant"],
            "stagnant_hours": stag_info["stagnant_hours"],
        }
        board[lead_stage]["leads"].append(card)
        board[lead_stage]["count"] += 1
        total_matched += 1

    return {
        "board": board,
        "total_leads": total_matched
    }


@router.post("/leads/{lead_id}/stage")
def change_lead_stage(lead_id: UUID, payload: StageTransitionRequest):
    result = transition_stage(
        lead_id=lead_id,
        to_stage=payload.stage,
        notes=payload.notes,
        reactivation_date=payload.reactivation_date,
        regret_reason=payload.regret_reason,
        regret_details=payload.regret_details,
        regret_amount=payload.regret_amount,
        regret_service=payload.regret_service,
        loss_reason=payload.loss_reason
    )
    return result


@router.get("/leads/{lead_id}/timeline")
def get_lead_timeline(lead_id: UUID):
    # Verify lead exists
    rows = execute_query("SELECT id, name, lifecycle_stage, created_at FROM leads WHERE id = %s;", (str(lead_id),))
    if not rows:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    lead = rows[0]

    # 1. Stage transitions
    stage_rows = execute_query(
        """
        SELECT id, from_stage, to_stage, duration_seconds, notes, reason, metadata, created_at
        FROM lead_stage_history
        WHERE lead_id = %s
        ORDER BY created_at DESC;
        """,
        (str(lead_id),)
    )

    # 2. Activity logs (interactions, wa clicks, calls, emails)
    act_rows = execute_query(
        """
        SELECT id, channel, action, metadata, created_at
        FROM lead_activity_log
        WHERE lead_id = %s
        ORDER BY created_at DESC;
        """,
        (str(lead_id),)
    )

    # 3. Custom notes
    notes_rows = execute_query(
        """
        SELECT id, content, author, created_at
        FROM lead_notes
        WHERE lead_id = %s
        ORDER BY created_at DESC;
        """,
        (str(lead_id),)
    )

    # Combine all items into chronological list
    timeline = []
    for s in stage_rows:
        timeline.append({
            "type": "STAGE_CHANGE",
            "id": str(s["id"]),
            "from_stage": s["from_stage"],
            "to_stage": s["to_stage"],
            "duration_seconds": s["duration_seconds"],
            "notes": s["notes"],
            "reason": s["reason"],
            "metadata": s["metadata"],
            "timestamp": s["created_at"]
        })

    for a in act_rows:
        # Avoid duplicate stage_transition if already recorded in stage history
        if a["channel"] == "PIPELINE" and a["action"] == "STAGE_TRANSITION":
            continue
        timeline.append({
            "type": "ACTIVITY",
            "id": str(a["id"]),
            "channel": a["channel"],
            "action": a["action"],
            "metadata": a["metadata"],
            "timestamp": a["created_at"]
        })

    for n in notes_rows:
        timeline.append({
            "type": "NOTE",
            "id": str(n["id"]),
            "content": n["content"],
            "author": n["author"],
            "timestamp": n["created_at"]
        })

    # Lead capture/creation event
    if lead.get("created_at"):
        timeline.append({
            "type": "ACTIVITY",
            "id": f"created-{lead['id']}",
            "channel": "SISTEMA",
            "action": "PROSPECTO_CREADO",
            "metadata": {"origen": "Extraccion / Registro inicial"},
            "timestamp": lead["created_at"]
        })

    # Sort descending by timestamp
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "lead_id": str(lead_id),
        "lead_name": lead["name"],
        "current_stage": lead["lifecycle_stage"],
        "timeline": timeline
    }


@router.post("/leads/{lead_id}/notes")
def add_lead_note(lead_id: UUID, payload: LeadNoteRequest):
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Contenido de la nota no puede estar vacio.")

    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM leads WHERE id = %s;", (str(lead_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

            cur.execute(
                """
                INSERT INTO lead_notes (lead_id, content, author, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (str(lead_id), payload.content.strip(), payload.author or "Usuario", now)
            )
            note_id = cur.fetchone()["id"]

            # Update last activity
            cur.execute(
                "UPDATE leads SET last_activity_at = %s, updated_at = %s WHERE id = %s;",
                (now, now, str(lead_id))
            )

    return {
        "id": str(note_id),
        "lead_id": str(lead_id),
        "content": payload.content.strip(),
        "author": payload.author or "Usuario",
        "created_at": now.isoformat()
    }


@router.get("/leads/{lead_id}/notes")
def list_lead_notes(lead_id: UUID):
    rows = execute_query(
        "SELECT id, content, author, created_at FROM lead_notes WHERE lead_id = %s ORDER BY created_at DESC;",
        (str(lead_id),)
    )
    return rows


@router.post("/leads/validate-duplicate")
def validate_duplicate(payload: DuplicateCheckRequest):
    conflict = check_duplicate(
        name=payload.name,
        phone_e164=payload.phone_e164,
        normalized_domain=payload.normalized_domain,
        exclude_id=payload.exclude_id
    )
    if conflict:
        return conflict
    return {"is_duplicate": False}


@router.post("/leads")
async def create_manual_lead(payload: ManualLeadCreateRequest):
    # Normalize phone
    phone_e164 = payload.phone_e164
    if not phone_e164 and payload.phone_raw:
        clean = payload.phone_raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean.startswith("+"):
            phone_e164 = clean
        elif len(clean) == 10:
            phone_e164 = f"+52{clean}"

    # Extract domain if website
    norm_domain = None
    if payload.website:
        import urllib.parse
        parsed = urllib.parse.urlparse(payload.website if "://" in payload.website else f"http://{payload.website}")
        norm_domain = parsed.netloc.lower().replace("www.", "")

    # Strict Duplicate check
    conflict = check_duplicate(
        name=payload.name,
        phone_e164=phone_e164,
        normalized_domain=norm_domain
    )
    if conflict:
        existing = conflict.get("existing_lead") or {}
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Colision detectada en {conflict.get('conflict_field', 'registro existente')}.",
                "conflict": conflict,
                "existing_lead_id": str(existing.get("id") or conflict.get("existing_id", "")),
                "existing_name": existing.get("name") or conflict.get("existing_name", ""),
                "existing_stage": existing.get("lifecycle_stage") or conflict.get("existing_stage", "")
            }
        )

    now = datetime.now(timezone.utc)
    ext_id = f"manual:{int(now.timestamp())}"
    social_json = json.dumps(payload.social_links or {})

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (
                    external_source, external_id, name, category_slug, primary_category,
                    phone_raw, phone_e164, phone_valid, website, normalized_domain,
                    email, address_raw, city, state, country, lifecycle_stage,
                    social_links, proposal_service, deal_value_estimated,
                    proposal_currency, proposal_notes,
                    stage_entered_at, last_activity_at, created_at, updated_at
                ) VALUES (
                    'manual', %s, %s, %s, %s,
                    %s, %s, TRUE, %s, %s,
                    %s, %s, %s, %s, %s, 'QUALIFIED',
                    %s::jsonb, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s
                ) RETURNING id;
                """,
                (
                    ext_id,
                    payload.name.strip(),
                    payload.category_slug,
                    payload.primary_category or payload.category_slug,
                    payload.phone_raw,
                    phone_e164,
                    payload.website,
                    norm_domain,
                    payload.email,
                    payload.address_raw,
                    payload.city,
                    payload.state,
                    payload.country,
                    social_json,
                    payload.proposal_service,
                    payload.deal_value_estimated,
                    payload.proposal_currency or "MXN",
                    payload.proposal_notes,
                    now,
                    now,
                    now,
                    now
                )
            )
            lead_id = cur.fetchone()["id"]

            if payload.notes:
                cur.execute(
                    "INSERT INTO lead_notes (lead_id, content, author, created_at) VALUES (%s, %s, 'Usuario', %s);",
                    (str(lead_id), payload.notes.strip(), now)
                )

            # Record initial history
            cur.execute(
                """
                INSERT INTO lead_stage_history (lead_id, from_stage, to_stage, duration_seconds, notes, created_at)
                VALUES (%s, NULL, 'QUALIFIED', 0, 'Contacto creado manualmente', %s);
                """,
                (str(lead_id), now)
            )

    # If website provided, enqueue or trigger technical web audit in background
    if payload.website:
        try:
            asyncio.create_task(process_and_audit_lead(str(lead_id)))
        except Exception:
            pass

    return {"id": str(lead_id), "status": "CREATED", "name": payload.name}


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: UUID, payload: LeadUpdateRequest):
    # Check lead exists
    rows = execute_query("SELECT id, name, phone_e164, normalized_domain FROM leads WHERE id = %s;", (str(lead_id),))
    if not rows:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    # Duplicate check on update
    norm_domain = None
    if payload.website:
        import urllib.parse
        parsed = urllib.parse.urlparse(payload.website if "://" in payload.website else f"http://{payload.website}")
        norm_domain = parsed.netloc.lower().replace("www.", "")

    # Normalize phone
    phone_e164 = payload.phone_e164
    if not phone_e164 and payload.phone_raw:
        clean = payload.phone_raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean.startswith("+"):
            phone_e164 = clean
        elif len(clean) == 10:
            phone_e164 = f"+52{clean}"

    conflict = check_duplicate(
        name=payload.name,
        phone_e164=phone_e164,
        normalized_domain=norm_domain,
        exclude_id=lead_id
    )
    if conflict:
        existing = conflict.get("existing_lead") or {}
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Colision detectada en {conflict.get('conflict_field')}.",
                "conflict": conflict,
                "existing_lead_id": str(existing.get("id") or conflict.get("existing_id", "")),
                "existing_name": existing.get("name") or conflict.get("existing_name", "")
            }
        )

    updates = []
    params = []
    if payload.name is not None:
        updates.append("name = %s")
        params.append(payload.name.strip())
    if payload.category_slug is not None:
        updates.append("category_slug = %s")
        params.append(payload.category_slug.strip())
    if payload.primary_category is not None:
        updates.append("primary_category = %s")
        params.append(payload.primary_category.strip())
    if payload.phone_raw is not None:
        updates.append("phone_raw = %s")
        params.append(payload.phone_raw.strip())
        if phone_e164:
            updates.append("phone_e164 = %s")
            params.append(phone_e164)
            updates.append("phone_valid = TRUE")
    elif phone_e164 is not None:
        updates.append("phone_e164 = %s")
        params.append(phone_e164)
        updates.append("phone_valid = TRUE")
    if payload.website is not None:
        updates.append("website = %s")
        params.append(payload.website.strip())
        updates.append("normalized_domain = %s")
        params.append(norm_domain)
    if payload.email is not None:
        updates.append("email = %s")
        params.append(payload.email.strip())
    if payload.address_raw is not None:
        updates.append("address_raw = %s")
        params.append(payload.address_raw.strip())
    if payload.social_links is not None:
        updates.append("social_links = %s::jsonb")
        params.append(json.dumps(payload.social_links))
    if payload.proposal_service is not None:
        updates.append("proposal_service = %s")
        params.append(payload.proposal_service.strip())
    if payload.deal_value_estimated is not None:
        updates.append("deal_value_estimated = %s")
        params.append(payload.deal_value_estimated)
    if payload.proposal_currency is not None:
        updates.append("proposal_currency = %s")
        params.append(payload.proposal_currency.strip())
    if payload.proposal_notes is not None:
        updates.append("proposal_notes = %s")
        params.append(payload.proposal_notes.strip())

    if not updates:
        return {"status": "NO_CHANGES", "id": str(lead_id)}

    modified_fields = [u.split(' =')[0] for u in updates]
    updates.append("updated_at = NOW()")
    params.append(str(lead_id))

    sql = f"UPDATE leads SET {', '.join(updates)} WHERE id = %s RETURNING id, name, category_slug, phone_raw, phone_e164, website, email, address_raw;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                VALUES (%s, 'sistema', 'EDICION', %s::jsonb);
                """,
                (str(lead_id), json.dumps({"campos": modified_fields}))
            )
        conn.commit()

    return {"status": "UPDATED", "id": str(lead_id), "lead": row}


@router.delete("/leads/{lead_id}")
def soft_delete_lead_endpoint(lead_id: UUID, reason: str = Query(default="Descarte manual de usuario")):
    return soft_delete_lead(lead_id, reason=reason)


@router.post("/leads/{lead_id}/restore")
def restore_lead_endpoint(lead_id: UUID):
    return restore_lead(lead_id)


@router.delete("/leads/{lead_id}/purge")
def purge_lead_endpoint(lead_id: UUID):
    return purge_lead_permanent(lead_id)


@router.post("/leads/{lead_id}/reset-history")
def reset_lead_history_endpoint(lead_id: UUID):
    return reset_lead_history(lead_id)


@router.get("/leads/trash/list")
def list_trash_leads():
    rows = execute_query(
        """
        SELECT id, name, category_slug, primary_category, phone_e164, phone_raw,
               website, deleted_at, deleted_reason, lifecycle_stage
        FROM leads
        WHERE is_deleted = TRUE
        ORDER BY deleted_at DESC;
        """
    )
    return rows
