import json
import logging
import math
import re
import unicodedata
import urllib.parse
from typing import Optional, Tuple, Dict, Any, List
from rapidfuzz import fuzz
from src.db.connection import get_db_connection, execute_query

logger = logging.getLogger("crm.analysis.deduplication")

# Recognized social platforms and directory platforms
SOCIAL_DOMAINS = {
    "facebook": ["facebook.com", "fb.com", "fb.me", "m.facebook.com"],
    "instagram": ["instagram.com", "instagr.am"],
    "whatsapp": ["wa.me", "whatsapp.com", "api.whatsapp.com"],
    "linktree": ["linktr.ee", "linktree.com"],
    "doctoralia": ["doctoralia.com.mx", "doctoralia.com"],
    "google_site": ["sites.google.com"],
    "linkedin": ["linkedin.com"],
    "tiktok": ["tiktok.com"],
    "twitter": ["twitter.com", "x.com"],
    "youtube": ["youtube.com", "youtu.be"]
}

# Legal suffixes to remove in commercial name normalization
LEGAL_REGIMES = [
    r"\bs\.?a\.?\s*de\s*c\.?v\.?\b",
    r"\bs\.?c\.?\b",
    r"\bs\.?\s*de\s*r\.?l\.?\s*(de\s*c\.?v\.?)?\b",
    r"\bs\.?a\.?p\.?i\.?\s*(de\s*c\.?v\.?)?\b",
    r"\binc\.?\b",
    r"\bllc\.?\b",
    r"\bltd\.?\b"
]

# Generic noise words in commercial names
GENERIC_NOISE_WORDS = [
    r"\bconsultorio\s*dental\b",
    r"\bclinica\s*dental\b",
    r"\bcirujano\s*dentista\b",
    r"\bdentista\b",
    r"\bodontologia\b",
    r"\bdental\b",
    r"\bdr\.?\b",
    r"\bdra\.?\b",
    r"\bdoctor\b",
    r"\bdoctora\b",
    r"\bdespacho\s*contable\b",
    r"\bdespacho\s*fiscal\b",
    r"\bcontador\s*publico\b",
    r"\bcontadores\s*publicos\b",
    r"\basesoria\s*fiscal\b",
    r"\bconsultoria\s*fiscal\b",
    r"\bcontabilidad\b",
    r"\bauditoria\s*contable\b",
    r"\bcorporativo\b",
    r"\basociados\b"
]

US_BORDER_AREA_CODES = {"619", "858", "760", "949", "818", "310", "213"}


def normalize_phone_e164(raw_phone: Optional[str]) -> Tuple[Optional[str], Optional[str], bool]:
    if not raw_phone:
        return None, None, False

    cleaned = re.sub(r"[^\d+]", "", raw_phone)
    if not cleaned:
        return None, None, False

    # Case 1: Starts with +
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if digits.startswith("52"):
            # Mexican number
            num_part = digits[2:]
            if num_part.startswith("1") and len(num_part) == 11:
                # Remove obsolete mobile '1' prefix
                num_part = num_part[1:]
            if len(num_part) == 10:
                return f"+52{num_part}", "MX", True
            return f"+52{num_part}", "MX", False

        if digits.startswith("1"):
            # US number
            num_part = digits[1:]
            if len(num_part) == 10:
                return f"+1{num_part}", "US", True
            return f"+1{num_part}", "US", False

        return cleaned, "OTHER", len(digits) >= 8

    # Case 2: No leading +
    digits = re.sub(r"\D", "", cleaned)

    # Remove Mexican obsolete long distance prefixes
    if digits.startswith("044") or digits.startswith("045"):
        digits = digits[3:]
    elif digits.startswith("01") and len(digits) == 12:
        digits = digits[2:]

    # Check 10-digit number
    if len(digits) == 10:
        area_code = digits[:3]
        if area_code in US_BORDER_AREA_CODES:
            return f"+1{digits}", "US", True
        return f"+52{digits}", "MX", True

    # 11 digits starting with 1
    if len(digits) == 11 and digits.startswith("1"):
        return f"+1{digits[1:]}", "US", True

    # 12 digits starting with 52
    if len(digits) == 12 and digits.startswith("52"):
        return f"+52{digits[2:]}", "MX", True

    # 13 digits starting with 521
    if len(digits) == 13 and digits.startswith("521"):
        return f"+52{digits[3:]}", "MX", True

    return None, None, False


def normalize_domain_and_social(raw_url: Optional[str]) -> Tuple[Optional[str], Optional[str], bool, Dict[str, str]]:
    if not raw_url:
        return None, None, False, {}

    url = raw_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]

        # Strip www.
        if netloc.startswith("www."):
            netloc = netloc[4:]

        if not netloc or "." not in netloc:
            return None, None, False, {}

        detected_social = {}
        for platform, domains in SOCIAL_DOMAINS.items():
            for d in domains:
                if netloc == d or netloc.endswith("." + d):
                    detected_social[platform] = raw_url.strip()
                    # It is a social profile or directory, not a dedicated website
                    return None, None, False, detected_social

        # Clean dedicated website
        clean_url = f"https://{netloc}/"
        return clean_url, netloc, True, {}

    except Exception:
        return None, None, False, {}


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_commercial_name(name: str) -> str:
    if not name:
        return ""
    text = name.lower()
    text = strip_accents(text)

    # Remove legal regimes
    for pattern in LEGAL_REGIMES:
        text = re.sub(pattern, " ", text)

    # Remove generic noise words
    for pattern in GENERIC_NOISE_WORDS:
        text = re.sub(pattern, " ", text)

    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def normalize_lead_record(lead_id: str) -> Dict[str, Any]:
    rows = execute_query(
        "SELECT id, phone_raw, website, social_links, is_deleted FROM leads WHERE id = %s;",
        (lead_id,)
    )
    if not rows or rows[0]["is_deleted"]:
        return {}

    lead = rows[0]
    phone_e164, country, is_valid = normalize_phone_e164(lead.get("phone_raw"))
    clean_web, domain, has_dedicated, new_social = normalize_domain_and_social(lead.get("website"))

    existing_social = lead.get("social_links") or {}
    if isinstance(existing_social, str):
        try:
            existing_social = json.loads(existing_social)
        except Exception:
            existing_social = {}
    merged_social = {**existing_social, **new_social}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET phone_e164 = %s,
                    phone_country = %s,
                    phone_valid = %s,
                    website = %s,
                    normalized_domain = %s,
                    has_dedicated_website = %s,
                    social_links = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (
                    phone_e164,
                    country,
                    is_valid,
                    clean_web,
                    domain,
                    has_dedicated,
                    json.dumps(merged_social),
                    lead_id
                )
            )

    return {
        "id": lead_id,
        "phone_e164": phone_e164,
        "normalized_domain": domain,
        "has_dedicated_website": has_dedicated,
        "social_links": merged_social
    }


def normalize_all_leads():
    rows = execute_query("SELECT id FROM leads WHERE is_deleted = FALSE;")
    count = 0
    for r in rows:
        normalize_lead_record(str(r["id"]))
        count += 1
    logger.info(f"Normalized {count} leads in database.")
    return count


def merge_two_leads(master_id: str, duplicate_id: str, reason: str, score: float):
    master_rows = execute_query("SELECT * FROM leads WHERE id = %s AND is_deleted = FALSE;", (master_id,))
    duplicate_rows = execute_query("SELECT * FROM leads WHERE id = %s AND is_deleted = FALSE;", (duplicate_id,))

    if not master_rows or not duplicate_rows:
        return

    m = master_rows[0]
    d = duplicate_rows[0]

    # Consolidate fields
    best_phone = m.get("phone_e164") or d.get("phone_e164")
    best_raw_phone = m.get("phone_raw") or d.get("phone_raw")
    best_web = m.get("website") or d.get("website")
    best_domain = m.get("normalized_domain") or d.get("normalized_domain")
    has_dedicated = m.get("has_dedicated_website") or d.get("has_dedicated_website") or False

    best_lat = m.get("latitude") if m.get("latitude") is not None else d.get("latitude")
    best_lon = m.get("longitude") if m.get("longitude") is not None else d.get("longitude")

    best_rating = max(m.get("rating") or 0.0, d.get("rating") or 0.0)
    best_reviews = max(m.get("review_count") or 0, d.get("review_count") or 0)

    # Merge social links
    m_social = m.get("social_links") or {}
    d_social = d.get("social_links") or {}
    merged_social = {**d_social, **m_social}

    # Merge metadata
    m_meta = m.get("extra_metadata") or {}
    d_meta = d.get("extra_metadata") or {}
    merged_meta = {**d_meta, **m_meta, "merged_record_id": duplicate_id}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Update master
            cur.execute(
                """
                UPDATE leads
                SET phone_e164 = %s,
                    phone_raw = %s,
                    website = %s,
                    normalized_domain = %s,
                    has_dedicated_website = %s,
                    latitude = %s,
                    longitude = %s,
                    rating = %s,
                    review_count = %s,
                    social_links = %s,
                    extra_metadata = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (
                    best_phone,
                    best_raw_phone,
                    best_web,
                    best_domain,
                    has_dedicated,
                    best_lat,
                    best_lon,
                    best_rating if best_rating > 0 else None,
                    best_reviews,
                    json.dumps(merged_social),
                    json.dumps(merged_meta),
                    master_id
                )
            )

            # 2. Soft-delete duplicate
            cur.execute(
                """
                UPDATE leads
                SET is_deleted = TRUE,
                    deleted_at = NOW(),
                    extra_metadata = extra_metadata || %s::jsonb
                WHERE id = %s;
                """,
                (json.dumps({"merged_into": master_id, "merge_reason": reason}), duplicate_id)
            )

            # 3. Insert deduplication history
            cur.execute(
                """
                INSERT INTO deduplication_history (
                    master_lead_id, merged_lead_id, merge_reason, similarity_score, details
                ) VALUES (%s, %s, %s, %s, %s);
                """,
                (master_id, duplicate_id, reason, score, json.dumps({"duplicate_name": d["name"]}))
            )

    logger.info(f"Merged duplicate {duplicate_id} into master {master_id} (Reason: {reason})")


def run_multilayer_deduplication(category_slug: Optional[str] = None) -> Dict[str, Any]:
    # First normalize all active records
    normalize_all_leads()

    sql = "SELECT id, name, category_slug, phone_e164, normalized_domain, latitude, longitude, created_at FROM leads WHERE is_deleted = FALSE"
    params = []
    if category_slug:
        sql += " AND category_slug = %s"
        params.append(category_slug)
    sql += " ORDER BY created_at ASC;"

    leads = execute_query(sql, tuple(params))
    merged_count = 0
    deleted_ids = set()

    for i in range(len(leads)):
        l1 = leads[i]
        id1 = str(l1["id"])
        if id1 in deleted_ids:
            continue

        for j in range(i + 1, len(leads)):
            l2 = leads[j]
            id2 = str(l2["id"])
            if id2 in deleted_ids:
                continue

            reason = None
            score = 1.0

            # Capa 1: Phone match
            if l1["phone_e164"] and l2["phone_e164"] and l1["phone_e164"] == l2["phone_e164"]:
                reason = "PHONE_E164"
                score = 1.0

            # Capa 2: Domain match
            elif l1["normalized_domain"] and l2["normalized_domain"] and l1["normalized_domain"] == l2["normalized_domain"]:
                reason = "DOMAIN"
                score = 1.0

            # Capa 3: Lexical similarity + Geographic proximity
            else:
                if l1["latitude"] is not None and l1["longitude"] is not None and l2["latitude"] is not None and l2["longitude"] is not None:
                    dist_meters = haversine_distance_meters(
                        l1["latitude"], l1["longitude"],
                        l2["latitude"], l2["longitude"]
                    )
                    if dist_meters <= 50.0:
                        clean_n1 = clean_commercial_name(l1["name"])
                        clean_n2 = clean_commercial_name(l2["name"])
                        sim = fuzz.token_sort_ratio(clean_n1, clean_n2) / 100.0
                        if sim >= 0.85:
                            reason = "FUZZY_NAME_AND_DISTANCE"
                            score = round(sim, 4)

            if reason:
                # Merge l2 into l1
                merge_two_leads(id1, id2, reason, score)
                deleted_ids.add(id2)
                merged_count += 1

    return {
        "processed_leads": len(leads),
        "merged_count": merged_count,
        "remaining_unique_leads": len(leads) - merged_count
    }
