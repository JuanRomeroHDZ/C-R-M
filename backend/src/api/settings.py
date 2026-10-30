import os
import socket
from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from src.db.connection import get_db_connection, execute_query

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


class SettingUpdate(BaseModel):
    whatsapp_template: Optional[str] = None


def get_lan_ip():
    host_ip = os.getenv("HOST_LAN_IP")
    if host_ip and host_ip != "127.0.0.1":
        return host_ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@router.get("")
def get_settings():
    rows = execute_query("SELECT key, value, description FROM system_settings;")
    settings_dict = {r["key"]: r["value"] for r in rows}

    lan_ip = get_lan_ip()
    proxy_port = os.getenv("HOST_PORT_PROXY", "8080")

    return {
        "whatsapp_template": settings_dict.get("whatsapp_template", "Hola, buen día."),
        "lan_ip": lan_ip,
        "proxy_port": proxy_port,
        "lan_url": f"http://{lan_ip}:{proxy_port}",
        "local_url": f"http://localhost:{proxy_port}",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@router.post("")
def update_settings(payload: SettingUpdate):
    if payload.whatsapp_template is not None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO system_settings (key, value, description, updated_at)
                    VALUES ('whatsapp_template', %s, 'Mensaje inicial predeterminado para WhatsApp', NOW())
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
                    """,
                    (payload.whatsapp_template,)
                )

    return get_settings()
