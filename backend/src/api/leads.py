import asyncio
import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Response, Body
from pydantic import BaseModel
from src.db.connection import get_db_connection, execute_query
from src.models.schemas import (
    LeadOut, LeadTagsUpdate, LeadEstimateRequest, LeadPitchUpdate,
    BatchStageRequest, BatchTagsRequest, BatchTrashRequest, BatchExportRequest
)
from src.pipeline.state_machine import get_stagnation_info, check_duplicate
from src.analysis.opening_hours import evaluate_opening_hours
from src.analysis.pitch_generator import build_commercial_pitch
from src.analysis.pipeline import process_and_audit_lead

router = APIRouter(prefix="/api/v1/leads", tags=["Leads"])


class QuickNotePayload(BaseModel):
    content: str
    author: Optional[str] = "Usuario"


def _hydrate_lead(row: dict) -> LeadOut:
    is_open, open_label = evaluate_opening_hours(row.get("opening_hours_raw"))
    pitch = row.get("commercial_pitch") or build_commercial_pitch(row)
    tags_list = row.get("tags") or []
    if isinstance(tags_list, str):
        try:
            tags_list = json.loads(tags_list)
        except Exception:
            tags_list = []

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
        phone_e164=row.get("phone_e164"),
        phone_country=row.get("phone_country"),
        phone_valid=row.get("phone_valid"),
        website=row.get("website"),
        normalized_domain=row.get("normalized_domain"),
        has_dedicated_website=row.get("has_dedicated_website"),
        social_links=row.get("social_links") or {},
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
        email=row.get("email"),
        has_whatsapp=row.get("has_whatsapp", True) if row.get("has_whatsapp") is not None else True,
        channels_status=row.get("channels_status") or {},
        first_contact_at=row.get("first_contact_at"),
        lifecycle_stage=row["lifecycle_stage"],
        extra_metadata=row.get("extra_metadata") or {},
        technical_health_score=float(row["technical_health_score"]) if row.get("technical_health_score") is not None else None,
        acceptance_probability_pct=float(row["acceptance_probability_pct"]) if row.get("acceptance_probability_pct") is not None else None,
        sales_arguments=row.get("sales_arguments") or [],
        audited_at=row.get("audited_at"),
        qualified_at=row.get("qualified_at"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_seen_at=row["last_seen_at"],
        is_deleted=row["is_deleted"],
        deleted_at=row.get("deleted_at"),
        deleted_reason=row.get("deleted_reason"),
        stage_entered_at=row.get("stage_entered_at"),
        last_activity_at=row.get("last_activity_at"),
        postponed_until=row.get("postponed_until"),
        postponed_note=row.get("postponed_note"),
        regret_reason=row.get("regret_reason"),
        regret_details=row.get("regret_details"),
        regret_amount=float(row["regret_amount"]) if row.get("regret_amount") is not None else None,
        regret_service=row.get("regret_service"),
        loss_reason=row.get("loss_reason"),
        is_stagnant=get_stagnation_info(row)["is_stagnant"],
        stagnant_hours=get_stagnation_info(row)["stagnant_hours"],
        tags=tags_list if isinstance(tags_list, list) else [],
        deal_value_estimated=float(row["deal_value_estimated"]) if row.get("deal_value_estimated") is not None else None,
        proposal_service=row.get("proposal_service"),
        proposal_currency=row.get("proposal_currency") or "MXN",
        proposal_notes=row.get("proposal_notes"),
        commercial_pitch=pitch,
        is_open_now=is_open,
        open_status_label=open_label
    )


@router.get("/search/global", response_model=List[LeadOut])
def global_search(q: str = Query(..., min_length=1), limit: int = 15):
    pattern = f"%{q.strip()}%"
    sql = """
    SELECT l.*
    FROM leads l
    WHERE l.is_deleted = FALSE AND (
        l.name ILIKE %s OR
        l.phone_raw ILIKE %s OR
        l.phone_e164 ILIKE %s OR
        l.street ILIKE %s OR
        l.suburb ILIKE %s OR
        l.address_raw ILIKE %s OR
        l.primary_category ILIKE %s OR
        l.tags::text ILIKE %s OR
        EXISTS (
            SELECT 1 FROM lead_notes ln
            WHERE ln.lead_id = l.id AND ln.content ILIKE %s
        )
    )
    ORDER BY l.acceptance_probability_pct DESC NULLS LAST
    LIMIT %s;
    """
    rows = execute_query(sql, (pattern, pattern, pattern, pattern, pattern, pattern, pattern, pattern, pattern, limit))
    return [_hydrate_lead(r) for r in rows]


@router.get("", response_model=List[LeadOut])
def list_leads(
    category_slug: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    only_open_now: bool = False,
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

    if tag:
        conditions.append("tags @> %s::jsonb")
        params.append(json.dumps([tag.strip()]))

    if search:
        conditions.append("(name ILIKE %s OR address_raw ILIKE %s OR phone_raw ILIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
    SELECT * FROM leads
    {where_clause}
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s;
    """
    params.extend([limit, offset])

    rows = execute_query(sql, tuple(params))
    hydrated = [_hydrate_lead(r) for r in rows]
    if only_open_now:
        hydrated = [h for h in hydrated if h.is_open_now]
    return hydrated


# ============================================================================
# FASE 10: BANDEJA "PARA HOY", IMPORTADOR Y EXPORTADOR INTEGRAL
# ============================================================================

@router.get("/today/tray")
def get_today_action_tray():
    # 1. Calendar events today
    cal_rows = execute_query(
        """
        SELECT DISTINCT l.*
        FROM calendar_events ce
        JOIN leads l ON ce.lead_id = l.id
        WHERE ce.start_time::date = CURRENT_DATE AND l.is_deleted = FALSE;
        """
    )

    # 2. Postponed due leads (<= NOW)
    post_rows = execute_query(
        """
        SELECT l.*
        FROM leads l
        WHERE l.lifecycle_stage = 'POSTPONED'
          AND l.postponed_until IS NOT NULL
          AND l.postponed_until <= NOW()
          AND l.is_deleted = FALSE
        ORDER BY l.postponed_until ASC;
        """
    )

    # 3. Stagnant leads (>48 hours in active pipeline stages)
    stag_rows = execute_query(
        """
        SELECT l.*
        FROM leads l
        WHERE l.is_deleted = FALSE
          AND l.lifecycle_stage NOT IN ('EXTRACTED', 'CLOSED_WON', 'CLOSED_LOST', 'REGRETTED')
          AND (
              (l.last_activity_at IS NOT NULL AND l.last_activity_at < NOW() - INTERVAL '48 hours')
              OR
              (l.last_activity_at IS NULL AND l.stage_entered_at < NOW() - INTERVAL '48 hours')
          )
        ORDER BY l.last_activity_at ASC NULLS FIRST;
        """
    )

    cal_leads = [_hydrate_lead(r) for r in cal_rows]
    post_leads = [_hydrate_lead(r) for r in post_rows]
    stag_leads = [_hydrate_lead(r) for r in stag_rows]

    # Combine items preserving unique leads
    seen_ids = set()
    combined_items = []
    for l in cal_leads:
        if str(l.id) not in seen_ids:
            seen_ids.add(str(l.id))
            combined_items.append(l)

    for l in post_leads:
        if str(l.id) not in seen_ids:
            seen_ids.add(str(l.id))
            combined_items.append(l)

    for l in stag_leads:
        if str(l.id) not in seen_ids:
            seen_ids.add(str(l.id))
            combined_items.append(l)

    return {
        "total_count": len(combined_items),
        "calendar_count": len(cal_leads),
        "postponed_count": len(post_leads),
        "stagnant_count": len(stag_leads),
        "calendar_leads": cal_leads,
        "postponed_leads": post_leads,
        "stagnant_leads": stag_leads,
        "items": combined_items
    }


class LeadImportItem(BaseModel):
    name: str
    category_slug: Optional[str] = "dentistas"
    primary_category: Optional[str] = None
    phone_raw: Optional[str] = None
    phone_e164: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    address_raw: Optional[str] = None
    city: Optional[str] = "Tijuana"
    notes: Optional[str] = None


class BatchImportPayload(BaseModel):
    leads: List[LeadImportItem]


@router.post("/import")
async def import_leads_batch(payload: BatchImportPayload):
    imported = 0
    duplicates_skipped = 0
    errors = 0
    audit_tasks = []

    now = datetime.now(timezone.utc)
    for idx, item in enumerate(payload.leads):
        if not item.name or not item.name.strip():
            errors += 1
            continue

        clean_name = item.name.strip()

        # Phone normalization
        phone_e164 = item.phone_e164
        if not phone_e164 and item.phone_raw:
            clean_p = item.phone_raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if clean_p.startswith("+"):
                phone_e164 = clean_p
            elif len(clean_p) == 10:
                phone_e164 = f"+52{clean_p}"

        # Domain normalization
        norm_domain = None
        if item.website:
            import urllib.parse
            parsed = urllib.parse.urlparse(item.website if "://" in item.website else f"http://{item.website}")
            norm_domain = parsed.netloc.lower().replace("www.", "")

        # Duplicate check
        conflict = check_duplicate(
            name=clean_name,
            phone_e164=phone_e164,
            normalized_domain=norm_domain
        )
        if conflict:
            duplicates_skipped += 1
            continue

        ext_id = f"import:{int(now.timestamp())}:{idx}"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO leads (
                            external_source, external_id, name, category_slug, primary_category,
                            phone_raw, phone_e164, phone_valid, website, normalized_domain,
                            email, address_raw, city, state, country, lifecycle_stage,
                            stage_entered_at, last_activity_at, created_at, updated_at
                        ) VALUES (
                            'import', %s, %s, %s, %s,
                            %s, %s, TRUE, %s, %s,
                            %s, %s, %s, 'Baja California', 'Mexico', 'QUALIFIED',
                            %s, %s, %s, %s
                        ) RETURNING id;
                        """,
                        (
                            ext_id,
                            clean_name,
                            item.category_slug or "dentistas",
                            item.primary_category or item.category_slug or "dentistas",
                            item.phone_raw,
                            phone_e164,
                            item.website,
                            norm_domain,
                            item.email,
                            item.address_raw,
                            item.city or "Tijuana",
                            now,
                            now,
                            now,
                            now
                        )
                    )
                    new_id = cur.fetchone()["id"]

                    if item.notes:
                        cur.execute(
                            "INSERT INTO lead_notes (lead_id, content, author, created_at) VALUES (%s, %s, 'Importador', %s);",
                            (str(new_id), item.notes.strip(), now)
                        )

                    cur.execute(
                        """
                        INSERT INTO lead_stage_history (lead_id, from_stage, to_stage, duration_seconds, notes, created_at)
                        VALUES (%s, NULL, 'QUALIFIED', 0, 'Prospecto importado en lote', %s);
                        """,
                        (str(new_id), now)
                    )

            imported += 1
            if item.website:
                audit_tasks.append(str(new_id))
        except Exception:
            errors += 1

    # Enqueue background audits
    for lid in audit_tasks:
        try:
            asyncio.create_task(process_and_audit_lead(lid))
        except Exception:
            pass

    return {
        "status": "COMPLETED",
        "total_processed": len(payload.leads),
        "imported": imported,
        "duplicates_skipped": duplicates_skipped,
        "errors": errors,
        "audits_enqueued": len(audit_tasks)
    }


@router.get("/export")
def export_leads_dataset(
    format: str = Query("csv", pattern="^(csv|json)$"),
    category_slug: Optional[str] = None,
    lifecycle_stage: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    conditions = ["is_deleted = FALSE"]
    params = []

    if category_slug:
        conditions.append("category_slug = %s")
        params.append(category_slug)

    if lifecycle_stage:
        conditions.append("lifecycle_stage = %s")
        params.append(lifecycle_stage)

    if tag:
        conditions.append("tags @> %s::jsonb")
        params.append(json.dumps([tag.strip()]))

    if search:
        conditions.append("(name ILIKE %s OR phone_raw ILIKE %s OR address_raw ILIKE %s)")
        p = f"%{search.strip()}%"
        params.extend([p, p, p])

    where_clause = "WHERE " + " AND ".join(conditions)
    sql = f"""
    SELECT id, name, category_slug, primary_category, phone_raw, phone_e164, website,
           email, address_raw, city, rating, review_count, technical_health_score,
           acceptance_probability_pct, lifecycle_stage, deal_value_estimated,
           proposal_service, proposal_currency, proposal_notes, tags, created_at, updated_at
    FROM leads
    {where_clause}
    ORDER BY created_at DESC;
    """
    rows = execute_query(sql, tuple(params))

    if format == "json":
        json_str = json.dumps(rows, default=str, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=prospectos_crm.json"}
        )

    # Format CSV
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "ID", "Nombre Comercial", "Categoria", "Giro Primario", "Telefono", "Telefono E164",
        "Sitio Web", "Correo", "Direccion", "Ciudad", "Calificacion", "Resenas",
        "Salud Tecnica Web", "Probabilidad Aceptacion (%)", "Fase Comercial",
        "Valor Estimado", "Servicio Propuesto", "Moneda", "Notas Propuesta",
        "Etiquetas", "Fecha Creacion"
    ])

    for r in rows:
        tags_str = ", ".join(r["tags"]) if isinstance(r.get("tags"), list) else ""
        writer.writerow([
            r["id"],
            r["name"],
            r["category_slug"],
            r.get("primary_category") or "",
            r.get("phone_raw") or "",
            r.get("phone_e164") or "",
            r.get("website") or "",
            r.get("email") or "",
            r.get("address_raw") or "",
            r.get("city") or "",
            r.get("rating") or "",
            r.get("review_count") or 0,
            r.get("technical_health_score") or "",
            r.get("acceptance_probability_pct") or "",
            r.get("lifecycle_stage") or "",
            r.get("deal_value_estimated") or "",
            r.get("proposal_service") or "",
            r.get("proposal_currency") or "MXN",
            r.get("proposal_notes") or "",
            tags_str,
            str(r.get("created_at") or "")
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=prospectos_crm.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: UUID):
    rows = execute_query("SELECT * FROM leads WHERE id = %s;", (str(lead_id),))
    if not rows:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    return _hydrate_lead(rows[0])


@router.post("/{lead_id}/tags")
def update_lead_tags(lead_id: UUID, payload: LeadTagsUpdate):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET tags = %s::jsonb, updated_at = NOW()
                WHERE id = %s AND is_deleted = FALSE
                RETURNING id;
                """,
                (json.dumps(payload.tags), str(lead_id))
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
            # Log activity
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                VALUES (%s, 'tags', 'Etiquetas actualizadas', %s::jsonb);
                """,
                (str(lead_id), json.dumps({"tags": payload.tags}))
            )
        conn.commit()
    return {"status": "SUCCESS", "tags": payload.tags}


@router.get("/{lead_id}/pitch")
def get_commercial_pitch(lead_id: UUID):
    rows = execute_query("SELECT * FROM leads WHERE id = %s;", (str(lead_id),))
    if not rows:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    lead = rows[0]
    audit_rows = execute_query("SELECT * FROM lead_web_audits WHERE lead_id = %s ORDER BY created_at DESC LIMIT 1;", (str(lead_id),))
    audit = audit_rows[0] if audit_rows else None
    pitch = build_commercial_pitch(lead, audit)
    return {"lead_id": str(lead_id), "name": lead["name"], "pitch": pitch}


@router.post("/{lead_id}/pitch")
def save_commercial_pitch(lead_id: UUID, payload: LeadPitchUpdate):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE leads SET commercial_pitch = %s, updated_at = NOW() WHERE id = %s RETURNING id;",
                (payload.pitch.strip(), str(lead_id))
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
        conn.commit()
    return {"status": "SUCCESS", "pitch": payload.pitch}


@router.get("/{lead_id}/competitors")
def get_lead_competitors(lead_id: UUID):
    lead_rows = execute_query("SELECT * FROM leads WHERE id = %s;", (str(lead_id),))
    if not lead_rows:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    lead = lead_rows[0]
    cat = lead["category_slug"]
    suburb = lead.get("suburb") or ""

    conditions = ["category_slug = %s", "id != %s", "is_deleted = FALSE"]
    params = [cat, str(lead_id)]
    if suburb:
        conditions.append("(suburb ILIKE %s OR address_raw ILIKE %s)")
        params.extend([f"%{suburb}%", f"%{suburb}%"])

    sql = f"""
    SELECT id, name, phone_raw, phone_e164, website, has_dedicated_website,
           rating, review_count, technical_health_score, acceptance_probability_pct,
           lifecycle_stage
    FROM leads
    WHERE {' AND '.join(conditions)}
    ORDER BY rating DESC NULLS LAST, review_count DESC NULLS LAST
    LIMIT 5;
    """
    comp_rows = execute_query(sql, tuple(params))
    if len(comp_rows) < 3:
        sql_fallback = """
        SELECT id, name, phone_raw, phone_e164, website, has_dedicated_website,
               rating, review_count, technical_health_score, acceptance_probability_pct,
               lifecycle_stage
        FROM leads
        WHERE category_slug = %s AND id != %s AND is_deleted = FALSE
        ORDER BY rating DESC NULLS LAST, review_count DESC NULLS LAST
        LIMIT 5;
        """
        comp_rows = execute_query(sql_fallback, (cat, str(lead_id)))

    total_area = len(comp_rows)
    with_site = sum(1 for c in comp_rows if c.get("has_dedicated_website"))
    pct_with_site = round((with_site / total_area * 100)) if total_area > 0 else 0

    lead_has_site = bool(lead.get("has_dedicated_website"))
    if not lead_has_site and pct_with_site >= 50:
        advantage_arg = f"En esta zona, el {pct_with_site}% de negocios similares ya cuenta con pagina web propia. Este negocio se encuentra en desventaja directa."
    elif lead_has_site and (lead.get("technical_health_score") or 0) < 50:
        advantage_arg = "Sus competidores mas cercanos tienen paginas web mas modernas y adaptadas a celulares, lo que les resta citas semanales."
    else:
        advantage_arg = f"Cuenta con {total_area} competidores directos en la zona; renovar su presencia digital le permitira destacar con citas directas a WhatsApp."

    return {
        "lead_id": str(lead_id),
        "lead_name": lead["name"],
        "category": cat,
        "area": suburb or "Tijuana",
        "total_competitors_found": total_area,
        "competitors_with_website_pct": pct_with_site,
        "commercial_leverage_argument": advantage_arg,
        "competitors": [
            {
                "id": str(c["id"]),
                "name": c["name"],
                "has_website": bool(c.get("has_dedicated_website")),
                "rating": float(c["rating"]) if c.get("rating") else None,
                "reviews": c.get("review_count", 0),
                "score": round(float(c["acceptance_probability_pct"] or 0))
            }
            for c in comp_rows
        ]
    }


@router.post("/{lead_id}/estimate")
def calculate_lead_estimate(lead_id: UUID, payload: LeadEstimateRequest):
    PRICE_CATALOG = {
        "web_responsive": {"name": "Pagina adaptada a celulares", "price": 4500.0},
        "security_ssl": {"name": "Seguridad y candado de confianza", "price": 1500.0},
        "speed_optimization": {"name": "Optimizacion de velocidad de carga", "price": 2000.0},
        "local_seo": {"name": "Posicionamiento local en mapas", "price": 2500.0},
        "tracking_analytics": {"name": "Rastreo de visitas y anuncios", "price": 1800.0},
        "whatsapp_direct": {"name": "Canal de captacion directa a WhatsApp", "price": 1200.0}
    }
    total = 0.0
    items = []
    for s in payload.services:
        if s in PRICE_CATALOG:
            items.append(PRICE_CATALOG[s]["name"])
            total += PRICE_CATALOG[s]["price"]

    if payload.custom_amount is not None:
        total = float(payload.custom_amount)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET deal_value_estimated = %s, updated_at = NOW()
                WHERE id = %s AND is_deleted = FALSE
                RETURNING id;
                """,
                (total, str(lead_id))
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
            # Log in activity log
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                VALUES (%s, 'estimate', 'Propuesta estimada calculada', %s::jsonb);
                """,
                (str(lead_id), json.dumps({"services": items, "total_mxn": total, "notes": payload.notes}))
            )
        conn.commit()

    return {
        "status": "SUCCESS",
        "lead_id": str(lead_id),
        "total_estimated_mxn": total,
        "services_included": items,
        "summary_text": f"Propuesta estimada: ${total:,.2f} MXN por " + (", ".join(items) if items else "servicios comerciales personalizados")
    }


@router.post("/batch/stage")
def batch_update_stage(payload: BatchStageRequest):
    if not payload.lead_ids:
        return {"status": "SUCCESS", "updated_count": 0}
    ids_str = [str(lid) for lid in payload.lead_ids]
    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, lifecycle_stage FROM leads WHERE id = ANY(%s) AND is_deleted = FALSE;", (ids_str,))
            rows = cur.fetchall()
            for r in rows:
                old_stage = r["lifecycle_stage"]
                cur.execute(
                    """
                    INSERT INTO lead_stage_history (lead_id, from_stage, to_stage, reason, created_at)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (r["id"], old_stage, payload.stage, payload.reason or "Cambio en lote", now)
                )
                cur.execute(
                    """
                    INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                    VALUES (%s, 'stage_change', 'Fase comercial actualizada en lote', %s::jsonb);
                    """,
                    (r["id"], json.dumps({"from": old_stage, "to": payload.stage, "reason": payload.reason}))
                )
            cur.execute(
                """
                UPDATE leads
                SET lifecycle_stage = %s, stage_entered_at = %s, last_activity_at = %s, updated_at = %s
                WHERE id = ANY(%s) AND is_deleted = FALSE;
                """,
                (payload.stage, now, now, now, ids_str)
            )
            count = cur.rowcount
        conn.commit()
    return {"status": "SUCCESS", "updated_count": count}


@router.post("/batch/tags")
def batch_update_tags(payload: BatchTagsRequest):
    if not payload.lead_ids:
        return {"status": "SUCCESS", "updated_count": 0}
    ids_str = [str(lid) for lid in payload.lead_ids]
    tag_clean = payload.tag.strip()
    if not tag_clean:
        raise HTTPException(status_code=400, detail="Etiqueta no puede estar vacia.")
    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tags FROM leads WHERE id = ANY(%s) AND is_deleted = FALSE;", (ids_str,))
            rows = cur.fetchall()
            count = 0
            for r in rows:
                raw_tags = r["tags"] or []
                if isinstance(raw_tags, str):
                    try:
                        raw_tags = json.loads(raw_tags)
                    except Exception:
                        raw_tags = []
                cur_tags = list(raw_tags)
                if payload.action == "add":
                    if tag_clean not in cur_tags:
                        cur_tags.append(tag_clean)
                elif payload.action == "remove":
                    cur_tags = [t for t in cur_tags if t != tag_clean]
                cur.execute(
                    "UPDATE leads SET tags = %s::jsonb, updated_at = %s WHERE id = %s;",
                    (json.dumps(cur_tags), now, r["id"])
                )
                cur.execute(
                    """
                    INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                    VALUES (%s, 'tags', 'Etiqueta modificada en lote', %s::jsonb);
                    """,
                    (r["id"], json.dumps({"action": payload.action, "tag": tag_clean}))
                )
                count += 1
        conn.commit()
    return {"status": "SUCCESS", "updated_count": count}


@router.post("/batch/trash")
def batch_trash_leads(payload: BatchTrashRequest):
    if not payload.lead_ids:
        return {"status": "SUCCESS", "deleted_count": 0}
    ids_str = [str(lid) for lid in payload.lead_ids]
    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET is_deleted = TRUE, deleted_at = %s, deleted_reason = %s, updated_at = %s
                WHERE id = ANY(%s) AND is_deleted = FALSE;
                """,
                (now, payload.reason or "Descarte masivo en lote", now, ids_str)
            )
            count = cur.rowcount
            for lid in ids_str:
                cur.execute(
                    """
                    INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                    VALUES (%s, 'trash', 'Descartado a papelera en lote', %s::jsonb);
                    """,
                    (lid, json.dumps({"reason": payload.reason}))
                )
        conn.commit()
    return {"status": "SUCCESS", "deleted_count": count}


@router.post("/batch/export")
def batch_export_leads(payload: BatchExportRequest):
    if not payload.lead_ids:
        raise HTTPException(status_code=400, detail="Seleccione al menos un prospecto para exportar.")
    ids_str = [str(lid) for lid in payload.lead_ids]
    rows = execute_query(
        """
        SELECT id, name, category_slug, phone_raw, phone_e164, website, address_raw,
               suburb, city, rating, review_count, acceptance_probability_pct,
               lifecycle_stage, deal_value_estimated, tags, created_at
        FROM leads
        WHERE id = ANY(%s)
        ORDER BY created_at DESC;
        """,
        (ids_str,)
    )
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "ID", "Nombre Comercial", "Categoria", "Telefono", "Telefono E164", "Sitio Web",
        "Direccion", "Colonia", "Ciudad", "Calificacion", "Resenas", "Probabilidad Aceptacion (%)",
        "Fase Comercial", "Valor Estimado (MXN)", "Etiquetas", "Fecha Captura"
    ])
    for r in rows:
        tags_str = ", ".join(r["tags"]) if isinstance(r.get("tags"), list) else ""
        writer.writerow([
            r["id"],
            r["name"],
            r["category_slug"],
            r.get("phone_raw") or "",
            r.get("phone_e164") or "",
            r.get("website") or "",
            r.get("address_raw") or "",
            r.get("suburb") or "",
            r.get("city") or "",
            r.get("rating") or "",
            r.get("review_count") or 0,
            r.get("acceptance_probability_pct") or "",
            r.get("lifecycle_stage") or "",
            r.get("deal_value_estimated") or "",
            tags_str,
            str(r.get("created_at") or "")
        ])
    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=prospectos_exportados.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.post("/{lead_id}/notes")
def add_lead_note(lead_id: UUID, payload: QuickNotePayload):
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
            cur.execute(
                "UPDATE leads SET last_activity_at = %s, updated_at = %s WHERE id = %s;",
                (now, now, str(lead_id))
            )
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                VALUES (%s, 'notes', 'Nota guardada', %s::jsonb);
                """,
                (str(lead_id), json.dumps({"note_id": str(note_id)}))
            )
        conn.commit()
    return {
        "id": str(note_id),
        "lead_id": str(lead_id),
        "content": payload.content.strip(),
        "author": payload.author or "Usuario",
        "created_at": now.isoformat()
    }


@router.get("/{lead_id}/notes")
def list_lead_notes(lead_id: UUID):
    rows = execute_query(
        "SELECT id, content, author, created_at FROM lead_notes WHERE lead_id = %s ORDER BY created_at DESC;",
        (str(lead_id),)
    )
    return rows

