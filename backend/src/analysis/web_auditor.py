import ipaddress
import json
import logging
import re
import socket
import ssl
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger("crm.analysis.web_auditor")

PARKING_PATTERNS = [
    r"\bdomain\s+(is\s+)?for\s+sale\b",
    r"\bbuy\s+this\s+domain\b",
    r"\bparking\s+page\b",
    r"\bparked\s+domain\b",
    r"\bdominio\s+en\s+venta\b",
    r"\bsedo\s+domain\s+parking\b",
    r"\bgodaddy\b.*\bparking\b",
    r"\bhugedomains\b"
]


class SecuritySSRFException(Exception):
    pass


def validate_ip_address_not_private(ip_str: str):
    ip_obj = ipaddress.ip_address(ip_str)
    if (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or ip_obj.is_multicast
    ):
        raise SecuritySSRFException(f"Destination IP {ip_str} is in a forbidden private/loopback range.")


def resolve_domain_safe(hostname: str) -> str:
    try:
        addr_info = socket.getaddrinfo(hostname, 80, socket.AF_INET, socket.SOCK_STREAM)
        if not addr_info:
            raise ValueError(f"Could not resolve host {hostname}")
        ip = addr_info[0][4][0]
        validate_ip_address_not_private(ip)
        return ip
    except socket.gaierror as e:
        raise ValueError(f"DNS resolution error for {hostname}: {e}")


def inspect_ssl_certificate(hostname: str, port: int = 443) -> Dict[str, Any]:
    ssl_data = {
        "has_ssl": False,
        "ssl_valid": False,
        "ssl_days_remaining": None,
        "ssl_issuer": None,
        "is_self_signed": False,
        "protocol": None,
        "error": None
    }

    try:
        ip = resolve_domain_safe(hostname)
    except Exception as e:
        ssl_data["error"] = str(e)
        return ssl_data

    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    try:
        with socket.create_connection((ip, port), timeout=4.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                ssl_data["has_ssl"] = True
                ssl_data["ssl_valid"] = True
                ssl_data["protocol"] = ssock.version()

                # Issuer
                issuer_dict = dict(x[0] for x in cert.get("issuer", ()))
                ssl_data["ssl_issuer"] = issuer_dict.get("organizationName") or issuer_dict.get("commonName")

                # Self-signed check
                subject_dict = dict(x[0] for x in cert.get("subject", ()))
                if issuer_dict == subject_dict:
                    ssl_data["is_self_signed"] = True

                # Expiration calculation
                not_after_str = cert.get("notAfter")
                if not_after_str:
                    not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_left = (not_after - datetime.now(timezone.utc)).days
                    ssl_data["ssl_days_remaining"] = days_left
                    if days_left < 0:
                        ssl_data["ssl_valid"] = False

    except ssl.SSLCertVerificationError as cert_err:
        ssl_data["has_ssl"] = True
        ssl_data["ssl_valid"] = False
        ssl_data["error"] = f"SSL Verification Failed: {cert_err.verify_message}"
    except Exception as err:
        ssl_data["error"] = f"SSL Connection Error: {type(err).__name__}"

    return ssl_data


class TechnicalWebAuditor:
    def __init__(self, user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) CRM-Web-Auditor/1.0"):
        self.user_agent = user_agent
        self.max_body_bytes = 2 * 1024 * 1024  # 2 MB limit for DoS protection

    async def audit_lead_website(self, lead_id: str, website_url: str) -> Dict[str, Any]:
        start_ts = time.time()
        audit_result = {
            "lead_id": lead_id,
            "domain": "",
            "url_checked": website_url,
            "dns_resolved": False,
            "ip_address": None,
            "http_status_code": None,
            "redirect_count": 0,
            "final_url": None,
            "has_ssl": False,
            "ssl_valid": False,
            "ssl_days_remaining": None,
            "ssl_issuer": None,
            "is_self_signed": False,
            "redirects_to_https": False,
            "ttfb_ms": None,
            "download_time_ms": None,
            "html_size_bytes": 0,
            "compression_type": None,
            "has_viewport": False,
            "viewport_content": None,
            "technologies": [],
            "has_title": False,
            "title_text": None,
            "has_description": False,
            "description_text": None,
            "h1_count": 0,
            "has_canonical": False,
            "has_open_graph": False,
            "has_schema_local_business": False,
            "has_google_analytics": False,
            "has_google_tag_manager": False,
            "has_meta_pixel": False,
            "has_tiktok_pixel": False,
            "is_parking_domain": False,
            "findings": [],
            "technical_health_score": 0.0,
            "acceptance_probability_pct": 0.0,
            "audit_duration_seconds": 0.0
        }

        parsed_initial = urllib.parse.urlparse(website_url)
        hostname = parsed_initial.netloc or parsed_initial.path
        if ":" in hostname:
            hostname = hostname.split(":")[0]
        audit_result["domain"] = hostname

        # 1. DNS Resolution & SSRF Validation
        try:
            ip_str = resolve_domain_safe(hostname)
            audit_result["dns_resolved"] = True
            audit_result["ip_address"] = ip_str
        except Exception as dns_err:
            audit_result["findings"].append(f"Falla de resolución DNS para el dominio: {dns_err}")
            audit_result["audit_duration_seconds"] = round(time.time() - start_ts, 3)
            return audit_result

        # 2. SSL/TLS Deep Inspection
        ssl_info = inspect_ssl_certificate(hostname)
        audit_result["has_ssl"] = ssl_info["has_ssl"]
        audit_result["ssl_valid"] = ssl_info["ssl_valid"]
        audit_result["ssl_days_remaining"] = ssl_info["ssl_days_remaining"]
        audit_result["ssl_issuer"] = ssl_info["ssl_issuer"]
        audit_result["is_self_signed"] = ssl_info["is_self_signed"]

        if not ssl_info["has_ssl"]:
            audit_result["findings"].append("El sitio web no cuenta con certificado SSL/TLS (inseguro)")
        elif not ssl_info["ssl_valid"]:
            audit_result["findings"].append("Certificado SSL inválido o expirado (navegadores muestran alerta de seguridad)")
        elif ssl_info["ssl_days_remaining"] is not None and ssl_info["ssl_days_remaining"] <= 15:
            audit_result["findings"].append(f"Certificado SSL por expirar en {ssl_info['ssl_days_remaining']} días")

        # 3. HTTP Request with Redirect & SSRF Tracking
        target_url = f"http://{hostname}/"
        redirect_history = []
        html_content = ""

        try:
            current_url = target_url
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br"
            }

            async with httpx.AsyncClient(timeout=8.0, follow_redirects=False) as client:
                hops = 0
                max_hops = 5

                while hops < max_hops:
                    p = urllib.parse.urlparse(current_url)
                    cur_host = p.netloc.split(":")[0]
                    # Validate each hop for SSRF
                    resolve_domain_safe(cur_host)

                    t0 = time.time()
                    resp = await client.get(current_url, headers=headers)
                    ttfb = round((time.time() - t0) * 1000.0, 2)
                    if audit_result["ttfb_ms"] is None:
                        audit_result["ttfb_ms"] = ttfb

                    redirect_history.append((current_url, resp.status_code))

                    if resp.is_redirect and "location" in resp.headers:
                        loc = resp.headers["location"]
                        current_url = urllib.parse.urljoin(current_url, loc)
                        hops += 1
                    else:
                        audit_result["http_status_code"] = resp.status_code
                        audit_result["final_url"] = current_url
                        audit_result["download_time_ms"] = round((time.time() - start_ts) * 1000.0, 2)
                        audit_result["compression_type"] = resp.headers.get("content-encoding")

                        # Read stream with body limit
                        body_bytes = resp.content[:self.max_body_bytes]
                        audit_result["html_size_bytes"] = len(body_bytes)
                        html_content = body_bytes.decode("utf-8", errors="ignore")
                        break

                audit_result["redirect_count"] = hops
                if audit_result["final_url"] and audit_result["final_url"].startswith("https://"):
                    audit_result["redirects_to_https"] = True
                elif audit_result["has_ssl"]:
                    audit_result["findings"].append("El sitio no redirige automáticamente de HTTP a HTTPS")

        except Exception as req_err:
            audit_result["findings"].append(f"Error en conexión HTTP: {type(req_err).__name__}")
            audit_result["audit_duration_seconds"] = round(time.time() - start_ts, 3)
            return audit_result

        # Check HTTP Status Code
        status_code = audit_result["http_status_code"]
        if status_code and status_code >= 400:
            audit_result["findings"].append(f"El sitio web responde con código de error HTTP {status_code}")
            audit_result["audit_duration_seconds"] = round(time.time() - start_ts, 3)
            return audit_result

        # 4. Check for Parking Domain
        lower_html = html_content.lower()
        for p in PARKING_PATTERNS:
            if re.search(p, lower_html):
                audit_result["is_parking_domain"] = True
                audit_result["findings"].append("Página de estacionamiento detectada (dominio sin uso o en venta)")
                break

        # 5. DOM Inspection via BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Viewport check
        vp_tag = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
        if vp_tag and vp_tag.get("content"):
            audit_result["has_viewport"] = True
            audit_result["viewport_content"] = str(vp_tag["content"]).strip()
        else:
            audit_result["findings"].append("Sin etiqueta meta viewport (sitio no optimizado para dispositivos móviles)")

        # Title & Meta Description
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()
            if len(title_text) > 0:
                audit_result["has_title"] = True
                audit_result["title_text"] = title_text[:200]
        if not audit_result["has_title"]:
            audit_result["findings"].append("Falta título en la página principal (<title>)")

        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if desc_tag and desc_tag.get("content"):
            desc_text = str(desc_tag["content"]).strip()
            if len(desc_text) > 0:
                audit_result["has_description"] = True
                audit_result["description_text"] = desc_text[:300]
        if not audit_result["has_description"]:
            audit_result["findings"].append("Falta meta descripción para posicionamiento en Google")

        # H1 check
        h1_tags = soup.find_all("h1")
        audit_result["h1_count"] = len(h1_tags)
        if len(h1_tags) == 0:
            audit_result["findings"].append("Sin encabezado principal <h1> para estructura SEO")

        # Canonical
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag and canonical_tag.get("href"):
            audit_result["has_canonical"] = True

        # Open Graph
        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_image = soup.find("meta", attrs={"property": "og:image"})
        if og_title or og_image:
            audit_result["has_open_graph"] = True
        else:
            audit_result["findings"].append("Sin etiquetas Open Graph para visualización enriquecida en WhatsApp y redes")

        # Schema.org JSON-LD LocalBusiness check
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "")
                types_found = []
                if isinstance(data, dict):
                    types_found.append(str(data.get("@type", "")))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            types_found.append(str(item.get("@type", "")))

                local_keywords = ["LocalBusiness", "Dentist", "AccountingService", "MedicalBusiness", "ProfessionalService"]
                if any(any(lk in t for lk in local_keywords) for t in types_found):
                    audit_result["has_schema_local_business"] = True
                    break
            except Exception:
                continue

        if not audit_result["has_schema_local_business"]:
            audit_result["findings"].append("Sin datos estructurados Schema.org para SEO local en Google")

        # 6. Tracking Pixels & Analytics Detection
        if re.search(r"G-[A-Z0-9]{6,12}", html_content) or "gtag(" in html_content:
            audit_result["has_google_analytics"] = True

        if re.search(r"GTM-[A-Z0-9]{5,10}", html_content):
            audit_result["has_google_tag_manager"] = True

        if "fbq(" in html_content or "connect.facebook.net" in html_content:
            audit_result["has_meta_pixel"] = True

        if "ttq.load(" in html_content or "analytics.tiktok.com" in html_content:
            audit_result["has_tiktok_pixel"] = True

        if not (audit_result["has_google_analytics"] or audit_result["has_meta_pixel"]):
            audit_result["findings"].append("Sin píxeles de captación ni herramientas de analítica (sin Meta Pixel ni Google Analytics)")

        # 7. Technology Fingerprinting
        techs = []
        if "wp-content" in html_content or "wp-includes" in html_content:
            techs.append("WordPress")
        if "wix.com" in html_content or "wixstatic.com" in html_content:
            techs.append("Wix")
        if "squarespace.com" in html_content:
            techs.append("Squarespace")
        if "cdn.shopify.com" in html_content:
            techs.append("Shopify")
        if "webflow.com" in html_content:
            techs.append("Webflow")
        if "joomla" in lower_html:
            techs.append("Joomla")
        audit_result["technologies"] = techs

        # Check slow TTFB
        if audit_result["ttfb_ms"] and audit_result["ttfb_ms"] > 1000.0:
            audit_result["findings"].append(f"Tiempo de respuesta inicial lento: {audit_result['ttfb_ms']} ms")

        audit_result["audit_duration_seconds"] = round(time.time() - start_ts, 3)
        return audit_result
