import logging
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from src.db.connection import get_db_connection, execute_query
from src.security.encryption import hash_pin_argon2, verify_pin_argon2
from src.security.sanitization import sanitize_text

logger = logging.getLogger("crm.api.security")
router = APIRouter(prefix="/api/v1/security", tags=["Security & AppSec"])


class PinSetRequest(BaseModel):
    pin: str
    current_pin: str = ""


class PinVerifyRequest(BaseModel):
    pin: str


class ProtectionToggleRequest(BaseModel):
    enabled: bool
    pin: str


@router.get("/status")
def get_security_status():
    rows = execute_query(
        "SELECT key, value FROM system_settings WHERE key IN ('lan_protection_enabled', 'lan_access_pin_hash');"
    )
    settings_dict = {r["key"]: r["value"] for r in rows}
    has_pin = bool(settings_dict.get("lan_access_pin_hash"))
    enabled = settings_dict.get("lan_protection_enabled", "false") == "true"

    return {
        "protection_enabled": enabled,
        "pin_configured": has_pin,
        "algorithm": "Argon2id"
    }


@router.post("/set-pin")
def set_security_pin(payload: PinSetRequest):
    pin = payload.pin.strip()
    if len(pin) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El PIN de seguridad debe contener al menos 4 caracteres."
        )

    rows = execute_query("SELECT value FROM system_settings WHERE key = 'lan_access_pin_hash';")
    current_hash = rows[0]["value"] if rows else ""

    # If already set, verify current pin first
    if current_hash:
        if not payload.current_pin or not verify_pin_argon2(current_hash, payload.current_pin.strip()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El PIN actual proporcionado es incorrecto."
            )

    # Hash new PIN strictly with Argon2id
    new_hash = hash_pin_argon2(pin)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_settings (key, value, description, updated_at)
                VALUES ('lan_access_pin_hash', %s, 'Hash Argon2id del PIN de acceso local', NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
                """,
                (new_hash,)
            )

    logger.info("Local access PIN set successfully with Argon2id.")
    return {"status": "SUCCESS", "message": "PIN de seguridad configurado con Argon2id."}


@router.post("/verify-pin")
def verify_security_pin(payload: PinVerifyRequest):
    rows = execute_query("SELECT value FROM system_settings WHERE key = 'lan_access_pin_hash';")
    stored_hash = rows[0]["value"] if rows else ""

    if not stored_hash:
        # If no PIN configured, always valid
        return {"valid": True, "protection_enabled": False}

    is_valid = verify_pin_argon2(stored_hash, payload.pin.strip())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN de acceso incorrecto."
        )

    return {"valid": True, "message": "Acceso autorizado."}


@router.post("/toggle-protection")
def toggle_protection(payload: ProtectionToggleRequest):
    rows = execute_query("SELECT value FROM system_settings WHERE key = 'lan_access_pin_hash';")
    stored_hash = rows[0]["value"] if rows else ""

    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes configurar un PIN antes de habilitar el bloqueo en red local."
        )

    if not verify_pin_argon2(stored_hash, payload.pin.strip()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PIN incorrecto."
        )

    val_str = "true" if payload.enabled else "false"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE system_settings
                SET value = %s, updated_at = NOW()
                WHERE key = 'lan_protection_enabled';
                """,
                (val_str,)
            )

    logger.info(f"LAN protection toggled to: {val_str}")
    return {"status": "SUCCESS", "protection_enabled": payload.enabled}
