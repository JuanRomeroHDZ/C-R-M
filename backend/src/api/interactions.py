import json
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from src.analysis.channel_enricher import (
    compute_channel_statuses,
    generate_whatsapp_url,
    enrich_lead_channels
)
from src.db.connection import get_db_connection, execute_query

logger = logging.getLogger("crm.api.interactions")
router = APIRouter(prefix="/api/v1/leads", tags=["Interactions"])


class InteractionPayload(BaseModel):
    channel: str
    action: str = "click"
    metadata: Optional[Dict[str, Any]] = None


@router.get("/{lead_id}/contact-card")
def get_lead_contact_card(lead_id: UUID):
    lead_str = str(lead_id)
    rows = execute_query(
        """
        SELECT id, name, category_slug, phone_raw, phone_e164, has_whatsapp,
               website, normalized_domain, has_dedicated_website, social_links, email,
               rating, review_count, technical_health_score, acceptance_probability_pct,
               sales_arguments, lifecycle_stage, first_contact_at
        FROM leads
        WHERE id = %s AND is_deleted = FALSE;
        """,
        (lead_str,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Lead not found.")

    lead = rows[0]

    # Get WhatsApp template from settings
    setting_rows = execute_query("SELECT value FROM system_settings WHERE key = 'whatsapp_template';")
    wa_template = setting_rows[0]["value"] if setting_rows else "Hola, buen día."

    # Compute channels status
    channels = compute_channel_statuses(lead)
    whatsapp_url = None
    if channels.get("whatsapp") == "DISPONIBLE":
        whatsapp_url = generate_whatsapp_url(lead.get("phone_e164"), wa_template, lead.get("name", ""))

    social_links = lead.get("social_links") or {}
    if isinstance(social_links, str):
        try:
            social_links = json.loads(social_links)
        except Exception:
            social_links = {}

    return {
        "id": lead["id"],
        "name": lead["name"],
        "category_slug": lead["category_slug"],
        "phone_e164": lead["phone_e164"],
        "phone_raw": lead["phone_raw"],
        "has_whatsapp": lead["has_whatsapp"],
        "website": lead["website"],
        "email": lead.get("email"),
        "channels_status": channels,
        "whatsapp_url": whatsapp_url,
        "tel_url": f"tel:{lead['phone_e164']}" if lead.get("phone_e164") else None,
        "mailto_url": f"mailto:{lead['email']}" if lead.get("email") else None,
        "social_links": social_links,
        "rating": float(lead["rating"]) if lead.get("rating") is not None else None,
        "review_count": lead["review_count"],
        "technical_health_score": float(lead["technical_health_score"]) if lead.get("technical_health_score") is not None else 0.0,
        "acceptance_probability_pct": float(lead["acceptance_probability_pct"]) if lead.get("acceptance_probability_pct") is not None else 0.0,
        "sales_arguments": lead.get("sales_arguments") or [],
        "lifecycle_stage": lead["lifecycle_stage"],
        "first_contact_at": lead.get("first_contact_at")
    }


@router.post("/{lead_id}/interact")
def record_interaction(lead_id: UUID, payload: InteractionPayload):
    lead_str = str(lead_id)
    rows = execute_query("SELECT id, lifecycle_stage, name FROM leads WHERE id = %s AND is_deleted = FALSE;", (lead_str,))
    if not rows:
        raise HTTPException(status_code=404, detail="Lead not found.")

    lead = rows[0]
    current_stage = lead["lifecycle_stage"]
    stage_changed = False
    new_stage = current_stage

    # Automatic stage progression: QUALIFIED -> FIRST_CONTACT on first interaction
    if current_stage == "QUALIFIED" and payload.action in ("click", "call", "whatsapp", "email"):
        new_stage = "FIRST_CONTACT"
        stage_changed = True

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Log activity
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                VALUES (%s, %s, %s, %s);
                """,
                (lead_str, payload.channel, payload.action, json.dumps(payload.metadata or {}))
            )

            # 2. Advance stage if applicable
            if stage_changed:
                cur.execute(
                    """
                    UPDATE leads
                    SET lifecycle_stage = 'FIRST_CONTACT',
                        first_contact_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (lead_str,)
                )

    return {
        "status": "RECORDED",
        "lead_id": lead_str,
        "channel": payload.channel,
        "action": payload.action,
        "stage_advanced": stage_changed,
        "current_stage": new_stage
    }


@router.post("/{lead_id}/mark-no-whatsapp")
def mark_no_whatsapp(lead_id: UUID):
    lead_str = str(lead_id)
    rows = execute_query("SELECT id, channels_status FROM leads WHERE id = %s AND is_deleted = FALSE;", (lead_str,))
    if not rows:
        raise HTTPException(status_code=404, detail="Lead not found.")

    current_channels = rows[0].get("channels_status") or {}
    if isinstance(current_channels, str):
        try:
            current_channels = json.loads(current_channels)
        except Exception:
            current_channels = {}
    current_channels["whatsapp"] = "DESCARTADO_MANUALMENTE"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET has_whatsapp = FALSE,
                    channels_status = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (json.dumps(current_channels), lead_str)
            )

            # Log interaction
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata)
                VALUES (%s, 'whatsapp', 'MANUAL_MARK_NO_WHATSAPP', %s);
                """,
                (lead_str, json.dumps({"note": "Solo línea fija / Descartado manualmente"}))
            )

    return get_lead_contact_card(lead_id)


@router.get("/{lead_id}/activity")
def get_lead_activity(lead_id: UUID, limit: int = Query(default=20, ge=1, le=100)):
    lead_str = str(lead_id)
    rows = execute_query(
        """
        SELECT id, channel, action, metadata, created_at
        FROM lead_activity_log
        WHERE lead_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """,
        (lead_str, limit)
    )
    return rows
