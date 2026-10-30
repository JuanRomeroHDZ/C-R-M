import html
import re
import urllib.parse
from typing import Optional

ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}
DANGEROUS_PROTOCOLS = {"javascript", "data", "vbscript", "file"}


def sanitize_text(text: Optional[str]) -> str:
    """Sanitize free text input by stripping control chars and escaping HTML."""
    if not text:
        return ""
    # Strip null bytes and non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Strip dangerous HTML tags
    cleaned = html.escape(cleaned.strip(), quote=True)
    return cleaned


def validate_redirect_url(url: Optional[str]) -> bool:
    """Validate URL schemes strictly, allowing only http, https, mailto, tel."""
    if not url:
        return False
    url_clean = url.strip()
    # Check lowercase protocol before parsing
    lower_url = url_clean.lower()
    for proto in DANGEROUS_PROTOCOLS:
        if lower_url.startswith(f"{proto}:"):
            return False

    try:
        parsed = urllib.parse.urlparse(url_clean)
        scheme = parsed.scheme.lower()
        if scheme not in ALLOWED_SCHEMES:
            return False
        return True
    except Exception:
        return False


def clean_phone_number(raw_phone: Optional[str]) -> str:
    """Extract digits and optional leading plus sign from phone string."""
    if not raw_phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", raw_phone)
    return cleaned
