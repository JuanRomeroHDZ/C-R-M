import csv
import datetime
import io
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel
from src.db.connection import get_db_connection, execute_query
from src.security.sanitization import sanitize_text

logger = logging.getLogger("crm.api.settings_advanced")
router = APIRouter(prefix="/api/v1", tags=["Settings & Maintenance"])


# Pydantic Schemas for Modular Settings
class OperatorProfileUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    country_code: Optional[str] = None


class ScraperLimitsUpdate(BaseModel):
    concurrency: Optional[int] = None
    jitter_min_ms: Optional[int] = None
    jitter_max_ms: Optional[int] = None
    quadtree_max_depth: Optional[int] = None
    block_heavy_resources: Optional[bool] = None


class ScoringWeightsUpdate(BaseModel):
    weight_no_website: Optional[float] = None
    weight_ssl_expired: Optional[float] = None
    weight_slow_ttfb: Optional[float] = None
    threshold_ttfb_ms: Optional[int] = None
    weight_no_mobile: Optional[float] = None
    weight_no_pixels: Optional[float] = None


class TemplatesChannelsUpdate(BaseModel):
    whatsapp_template: Optional[str] = None
    visible_channels: Optional[List[str]] = None


class PipelineRulesUpdate(BaseModel):
    stagnation_threshold_hours: Optional[int] = None


class FactoryResetRequest(BaseModel):
    confirmation_phrase: str


@router.get("/settings/all")
def get_all_settings():
    rows = execute_query("SELECT key, value FROM system_settings;")
    settings_dict = {r["key"]: r["value"] for r in rows}

    try:
        vis_channels = json.loads(settings_dict.get("visible_channels", "[]"))
    except Exception:
        vis_channels = ["whatsapp", "phone", "website", "email", "facebook", "instagram"]

    return {
        "operator": {
            "name": settings_dict.get("operator_name", "Operador Tijuana"),
            "whatsapp": settings_dict.get("operator_whatsapp", ""),
            "email": settings_dict.get("operator_email", ""),
            "country_code": settings_dict.get("operator_country_code", "+52")
        },
        "scraper": {
            "concurrency": int(settings_dict.get("scraper_concurrency", 5)),
            "jitter_min_ms": int(settings_dict.get("scraper_jitter_min_ms", 1500)),
            "jitter_max_ms": int(settings_dict.get("scraper_jitter_max_ms", 4500)),
            "quadtree_max_depth": int(settings_dict.get("scraper_quadtree_max_depth", 3)),
            "block_heavy_resources": settings_dict.get("scraper_block_heavy_resources", "true") == "true"
        },
        "scoring": {
            "weight_no_website": float(settings_dict.get("weight_no_website", 25.0)),
            "weight_ssl_expired": float(settings_dict.get("weight_ssl_expired", 15.0)),
            "weight_slow_ttfb": float(settings_dict.get("weight_slow_ttfb", 15.0)),
            "threshold_ttfb_ms": int(settings_dict.get("threshold_ttfb_ms", 1800)),
            "weight_no_mobile": float(settings_dict.get("weight_no_mobile", 20.0)),
            "weight_no_pixels": float(settings_dict.get("weight_no_pixels", 15.0))
        },
        "templates": {
            "whatsapp_template": settings_dict.get("whatsapp_template", "Hola, buen día."),
            "visible_channels": vis_channels
        },
        "pipeline": {
            "stagnation_threshold_hours": int(settings_dict.get("stagnation_threshold_hours", 48))
        },
        "security": {
            "lan_protection_enabled": settings_dict.get("lan_protection_enabled", "false") == "true",
            "pin_configured": bool(settings_dict.get("lan_access_pin_hash"))
        },
        "onboarding": {
            "completed": settings_dict.get("onboarding_completed", "false") == "true"
        }
    }


def _update_setting_key(key: str, val: str, desc: str = ""):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_settings (key, value, description, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
                """,
                (key, val, desc)
            )


@router.post("/settings/operator")
def update_operator_profile(payload: OperatorProfileUpdate):
    if payload.name is not None:
        _update_setting_key("operator_name", sanitize_text(payload.name))
    if payload.whatsapp is not None:
        _update_setting_key("operator_whatsapp", payload.whatsapp.strip())
    if payload.email is not None:
        _update_setting_key("operator_email", payload.email.strip())
    if payload.country_code is not None:
        _update_setting_key("operator_country_code", payload.country_code.strip())
    return {"status": "SUCCESS", "message": "Perfil de operador actualizado."}


@router.post("/settings/scraper")
def update_scraper_limits(payload: ScraperLimitsUpdate):
    if payload.concurrency is not None:
        _update_setting_key("scraper_concurrency", str(max(1, min(20, payload.concurrency))))
    if payload.jitter_min_ms is not None:
        _update_setting_key("scraper_jitter_min_ms", str(max(500, payload.jitter_min_ms)))
    if payload.jitter_max_ms is not None:
        _update_setting_key("scraper_jitter_max_ms", str(max(1000, payload.jitter_max_ms)))
    if payload.quadtree_max_depth is not None:
        _update_setting_key("scraper_quadtree_max_depth", str(max(1, min(5, payload.quadtree_max_depth))))
    if payload.block_heavy_resources is not None:
        _update_setting_key("scraper_block_heavy_resources", "true" if payload.block_heavy_resources else "false")
    return {"status": "SUCCESS", "message": "Parametros del motor de extraccion actualizados."}


@router.post("/settings/scoring")
def update_scoring_weights(payload: ScoringWeightsUpdate):
    if payload.weight_no_website is not None:
        _update_setting_key("weight_no_website", str(payload.weight_no_website))
    if payload.weight_ssl_expired is not None:
        _update_setting_key("weight_ssl_expired", str(payload.weight_ssl_expired))
    if payload.weight_slow_ttfb is not None:
        _update_setting_key("weight_slow_ttfb", str(payload.weight_slow_ttfb))
    if payload.threshold_ttfb_ms is not None:
        _update_setting_key("threshold_ttfb_ms", str(payload.threshold_ttfb_ms))
    if payload.weight_no_mobile is not None:
        _update_setting_key("weight_no_mobile", str(payload.weight_no_mobile))
    if payload.weight_no_pixels is not None:
        _update_setting_key("weight_no_pixels", str(payload.weight_no_pixels))
    return {"status": "SUCCESS", "message": "Ponderaciones de exito actualizadas."}


@router.post("/settings/recalibrate-scores")
def recalibrate_all_scores():
    # Read current weights
    weights = get_all_settings()["scoring"]
    leads = execute_query(
        """
        SELECT l.id, l.name, l.website, l.review_count, l.rating,
               a.dns_resolved, a.ssl_valid, a.ttfb_ms, a.http_status_code,
               a.has_viewport, a.has_meta_pixel, a.has_google_analytics
        FROM leads l
        LEFT JOIN lead_web_audits a ON a.lead_id = l.id
        WHERE l.is_deleted = FALSE;
        """
    )

    recalculated_count = 0
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for r in leads:
                lead_id = r["id"]
                prob = 0.0

                # 1. Traccion comercial
                rev = r["review_count"] or 0
                if rev >= 5:
                    prob += min(30.0, rev * 0.8)

                # 2. Ausencia de sitio web
                has_web = bool(r["website"] and r["website"].strip())
                if not has_web:
                    prob += weights["weight_no_website"]
                else:
                    # Auditoria
                    if r.get("ssl_valid") is False:
                        prob += weights["weight_ssl_expired"]
                    ttfb = r.get("ttfb_ms") or 0
                    if ttfb > weights["threshold_ttfb_ms"] or (r.get("http_status_code") and r["http_status_code"] >= 400):
                        prob += weights["weight_slow_ttfb"]
                    if r.get("has_viewport") is False:
                        prob += weights["weight_no_mobile"]
                    if r.get("has_meta_pixel") is False and r.get("has_google_analytics") is False:
                        prob += weights["weight_no_pixels"]

                final_prob = min(98.0, max(5.0, prob))
                cur.execute(
                    "UPDATE leads SET acceptance_probability_pct = %s, updated_at = NOW() WHERE id = %s;",
                    (final_prob, str(lead_id))
                )
                recalculated_count += 1

    logger.info(f"Recalibrated scores for {recalculated_count} leads.")
    return {"status": "SUCCESS", "recalculated_leads": recalculated_count}


@router.post("/settings/templates")
def update_templates_channels(payload: TemplatesChannelsUpdate):
    if payload.whatsapp_template is not None:
        _update_setting_key("whatsapp_template", payload.whatsapp_template.strip())
    if payload.visible_channels is not None:
        _update_setting_key("visible_channels", json.dumps(payload.visible_channels))
    return {"status": "SUCCESS", "message": "Plantillas y canales actualizados."}


@router.post("/settings/pipeline")
def update_pipeline_rules(payload: PipelineRulesUpdate):
    if payload.stagnation_threshold_hours is not None:
        _update_setting_key("stagnation_threshold_hours", str(max(12, payload.stagnation_threshold_hours)))
    return {"status": "SUCCESS", "message": "Reglas de pipeline actualizadas."}


# ------------------------------------------------------------------------------
# Export & Import & Maintenance
# ------------------------------------------------------------------------------
@router.get("/maintenance/export")
def export_database(format: str = Query(default="json", pattern="^(json|csv)$")):
    leads = execute_query(
        """
        SELECT id, external_source, external_id, name, category_slug, primary_category,
               phone_e164, phone_raw, website, email, address_raw, city, state, country,
               rating, review_count, lifecycle_stage, acceptance_probability_pct,
               technical_health_score, has_whatsapp, created_at, updated_at
        FROM leads
        ORDER BY created_at DESC;
        """
    )

    if format == "csv":
        output = io.StringIO()
        if leads:
            writer = csv.DictWriter(output, fieldnames=list(leads[0].keys()))
            writer.writeheader()
            for row in leads:
                # Format dates to string
                cleaned_row = {k: str(v) if v is not None else "" for k, v in row.items()}
                writer.writerow(cleaned_row)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=crm_tijuana_leads.csv"}
        )

    # JSON export
    cleaned_leads = []
    for r in leads:
        lead_dict = dict(r)
        lead_dict["id"] = str(lead_dict["id"])
        if lead_dict.get("created_at"):
            lead_dict["created_at"] = lead_dict["created_at"].isoformat()
        if lead_dict.get("updated_at"):
            lead_dict["updated_at"] = lead_dict["updated_at"].isoformat()
        cleaned_leads.append(lead_dict)

    settings_rows = execute_query("SELECT key, value FROM system_settings;")
    settings_dict = {r["key"]: r["value"] for r in settings_rows}

    export_bundle = {
        "export_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_records": len(cleaned_leads),
        "leads": cleaned_leads,
        "settings": settings_dict
    }
    return Response(
        content=json.dumps(export_bundle, indent=2, ensure_ascii=False, default=str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=crm_tijuana_backup.json"}
    )


@router.post("/maintenance/factory-reset")
def factory_reset_database(payload: FactoryResetRequest):
    # Required confirmation phrase
    if payload.confirmation_phrase.strip().lower() != "purgar datos crm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frase de confirmacion incorrecta. Escribe exactamente 'purgar datos crm'."
        )

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM calendar_events;")
            cur.execute("DELETE FROM lead_activity_log;")
            cur.execute("DELETE FROM lead_stage_history;")
            cur.execute("DELETE FROM lead_notes;")
            cur.execute("DELETE FROM lead_web_audits;")
            cur.execute("DELETE FROM deduplication_history;")
            cur.execute("DELETE FROM blacklist_identifiers;")
            cur.execute("DELETE FROM extraction_grid_cells;")
            cur.execute("DELETE FROM extraction_jobs;")
            cur.execute("DELETE FROM leads;")

    logger.warning("FACTORY RESET EXECUTED: All leads and operational tables purged.")
    return {"status": "SUCCESS", "message": "Base de datos restablecida a valores iniciales."}


# ------------------------------------------------------------------------------
# Onboarding Status
# ------------------------------------------------------------------------------
@router.get("/onboarding/status")
def get_onboarding_status():
    rows = execute_query("SELECT value FROM system_settings WHERE key = 'onboarding_completed';")
    completed = rows[0]["value"] == "true" if rows else False
    return {"completed": completed}


@router.post("/onboarding/complete")
def complete_onboarding():
    _update_setting_key("onboarding_completed", "true", "Recorrido completado")
    return {"status": "SUCCESS", "completed": True}


@router.post("/onboarding/reset")
def reset_onboarding():
    _update_setting_key("onboarding_completed", "false", "Recorrido reiniciado")
    return {"status": "SUCCESS", "completed": False}
