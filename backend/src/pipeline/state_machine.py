import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import HTTPException
from src.db.connection import get_db_connection, execute_query

logger = logging.getLogger("crm.pipeline.state_machine")

# 12 Exact Pipeline Stages
STAGES = [
    {"slug": "EXTRACTED", "name": "Extraído", "step": 1},
    {"slug": "AUDITED", "name": "Auditado", "step": 2},
    {"slug": "QUALIFIED", "name": "Calificado", "step": 3},
    {"slug": "FIRST_CONTACT", "name": "Primer Contacto", "step": 4},
    {"slug": "REPLY_RECEIVED", "name": "Respuesta Recibida", "step": 5},
    {"slug": "IN_CONVERSATION", "name": "En Conversación", "step": 6},
    {"slug": "PROPOSAL_PRESENTED", "name": "Demostración / Propuesta", "step": 7},
    {"slug": "IN_NEGOTIATION", "name": "En Negociación", "step": 8},
    {"slug": "POSTPONED", "name": "En Espera / Postergado", "step": 9},
    {"slug": "REGRETTED", "name": "Arrepentimiento / Retractado", "step": 10},
    {"slug": "CLOSED_WON", "name": "Cerrado - Ganado", "step": 11},
    {"slug": "CLOSED_LOST", "name": "Cerrado - Descartado", "step": 12},
]

VALID_STAGES = [s["slug"] for s in STAGES]

REGRET_REASONS = [
    "Presupuesto insuficiente",
    "Decidió ir con otro proveedor",
    "Urgencia operativa interna",
    "Desconfianza / Indecisión",
    "Dejó de responder tras aceptar",
    "Otro"
]

LOSS_REASONS = [
    "No le interesa",
    "Ya cuenta con equipo interno",
    "Número equivocado / Inexistente",
    "Negocio cerrado definitivamente",
    "Sin presupuesto"
]

STAGNATION_THRESHOLD_HOURS = 48
STAGNATION_STAGES = {"FIRST_CONTACT", "IN_CONVERSATION", "PROPOSAL_PRESENTED", "IN_NEGOTIATION"}


def get_stagnation_info(lead: Dict[str, Any]) -> Dict[str, Any]:
    stage = lead.get("lifecycle_stage")
    if stage not in STAGNATION_STAGES:
        return {"is_stagnant": False, "stagnant_hours": 0}

    now = datetime.now(timezone.utc)
    last_act = lead.get("last_activity_at") or lead.get("stage_entered_at") or lead.get("updated_at") or lead.get("created_at")
    if not last_act:
        return {"is_stagnant": False, "stagnant_hours": 0}

    if last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)

    diff = now - last_act
    hours = int(diff.total_seconds() / 3600)
    is_stagnant = hours >= STAGNATION_THRESHOLD_HOURS

    return {
        "is_stagnant": is_stagnant,
        "stagnant_hours": hours,
        "threshold_hours": STAGNATION_THRESHOLD_HOURS
    }


def transition_stage(
    lead_id: UUID,
    to_stage: str,
    notes: Optional[str] = None,
    reactivation_date: Optional[str] = None,
    regret_reason: Optional[str] = None,
    regret_details: Optional[str] = None,
    regret_amount: Optional[float] = None,
    regret_service: Optional[str] = None,
    loss_reason: Optional[str] = None,
    changed_by: str = "usuario"
) -> Dict[str, Any]:
    to_stage = to_stage.strip().upper()
    if to_stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Fase no valida: {to_stage}. Fases validas: {', '.join(VALID_STAGES)}"
        )

    # 1. Fetch current lead
    rows = execute_query(
        """
        SELECT id, name, lifecycle_stage, stage_entered_at, last_activity_at, created_at, phone_e164
        FROM leads WHERE id = %s AND is_deleted = FALSE;
        """,
        (str(lead_id),)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado o en papelera.")

    lead = rows[0]
    from_stage = lead["lifecycle_stage"]

    # 2. Validation per stage
    parsed_reactivation = None
    if to_stage == "POSTPONED":
        if not reactivation_date:
            raise HTTPException(
                status_code=400,
                detail="Fecha de reactivacion obligatoria para la fase En Espera / Postergado."
            )
        try:
            parsed_reactivation = datetime.fromisoformat(reactivation_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha de reactivacion invalido. Utiliza formato ISO 8601."
            )
        if not notes or not notes.strip():
            raise HTTPException(
                status_code=400,
                detail="Nota explicativa obligatoria para la fase En Espera / Postergado."
            )

    if to_stage == "REGRETTED":
        if not regret_reason or regret_reason.strip() not in REGRET_REASONS:
            raise HTTPException(
                status_code=400,
                detail=f"Motivo de arrepentimiento obligatorio. Opciones validas: {', '.join(REGRET_REASONS)}"
            )

    if to_stage == "CLOSED_LOST":
        if not loss_reason or loss_reason.strip() not in LOSS_REASONS:
            raise HTTPException(
                status_code=400,
                detail=f"Motivo de descarte obligatorio. Opciones validas: {', '.join(LOSS_REASONS)}"
            )

    # 3. Calculate duration spent in from_stage
    now = datetime.now(timezone.utc)
    stage_entered = lead.get("stage_entered_at") or lead.get("created_at") or now
    if stage_entered.tzinfo is None:
        stage_entered = stage_entered.replace(tzinfo=timezone.utc)

    duration_seconds = max(0, int((now - stage_entered).total_seconds()))

    # 4. Perform atomic update in PostgreSQL
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Insert Stage History
            cur.execute(
                """
                INSERT INTO lead_stage_history (
                    lead_id, from_stage, to_stage, duration_seconds, changed_by, notes, reason, metadata, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id;
                """,
                (
                    str(lead_id),
                    from_stage,
                    to_stage,
                    duration_seconds,
                    changed_by,
                    notes,
                    regret_reason or loss_reason,
                    json.dumps({
                        "regret_details": regret_details,
                        "regret_amount": regret_amount,
                        "regret_service": regret_service,
                        "reactivation_date": reactivation_date
                    }),
                    now
                )
            )

            # Update Lead record
            cur.execute(
                """
                UPDATE leads SET
                    lifecycle_stage = %s,
                    stage_entered_at = %s,
                    last_activity_at = %s,
                    postponed_until = %s,
                    postponed_note = %s,
                    regret_reason = %s,
                    regret_details = %s,
                    regret_amount = %s,
                    regret_service = %s,
                    loss_reason = %s,
                    updated_at = %s
                WHERE id = %s;
                """,
                (
                    to_stage,
                    now,
                    now,
                    parsed_reactivation,
                    notes if to_stage == "POSTPONED" else None,
                    regret_reason if to_stage == "REGRETTED" else None,
                    regret_details if to_stage == "REGRETTED" else None,
                    regret_amount if to_stage == "REGRETTED" else None,
                    regret_service if to_stage == "REGRETTED" else None,
                    loss_reason if to_stage == "CLOSED_LOST" else None,
                    now,
                    str(lead_id)
                )
            )

            # Stage 9 Auto-schedule Calendar Event
            if to_stage == "POSTPONED" and parsed_reactivation:
                cal_end = parsed_reactivation + timedelta(minutes=30)
                cur.execute(
                    """
                    INSERT INTO calendar_events (
                        lead_id, title, event_type, start_time, end_time, notes, status, sync_status, created_at, updated_at
                    ) VALUES (
                        %s, %s, 'SEGUIMIENTO', %s, %s, %s, 'Pendiente', 'LOCAL_ONLY', %s, %s
                    );
                    """,
                    (
                        str(lead_id),
                        f"Reactivar prospecto: {lead['name']}",
                        parsed_reactivation,
                        cal_end,
                        notes,
                        now,
                        now
                    )
                )

            # Log to Activity Log for unified timeline
            cur.execute(
                """
                INSERT INTO lead_activity_log (
                    lead_id, channel, action, metadata, created_at
                ) VALUES (
                    %s, 'PIPELINE', 'STAGE_TRANSITION', %s, %s
                );
                """,
                (
                    str(lead_id),
                    json.dumps({
                        "from_stage": from_stage,
                        "to_stage": to_stage,
                        "duration_seconds": duration_seconds,
                        "notes": notes,
                        "reason": regret_reason or loss_reason
                    }),
                    now
                )
            )

    logger.info(f"Lead {lead_id} transitioned: {from_stage} -> {to_stage} (duracion {duration_seconds}s)")
    return {
        "lead_id": str(lead_id),
        "from_stage": from_stage,
        "to_stage": to_stage,
        "duration_seconds": duration_seconds,
        "stage_entered_at": now.isoformat(),
        "notes": notes
    }


def check_duplicate(
    name: Optional[str] = None,
    phone_e164: Optional[str] = None,
    normalized_domain: Optional[str] = None,
    exclude_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    exclude_clause = "AND id != %s" if exclude_id else ""
    exclude_params = [str(exclude_id)] if exclude_id else []

    # Check Phone collision (E.164)
    if phone_e164 and phone_e164.strip():
        clean_phone = phone_e164.strip()
        rows = execute_query(
            f"SELECT id, name, lifecycle_stage, phone_e164, is_deleted FROM leads WHERE phone_e164 = %s {exclude_clause} LIMIT 1;",
            tuple([clean_phone] + exclude_params)
        )
        if rows:
            r = rows[0]
            return {
                "is_duplicate": True,
                "conflict_field": "phone_e164",
                "conflict_value": clean_phone,
                "existing_lead": {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "lifecycle_stage": r["lifecycle_stage"],
                    "is_deleted": r["is_deleted"]
                }
            }

    # Check Normalized Domain collision
    if normalized_domain and normalized_domain.strip():
        clean_domain = normalized_domain.strip().lower()
        rows = execute_query(
            f"SELECT id, name, lifecycle_stage, normalized_domain, is_deleted FROM leads WHERE normalized_domain = %s {exclude_clause} LIMIT 1;",
            tuple([clean_domain] + exclude_params)
        )
        if rows:
            r = rows[0]
            return {
                "is_duplicate": True,
                "conflict_field": "normalized_domain",
                "conflict_value": clean_domain,
                "existing_lead": {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "lifecycle_stage": r["lifecycle_stage"],
                    "is_deleted": r["is_deleted"]
                }
            }

    # Check Name exact match
    if name and name.strip():
        clean_name = name.strip()
        rows = execute_query(
            f"SELECT id, name, lifecycle_stage, is_deleted FROM leads WHERE LOWER(name) = LOWER(%s) {exclude_clause} LIMIT 1;",
            tuple([clean_name] + exclude_params)
        )
        if rows:
            r = rows[0]
            return {
                "is_duplicate": True,
                "conflict_field": "name",
                "conflict_value": clean_name,
                "existing_lead": {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "lifecycle_stage": r["lifecycle_stage"],
                    "is_deleted": r["is_deleted"]
                }
            }

    return None


def soft_delete_lead(lead_id: UUID, reason: str = "Descarte manual de usuario") -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads SET
                    is_deleted = TRUE,
                    deleted_at = %s,
                    deleted_reason = %s,
                    updated_at = %s
                WHERE id = %s AND is_deleted = FALSE
                RETURNING id, name, phone_e164, normalized_domain, external_id;
                """,
                (now, reason, now, str(lead_id))
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Prospecto no encontrado o ya eliminado.")

            # Add to blacklist for re-extraction immunity
            phone = row.get("phone_e164")
            domain = row.get("normalized_domain")
            ext_id = row.get("external_id")

            cur.execute(
                """
                INSERT INTO blacklist_identifiers (phone_e164, normalized_domain, external_id, reason, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (phone, domain, ext_id, f"Soft-deleted: {reason}", now)
            )

            # Log to Activity Log
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata, created_at)
                VALUES (%s, 'PIPELINE', 'SOFT_DELETE', %s, %s);
                """,
                (str(lead_id), json.dumps({"reason": reason}), now)
            )

    logger.info(f"Lead {lead_id} soft deleted and blacklisted.")
    return {"status": "DELETED", "lead_id": str(lead_id), "deleted_at": now.isoformat()}


def restore_lead(lead_id: UUID) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads SET
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    deleted_reason = NULL,
                    updated_at = %s
                WHERE id = %s AND is_deleted = TRUE
                RETURNING id, name, phone_e164, normalized_domain, external_id;
                """,
                (now, str(lead_id))
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Prospecto no encontrado en papelera.")

            # Remove from blacklist
            phone = row.get("phone_e164")
            domain = row.get("normalized_domain")
            ext_id = row.get("external_id")

            cur.execute(
                """
                DELETE FROM blacklist_identifiers
                WHERE (phone_e164 IS NOT NULL AND phone_e164 = %s)
                   OR (normalized_domain IS NOT NULL AND normalized_domain = %s)
                   OR (external_id IS NOT NULL AND external_id = %s);
                """,
                (phone, domain, ext_id)
            )

            # Log to Activity Log
            cur.execute(
                """
                INSERT INTO lead_activity_log (lead_id, channel, action, metadata, created_at)
                VALUES (%s, 'PIPELINE', 'RESTORED', '{}'::jsonb, %s);
                """,
                (str(lead_id), now)
            )

    logger.info(f"Lead {lead_id} restored from trash.")
    return {"status": "RESTORED", "lead_id": str(lead_id)}


def purge_lead_permanent(lead_id: UUID) -> Dict[str, Any]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM leads WHERE id = %s;", (str(lead_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

            cur.execute("DELETE FROM leads WHERE id = %s;", (str(lead_id),))

    logger.info(f"Lead {lead_id} permanently purged from database.")
    return {"status": "PURGED", "lead_id": str(lead_id)}


def reset_lead_history(lead_id: UUID) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM leads WHERE id = %s;", (str(lead_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

            cur.execute("DELETE FROM lead_stage_history WHERE lead_id = %s;", (str(lead_id),))
            cur.execute("DELETE FROM lead_activity_log WHERE lead_id = %s;", (str(lead_id),))
            cur.execute("DELETE FROM lead_notes WHERE lead_id = %s;", (str(lead_id),))
            cur.execute(
                """
                UPDATE leads SET
                    lifecycle_stage = 'QUALIFIED',
                    stage_entered_at = %s,
                    last_activity_at = %s,
                    postponed_until = NULL,
                    postponed_note = NULL,
                    regret_reason = NULL,
                    regret_details = NULL,
                    regret_amount = NULL,
                    regret_service = NULL,
                    loss_reason = NULL,
                    updated_at = %s
                WHERE id = %s;
                """,
                (now, now, now, str(lead_id))
            )

    logger.info(f"Lead {lead_id} history reset to QUALIFIED.")
    return {"status": "RESET", "lead_id": str(lead_id)}
