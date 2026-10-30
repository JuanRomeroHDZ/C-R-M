import logging
from typing import Dict, Any, List
from fastapi import APIRouter
from src.db.connection import execute_query
from src.pipeline.state_machine import STAGES

logger = logging.getLogger("crm.api.metrics")
router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics & Analytics"])


@router.get("/dashboard")
def get_metrics_dashboard():
    # 1. Total leads and stage distribution
    stage_counts_rows = execute_query(
        """
        SELECT lifecycle_stage, count(*) as count
        FROM leads
        WHERE is_deleted = FALSE
        GROUP BY lifecycle_stage;
        """
    )
    counts_map = {r["lifecycle_stage"]: r["count"] for r in stage_counts_rows}
    total_leads = sum(counts_map.values())

    # Build 12-stage funnel
    funnel = []
    prev_count = total_leads
    for st in STAGES:
        slug = st["slug"]
        cnt = counts_map.get(slug, 0)
        pct_of_total = round((cnt / total_leads * 100), 1) if total_leads > 0 else 0.0
        funnel.append({
            "step": st["step"],
            "slug": slug,
            "name": st["name"],
            "count": cnt,
            "pct_of_total": pct_of_total
        })

    # 2. Objections breakdown (REGRETTED and CLOSED_LOST)
    regret_reasons_rows = execute_query(
        """
        SELECT COALESCE(regret_reason, 'No especificado') as reason, count(*) as count
        FROM leads
        WHERE lifecycle_stage = 'REGRETTED' AND is_deleted = FALSE
        GROUP BY regret_reason
        ORDER BY count DESC;
        """
    )

    loss_reasons_rows = execute_query(
        """
        SELECT COALESCE(loss_reason, 'No especificado') as reason, count(*) as count
        FROM leads
        WHERE lifecycle_stage = 'CLOSED_LOST' AND is_deleted = FALSE
        GROUP BY loss_reason
        ORDER BY count DESC;
        """
    )

    # 3. Category distribution with average probability
    cat_rows = execute_query(
        """
        SELECT category_slug,
               count(*) as count,
               ROUND(AVG(COALESCE(acceptance_probability_pct, 0))::numeric, 1) as avg_score
        FROM leads
        WHERE is_deleted = FALSE
        GROUP BY category_slug
        ORDER BY count DESC;
        """
    )

    # 4. Zone distribution in Tijuana
    zone_rows = execute_query(
        """
        SELECT
            CASE
                WHEN STRPOS(LOWER(COALESCE(address_raw, '')), 'zona rio') > 0 OR STRPOS(LOWER(COALESCE(address_raw, '')), 'zona río') > 0 THEN 'Zona Rio'
                WHEN STRPOS(LOWER(COALESCE(address_raw, '')), 'centro') > 0 THEN 'Zona Centro'
                WHEN STRPOS(LOWER(COALESCE(address_raw, '')), 'otay') > 0 THEN 'Mesa de Otay'
                WHEN STRPOS(LOWER(COALESCE(address_raw, '')), 'playas') > 0 THEN 'Playas de Tijuana'
                WHEN STRPOS(LOWER(COALESCE(address_raw, '')), 'mesa') > 0 THEN 'La Mesa'
                WHEN STRPOS(LOWER(COALESCE(address_raw, '')), 'chapultepec') > 0 OR STRPOS(LOWER(COALESCE(address_raw, '')), 'hipodromo') > 0 THEN 'Chapultepec'
                ELSE 'Otras Zonas Tijuana'
            END as zone,
            count(*) as count
        FROM leads
        WHERE is_deleted = FALSE
        GROUP BY 1
        ORDER BY count DESC;
        """
    )

    # 5. Global KPIs
    won_count = counts_map.get("CLOSED_WON", 0)
    lost_count = counts_map.get("CLOSED_LOST", 0)
    contacted_count = (
        counts_map.get("FIRST_CONTACT", 0) +
        counts_map.get("REPLY_RECEIVED", 0) +
        counts_map.get("IN_CONVERSATION", 0) +
        counts_map.get("PROPOSAL_PRESENTED", 0) +
        counts_map.get("IN_NEGOTIATION", 0) +
        counts_map.get("POSTPONED", 0) +
        won_count
    )

    overall_avg_row = execute_query(
        "SELECT ROUND(AVG(COALESCE(acceptance_probability_pct, 0))::numeric, 1) as avg FROM leads WHERE is_deleted = FALSE;"
    )
    overall_avg = float(overall_avg_row[0]["avg"]) if overall_avg_row and overall_avg_row[0]["avg"] is not None else 0.0

    return {
        "kpis": {
            "total_leads": total_leads,
            "contacted_leads": contacted_count,
            "closed_won": won_count,
            "closed_lost": lost_count,
            "overall_avg_score": overall_avg
        },
        "funnel": funnel,
        "regret_breakdown": regret_reasons_rows,
        "loss_breakdown": loss_reasons_rows,
        "category_distribution": cat_rows,
        "zone_distribution": zone_rows
    }
