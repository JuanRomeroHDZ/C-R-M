import json
import logging
import re
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
from bs4 import BeautifulSoup
from src.db.connection import get_db_connection, execute_query

logger = logging.getLogger("crm.analysis.channel_enricher")

FALSE_POSITIVE_EMAILS = [
    r"@2x\.png$",
    r"@3x\.png$",
    r"@2x\.jpg$",
    r"@3x\.jpg$",
    r"\.webp$",
    r"\.svg$",
    r"^example@",
    r"@example\.com$",
    r"@domain\.com$",
    r"@email\.com$",
    r"@sentry\.io$",
    r"@wixpress\.com$",
    r"@w3\.org$",
    r"^user@",
    r"^test@"
]

SOCIAL_PATTERNS = {
    "facebook": [
        r"^https?://(www\.)?(facebook|fb)\.com/([^/?#]+)",
        r"^https?://(www\.)?facebook\.com/pages/[^/?#]+/(\d+)"
    ],
    "instagram": [
        r"^https?://(www\.)?instagram\.com/([^/?#]+)"
    ],
    "tiktok": [
        r"^https?://(www\.)?tiktok\.com/@([^/?#]+)"
    ],
    "linkedin": [
        r"^https?://(www\.)?linkedin\.com/(company|in)/([^/?#]+)"
    ],
    "youtube": [
        r"^https?://(www\.)?youtube\.com/(@[^/?#]+|channel/[^/?#]+|c/[^/?#]+|user/[^/?#]+)"
    ],
    "x": [
        r"^https?://(www\.)?(twitter|x)\.com/([^/?#]+)"
    ]
}

EXCLUDED_SOCIAL_PATHS = [
    "sharer",
    "sharer.php",
    "share",
    "intent/tweet",
    "plugins",
    "dialog/share",
    "tr?id=",
    "hashtag",
    "home.php",
    "login",
    "policies"
]


def extract_emails_from_html(html: str) -> List[str]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    found_emails = set()

    # 1. mailto: links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            raw_email = href[7:].split("?")[0].strip()
            if raw_email:
                found_emails.add(raw_email.lower())

    # 2. Regex scan on text
    text_content = soup.get_text(separator=" ")
    matches = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text_content)
    for m in matches:
        found_emails.add(m.lower())

    # 3. Filter false positives
    valid_emails = []
    for email in found_emails:
        is_false = False
        for fp in FALSE_POSITIVE_EMAILS:
            if re.search(fp, email, re.I):
                is_false = True
                break
        if not is_false and len(email) <= 100:
            valid_emails.append(email)

    return sorted(valid_emails)


def clean_social_url(url: str, platform: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip()

    # Check excluded paths
    for excluded in EXCLUDED_SOCIAL_PATHS:
        if excluded in url.lower():
            return None

    patterns = SOCIAL_PATTERNS.get(platform, [])
    for p in patterns:
        match = re.search(p, url, re.I)
        if match:
            # Clean protocol and trailing slash
            parsed = urllib.parse.urlparse(url)
            clean_path = parsed.path.rstrip("/")
            if platform in ("facebook", "x", "instagram") and clean_path in ("", "/", "/share", "/sharer.php"):
                return None
            return f"https://{parsed.netloc.lower()}{clean_path}"

    return None


def extract_social_links_from_html(html: str) -> Dict[str, str]:
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    social_links = {}

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        for platform in SOCIAL_PATTERNS.keys():
            if platform not in social_links:
                cleaned = clean_social_url(href, platform)
                if cleaned:
                    social_links[platform] = cleaned

    return social_links


def compute_channel_statuses(lead: Dict[str, Any]) -> Dict[str, str]:
    has_whatsapp_flag = lead.get("has_whatsapp", True)
    if has_whatsapp_flag is None:
        has_whatsapp_flag = True

    social_links = lead.get("social_links") or {}
    if isinstance(social_links, str):
        try:
            social_links = json.loads(social_links)
        except Exception:
            social_links = {}

    channels = {}

    # WhatsApp
    if not has_whatsapp_flag:
        channels["whatsapp"] = "DESCARTADO_MANUALMENTE"
    elif lead.get("phone_e164"):
        channels["whatsapp"] = "DISPONIBLE"
    else:
        channels["whatsapp"] = "NO_ENCONTRADO"

    # Phone
    if lead.get("phone_e164") or lead.get("phone_raw"):
        channels["phone"] = "DISPONIBLE"
    else:
        channels["phone"] = "NO_ENCONTRADO"

    # Website
    if lead.get("has_dedicated_website") and lead.get("website"):
        channels["website"] = "DISPONIBLE"
    else:
        channels["website"] = "NO_ENCONTRADO"

    # Email
    if lead.get("email"):
        channels["email"] = "DISPONIBLE"
    else:
        channels["email"] = "NO_ENCONTRADO"

    # Social platforms
    for plat in ("facebook", "instagram", "tiktok", "linkedin", "youtube", "x"):
        if plat in social_links and social_links[plat]:
            channels[plat] = "DISPONIBLE"
        else:
            channels[plat] = "NO_ENCONTRADO"

    return channels


def generate_whatsapp_url(phone_e164: Optional[str], template: str, lead_name: str = "") -> Optional[str]:
    if not phone_e164:
        return None

    clean_digits = re.sub(r"\D", "", phone_e164)
    if not clean_digits:
        return None

    # Replace template variables
    msg = template or "Hola, buen día."
    if "{nombre}" in msg:
        clean_name = re.sub(r"[^\w\s]", "", lead_name).strip() if lead_name else ""
        msg = msg.replace("{nombre}", clean_name).strip()

    encoded_msg = urllib.parse.quote(msg)
    return f"https://wa.me/{clean_digits}?text={encoded_msg}"


def enrich_lead_channels(lead_id: str) -> Dict[str, Any]:
    rows = execute_query(
        """
        SELECT l.id, l.name, l.phone_raw, l.phone_e164, l.has_whatsapp, l.website,
               l.has_dedicated_website, l.social_links, l.email,
               a.final_url, a.html_size_bytes
        FROM leads l
        LEFT JOIN lead_web_audits a ON a.lead_id = l.id
        WHERE l.id = %s AND l.is_deleted = FALSE;
        """,
        (lead_id,)
    )
    if not rows:
        return {}

    lead = rows[0]
    existing_social = lead.get("social_links") or {}
    if isinstance(existing_social, str):
        try:
            existing_social = json.loads(existing_social)
        except Exception:
            existing_social = {}

    current_email = lead.get("email")

    # If audit exists and website has dedicated domain, we can check if email or additional socials are present
    channel_status = compute_channel_statuses({
        **lead,
        "email": current_email,
        "social_links": existing_social
    })

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET channels_status = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (json.dumps(channel_status), lead_id)
            )

    return {
        "lead_id": lead_id,
        "email": current_email,
        "social_links": existing_social,
        "channels_status": channel_status
    }


def enrich_all_leads():
    rows = execute_query("SELECT id FROM leads WHERE is_deleted = FALSE;")
    count = 0
    for r in rows:
        enrich_lead_channels(str(r["id"]))
        count += 1
    logger.info(f"Enriched channels for {count} leads.")
    return count
