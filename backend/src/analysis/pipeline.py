import json
import logging
from typing import Dict, Any, Optional
from src.analysis.deduplication import normalize_lead_record
from src.analysis.web_auditor import TechnicalWebAuditor
from src.analysis.scoring import calculate_technical_health_score, calculate_acceptance_probability
from src.analysis.config_scoring import scoring_config
from src.db.connection import get_db_connection, execute_query

logger = logging.getLogger("crm.analysis.pipeline")
auditor_instance = TechnicalWebAuditor()


async def process_and_audit_lead(lead_id: str) -> Dict[str, Any]:
    # 1. Normalize lead contact info and website
    norm_data = normalize_lead_record(lead_id)

    rows = execute_query(
        """
        SELECT id, name, category_slug, phone_raw, phone_e164, website, normalized_domain,
               has_dedicated_website, social_links, rating, review_count, is_claimed,
               lifecycle_stage, is_deleted
        FROM leads
        WHERE id = %s AND is_deleted = FALSE;
        """,
        (lead_id,)
    )
    if not rows:
        return {"error": "Lead not found or soft-deleted"}

    lead = rows[0]
    has_dedicated_web = lead.get("has_dedicated_website") or False
    web_url = lead.get("website")

    audit_data = None
    if has_dedicated_web and web_url:
        logger.info(f"Auditing website for lead {lead['name']}: {web_url}")
        audit_data = await auditor_instance.audit_lead_website(lead_id, web_url)
        health_score = calculate_technical_health_score(audit_data, True)
    else:
        health_score = 0.0

    prob_pct, arguments = calculate_acceptance_probability(lead, audit_data, health_score)

    # 2. Pipeline State Transition (12-phase pipeline)
    # Stage 1: EXTRACTED -> Stage 2: AUDITED
    new_stage = "AUDITED"
    qualified_at_clause = ""
    qualified_at_param = []

    # Qualification criteria: viable contact and acceptance prob >= threshold
    has_contact = bool(lead.get("phone_e164") or lead.get("phone_raw") or has_dedicated_web)
    is_qualified = (prob_pct >= scoring_config.MIN_ACCEPTANCE_FOR_QUALIFIED) and has_contact

    if is_qualified:
        # Stage 2: AUDITED -> Stage 3: QUALIFIED
        new_stage = "QUALIFIED"
        qualified_at_clause = ", qualified_at = NOW()"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 3. Save detailed web audit if performed
            if audit_data:
                cur.execute(
                    """
                    INSERT INTO lead_web_audits (
                        lead_id, domain, url_checked, dns_resolved, ip_address, http_status_code,
                        redirect_count, final_url, has_ssl, ssl_valid, ssl_days_remaining,
                        ssl_issuer, is_self_signed, redirects_to_https, ttfb_ms, download_time_ms,
                        html_size_bytes, compression_type, has_viewport, viewport_content,
                        technologies, has_title, title_text, has_description, description_text,
                        h1_count, has_canonical, has_open_graph, has_schema_local_business,
                        has_google_analytics, has_google_tag_manager, has_meta_pixel, has_tiktok_pixel,
                        technical_health_score, acceptance_probability_pct, findings, audit_duration_seconds
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s
                    );
                    """,
                    (
                        lead_id, audit_data["domain"], audit_data["url_checked"],
                        audit_data["dns_resolved"], audit_data["ip_address"], audit_data["http_status_code"],
                        audit_data["redirect_count"], audit_data["final_url"], audit_data["has_ssl"],
                        audit_data["ssl_valid"], audit_data["ssl_days_remaining"], audit_data["ssl_issuer"],
                        audit_data["is_self_signed"], audit_data["redirects_to_https"], audit_data["ttfb_ms"],
                        audit_data["download_time_ms"], audit_data["html_size_bytes"], audit_data["compression_type"],
                        audit_data["has_viewport"], audit_data["viewport_content"],
                        json.dumps(audit_data["technologies"]), audit_data["has_title"], audit_data["title_text"],
                        audit_data["has_description"], audit_data["description_text"], audit_data["h1_count"],
                        audit_data["has_canonical"], audit_data["has_open_graph"], audit_data["has_schema_local_business"],
                        audit_data["has_google_analytics"], audit_data["has_google_tag_manager"],
                        audit_data["has_meta_pixel"], audit_data["has_tiktok_pixel"],
                        health_score, prob_pct, json.dumps(audit_data["findings"]),
                        audit_data["audit_duration_seconds"]
                    )
                )

            # 4. Update lead record with scores, arguments and pipeline stage
            update_sql = f"""
            UPDATE leads
            SET technical_health_score = %s,
                acceptance_probability_pct = %s,
                sales_arguments = %s,
                lifecycle_stage = %s,
                audited_at = NOW()
                {qualified_at_clause},
                updated_at = NOW()
            WHERE id = %s;
            """
            cur.execute(
                update_sql,
                (health_score, prob_pct, json.dumps(arguments), new_stage, lead_id)
            )

    return {
        "lead_id": lead_id,
        "name": lead["name"],
        "category_slug": lead["category_slug"],
        "has_dedicated_website": has_dedicated_web,
        "technical_health_score": health_score,
        "acceptance_probability_pct": prob_pct,
        "sales_arguments": arguments,
        "lifecycle_stage": new_stage
    }
