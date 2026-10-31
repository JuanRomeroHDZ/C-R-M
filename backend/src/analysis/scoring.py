import logging
from typing import Dict, Any, Optional, Tuple, List
from src.analysis.config_scoring import scoring_config

logger = logging.getLogger("crm.analysis.scoring")


def calculate_technical_health_score(
    audit: Optional[Dict[str, Any]],
    has_dedicated_website: bool
) -> float:
    if not has_dedicated_website or not audit:
        return 0.0

    if not audit.get("dns_resolved") or audit.get("is_parking_domain"):
        return 0.0

    status_code = audit.get("http_status_code")
    if not status_code or status_code >= 400:
        return 0.0

    score = 100.0

    # 1. SSL/TLS & HTTPS
    if not audit.get("has_ssl") or not audit.get("ssl_valid"):
        score -= 30.0
    elif audit.get("ssl_days_remaining") is not None and audit.get("ssl_days_remaining") <= 15:
        score -= 10.0

    if not audit.get("redirects_to_https") and audit.get("has_ssl"):
        score -= 10.0

    # 2. Performance (TTFB)
    ttfb = audit.get("ttfb_ms")
    if ttfb is not None:
        if ttfb > 1200.0:
            score -= 15.0
        elif ttfb > 600.0:
            score -= 8.0

    # 3. Mobile Viewport
    if not audit.get("has_viewport"):
        score -= 25.0

    # 4. Compression
    if not audit.get("compression_type"):
        score -= 5.0

    # 5. Core SEO
    if not audit.get("has_title"):
        score -= 10.0
    if not audit.get("has_description"):
        score -= 10.0
    if audit.get("h1_count", 0) == 0:
        score -= 5.0

    # 6. Open Graph & Schema.org
    if not audit.get("has_open_graph"):
        score -= 5.0
    if not audit.get("has_schema_local_business"):
        score -= 10.0

    # 7. Pixels
    if not audit.get("has_google_analytics") and not audit.get("has_meta_pixel"):
        score -= 10.0

    return max(0.0, min(100.0, round(score, 1)))


def calculate_acceptance_probability(
    lead: Dict[str, Any],
    audit: Optional[Dict[str, Any]],
    health_score: float
) -> Tuple[float, List[str]]:
    prob = scoring_config.BASE_ACCEPTANCE_PROBABILITY
    arguments: List[str] = []

    # 1. Commercial Traction Evaluation
    reviews = lead.get("review_count") or 0
    rating = float(lead.get("rating") or 0.0)
    has_phone = bool(lead.get("phone_e164") or lead.get("phone_raw"))
    has_dedicated_web = bool(lead.get("has_dedicated_website"))

    if reviews >= scoring_config.TRACTION_REVIEWS_HIGH:
        prob += scoring_config.TRACTION_WEIGHT_HIGH
        arguments.append(f"Alta popularidad ({reviews} opiniones con flujo constante de clientes)")
    elif reviews >= scoring_config.TRACTION_REVIEWS_MED:
        prob += scoring_config.TRACTION_WEIGHT_MED
        arguments.append(f"Actividad comercial activa ({reviews} opiniones)")
    elif reviews >= scoring_config.TRACTION_REVIEWS_LOW:
        prob += scoring_config.TRACTION_WEIGHT_LOW

    if rating >= scoring_config.TRACTION_RATING_THRESHOLD and reviews >= 3:
        prob += scoring_config.TRACTION_WEIGHT_RATING
        arguments.append(f"Excelente reputacion ({rating} estrellas de calificacion)")
    elif rating > 0.0 and rating < 3.0:
        prob += scoring_config.RESISTANCE_PENALTY_POOR_RATING

    if has_phone:
        prob += scoring_config.CONTACT_WEIGHT_VALID_PHONE
    else:
        prob += scoring_config.RESISTANCE_PENALTY_NO_PHONE
        arguments.append("Atención: Sin línea telefónica directa detectada")

    if reviews == 0:
        prob += scoring_config.RESISTANCE_PENALTY_ZERO_REVIEWS

    # 2. Digital Pain Points Evaluation
    if not has_dedicated_web:
        prob += scoring_config.PAIN_WEIGHT_NO_DEDICATED_SITE
        social_links = lead.get("social_links") or {}
        if isinstance(social_links, str):
            import json
            try:
                social_links = json.loads(social_links)
            except Exception:
                social_links = {}

        if social_links:
            platforms = ", ".join(k.capitalize() for k in social_links.keys())
            arguments.append(f"Sin sitio web propio: solo tiene perfiles en {platforms}")
        else:
            arguments.append("Sin sitio web propio ni presencia digital centralizada")
        arguments.append("Oportunidad directa para propuesta de presencia digital y captacion")

    else:
        # Business has a dedicated website, evaluate audit findings
        if audit:
            if not audit.get("has_ssl") or not audit.get("ssl_valid"):
                prob += scoring_config.PAIN_WEIGHT_SSL_INVALID_OR_EXPIRED
                arguments.append("Sitio no seguro (Sin candado para los visitantes)")

            status_code = audit.get("http_status_code")
            if status_code and status_code >= 400:
                prob += scoring_config.PAIN_WEIGHT_HTTP_ERROR
                arguments.append("Página caída o rota (Los clientes no pueden abrirla)")

            if not audit.get("has_viewport"):
                prob += scoring_config.PAIN_WEIGHT_NO_VIEWPORT
                arguments.append("No se adapta a celulares (Pierde clientes que navegan en móvil)")

            ttfb = audit.get("ttfb_ms")
            if ttfb and ttfb > 1000.0:
                prob += scoring_config.PAIN_WEIGHT_SLOW_TTFB
                arguments.append("Carga lenta (Tarda demasiado en abrir)")

            if not audit.get("has_google_analytics") and not audit.get("has_meta_pixel"):
                prob += scoring_config.PAIN_WEIGHT_NO_PIXELS
                arguments.append("Sin rastreo de anuncios ni visitas (Pierde oportunidades de venta)")

            if not audit.get("has_schema_local_business"):
                prob += scoring_config.PAIN_WEIGHT_NO_SCHEMA_LOCAL
                arguments.append("Mal posicionado en buscadores (Dificil de encontrar en internet)")

    # Unclaimed business on Google Maps
    if lead.get("is_claimed") is False:
        prob += scoring_config.PAIN_WEIGHT_UNCLAIMED_BUSINESS
        arguments.append("Ficha comercial no verificada en mapas (oportunidad de servicio de gestion)")

    # 3. Technical Resistance Factors
    if health_score >= 85.0:
        prob += scoring_config.RESISTANCE_PENALTY_EXCELLENT_SITE
        arguments.append("Ya cuenta con pagina moderna y optimizada (baja necesidad de cambio)")
    elif health_score >= 70.0:
        prob += scoring_config.RESISTANCE_PENALTY_GOOD_SITE
        arguments.append("Sitio web en condiciones aceptables")

    final_prob = max(0.0, min(100.0, round(prob, 1)))
    return final_prob, arguments
