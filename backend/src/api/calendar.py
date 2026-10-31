import json
import logging
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
import httpx
from src.db.connection import get_db_connection, execute_query
from src.security.encryption import encrypt_token, decrypt_token

logger = logging.getLogger("crm.api.calendar")
router = APIRouter(prefix="/api/v1/calendar", tags=["Calendar"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")


class CalendarEventCreate(BaseModel):
    lead_id: Optional[UUID] = None
    title: str
    event_type: str = "Llamada"
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    status: str = "Pendiente"


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None


@router.get("/events")
def list_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    status_filter: Optional[str] = None,
    lead_id: Optional[UUID] = None
):
    conditions = []
    params = []

    if start:
        conditions.append("e.start_time >= %s")
        params.append(start)
    if end:
        conditions.append("e.start_time <= %s")
        params.append(end)
    if status_filter:
        conditions.append("e.status = %s")
        params.append(status_filter)
    if lead_id:
        conditions.append("e.lead_id = %s")
        params.append(str(lead_id))

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
    SELECT e.id, e.lead_id, e.title, e.event_type, e.start_time, e.end_time,
           e.notes, e.status, e.google_event_id, e.sync_status, e.created_at, e.updated_at,
           l.name as lead_name, l.phone_e164, l.category_slug, l.acceptance_probability_pct,
           l.has_whatsapp, l.channels_status
    FROM calendar_events e
    LEFT JOIN leads l ON l.id = e.lead_id
    {where_clause}
    ORDER BY e.start_time ASC;
    """
    rows = execute_query(sql, tuple(params))
    return rows


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(payload: CalendarEventCreate):
    lead_id_str = str(payload.lead_id) if payload.lead_id else None

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO calendar_events (
                    lead_id, title, event_type, start_time, end_time, notes, status, sync_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'LOCAL_ONLY')
                RETURNING id, lead_id, title, event_type, start_time, end_time, notes, status, sync_status, created_at;
                """,
                (
                    lead_id_str, payload.title, payload.event_type,
                    payload.start_time, payload.end_time, payload.notes,
                    payload.status
                )
            )
            row = cur.fetchone()

    return row


@router.get("/events/{event_id}")
def get_event(event_id: UUID):
    sql = """
    SELECT e.id, e.lead_id, e.title, e.event_type, e.start_time, e.end_time,
           e.notes, e.status, e.google_event_id, e.sync_status, e.created_at, e.updated_at,
           l.name as lead_name, l.phone_e164, l.category_slug, l.acceptance_probability_pct,
           l.has_whatsapp, l.channels_status, l.social_links, l.website
    FROM calendar_events e
    LEFT JOIN leads l ON l.id = e.lead_id
    WHERE e.id = %s;
    """
    rows = execute_query(sql, (str(event_id),))
    if not rows:
        raise HTTPException(status_code=404, detail="Event not found.")
    return rows[0]


@router.put("/events/{event_id}")
@router.patch("/events/{event_id}")
def update_event(event_id: UUID, payload: CalendarEventUpdate):
    updates = []
    params = []

    if payload.title is not None:
        updates.append("title = %s")
        params.append(payload.title)
    if payload.event_type is not None:
        updates.append("event_type = %s")
        params.append(payload.event_type)
    if payload.start_time is not None:
        updates.append("start_time = %s")
        params.append(payload.start_time)
    if payload.end_time is not None:
        updates.append("end_time = %s")
        params.append(payload.end_time)
    if payload.notes is not None:
        updates.append("notes = %s")
        params.append(payload.notes)
    if payload.status is not None:
        updates.append("status = %s")
        params.append(payload.status)

    if not updates:
        return get_event(event_id)

    updates.append("updated_at = NOW()")
    params.append(str(event_id))

    sql = f"UPDATE calendar_events SET {', '.join(updates)} WHERE id = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))

    return get_event(event_id)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: UUID):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM calendar_events WHERE id = %s;", (str(event_id),))


@router.get("/alerts")
def get_calendar_alerts():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    next_hour = now + timedelta(hours=1)

    # Today's events
    today_rows = execute_query(
        """
        SELECT e.id, e.title, e.event_type, e.start_time, e.status, l.name as lead_name
        FROM calendar_events e
        LEFT JOIN leads l ON l.id = e.lead_id
        WHERE e.start_time >= %s AND e.start_time < %s AND e.status = 'Pendiente'
        ORDER BY e.start_time ASC;
        """,
        (today_start, today_end)
    )

    # Imminent alerts (within the next 60 minutes)
    imminent_rows = execute_query(
        """
        SELECT e.id, e.title, e.event_type, e.start_time, l.name as lead_name, l.phone_e164
        FROM calendar_events e
        LEFT JOIN leads l ON l.id = e.lead_id
        WHERE e.start_time >= %s AND e.start_time <= %s AND e.status = 'Pendiente'
        ORDER BY e.start_time ASC;
        """,
        (now, next_hour)
    )

    # Pending follow-ups in qualified leads without calendar events
    pending_qualified = execute_query(
        """
        SELECT COUNT(*) as count
        FROM leads
        WHERE lifecycle_stage = 'QUALIFIED' AND is_deleted = FALSE
        AND id NOT IN (SELECT lead_id FROM calendar_events WHERE lead_id IS NOT NULL);
        """
    )
    unassigned_count = pending_qualified[0]["count"] if pending_qualified else 0

    return {
        "today_pending_count": len(today_rows),
        "imminent_alerts": imminent_rows,
        "unassigned_qualified_leads": unassigned_count
    }


# ------------------------------------------------------------------------------
# Google Calendar OAuth 2.0 Integration
# ------------------------------------------------------------------------------
@router.get("/oauth/status")
def get_oauth_status():
    rows = execute_query("SELECT user_email, updated_at FROM oauth_tokens WHERE provider = 'google';")
    is_connected = len(rows) > 0
    configured_in_env = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

    mode_label = "Modo Local Activo (Conectar Gmail opcional)"
    if is_connected:
        mode_label = f"Conectado a Google Calendar ({rows[0]['user_email']})"

    return {
        "connected": is_connected,
        "user_email": rows[0]["user_email"] if is_connected else None,
        "configured_in_env": configured_in_env,
        "mode_label": mode_label
    }


@router.get("/oauth/authorize")
def authorize_google():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_CLIENT_ID no está configurado en las variables de entorno."
        )

    redirect_uri = GOOGLE_REDIRECT_URI or "http://localhost:8000/api/v1/calendar/oauth/callback"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url}


@router.get("/oauth/callback")
async def oauth_callback(code: str):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Credenciales OAuth no configuradas.")

    redirect_uri = GOOGLE_REDIRECT_URI or "http://localhost:8000/api/v1/calendar/oauth/callback"

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Falla al canjear código de autorización con Google.")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Get user email
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_email = user_info_resp.json().get("email", "usuario@gmail.com") if user_info_resp.status_code == 200 else None

        enc_access_token = encrypt_token(access_token)
        enc_refresh_token = encrypt_token(refresh_token) if refresh_token else None

    # Store encrypted tokens in database at rest
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO oauth_tokens (provider, access_token, refresh_token, expires_at, user_email, updated_at)
                VALUES ('google', %s, %s, %s, %s, NOW())
                ON CONFLICT (provider) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = COALESCE(EXCLUDED.refresh_token, oauth_tokens.refresh_token),
                    expires_at = EXCLUDED.expires_at,
                    user_email = EXCLUDED.user_email,
                    updated_at = NOW();
                """,
                (enc_access_token, enc_refresh_token, expires_at, user_email)
            )

    return {"status": "SUCCESS", "message": "Google Calendar sincronizado correctamente.", "email": user_email}


@router.post("/oauth/disconnect")
def disconnect_google():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM oauth_tokens WHERE provider = 'google';")
    return {"status": "DISCONNECTED", "mode_label": "Modo Local Activo (Conectar Gmail opcional)"}
