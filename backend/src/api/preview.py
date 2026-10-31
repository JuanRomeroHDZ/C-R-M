import ipaddress
import logging
import re
import socket
import urllib.parse
import httpx
from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import HTMLResponse

logger = logging.getLogger("crm.api.preview")
router = APIRouter(prefix="/api/v1/preview", tags=["Preview"])

PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_ssrf_safe(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if not host:
            return False
        
        # Check against string matches
        if host.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "crm_backend", "crm_frontend", "crm_postgres", "crm_redis", "crm_proxy"):
            return False

        try:
            ip = ipaddress.ip_address(host)
            for net in PRIVATE_NETWORKS:
                if ip in net:
                    return False
        except ValueError:
            # Host is a domain name, resolve IPs
            try:
                addr_info = socket.getaddrinfo(host, None)
                for item in addr_info:
                    ip_str = item[4][0]
                    ip = ipaddress.ip_address(ip_str)
                    for net in PRIVATE_NETWORKS:
                        if ip in net:
                            return False
            except Exception:
                # If resolution fails, let httpx try or return False
                pass

        return True
    except Exception as e:
        logger.warning(f"SSRF validation exception for {url}: {e}")
        return False


def _neutralize_framebusting(html: str) -> str:
    # Neutralize JS attempts to escape iframe
    patterns = [
        (r'(?i)(top|parent|window\.top|window\.parent)\.location\.replace\s*\(', 'console.warn('),
        (r'(?i)(top|parent|window\.top|window\.parent)\.location\.href\s*=', 'window.self.location.href ='),
        (r'(?i)(top|parent|window\.top|window\.parent)\.location\s*=', 'window.self.location ='),
        (r'(?i)if\s*\(\s*(top|parent|window\.top)\s*!==\s*(self|window)\s*\)\s*\{[^}]*\}', '// neutralized framebuster'),
        (r'(?i)if\s*\(\s*(top|parent|window\.top)\.location\s*!==?\s*(self|window)\.location\s*\)\s*\{[^}]*\}', '// neutralized framebuster'),
    ]
    for pattern, replacement in patterns:
        html = re.sub(pattern, replacement, html)
    return html


def _build_error_page(url: str, message: str) -> str:
    safe_url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Vista previa no disponible</title>
  <style>
    body {{
      background-color: #12151c;
      color: #94a3b8;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 80vh;
      margin: 0;
      padding: 24px;
      text-align: center;
    }}
    .box {{
      max-width: 480px;
      background: #181c26;
      border: 1px solid #232936;
      border-radius: 8px;
      padding: 32px 24px;
    }}
    h2 {{
      color: #f1f5f9;
      font-size: 1.1rem;
      font-weight: 600;
      margin: 0 0 12px 0;
    }}
    p {{
      font-size: 0.875rem;
      line-height: 1.5;
      margin: 0 0 20px 0;
      color: #94a3b8;
    }}
    .btn {{
      display: inline-block;
      padding: 8px 16px;
      background: #2563eb;
      color: #ffffff;
      text-decoration: none;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 500;
    }}
  </style>
</head>
<body>
  <div class="box">
    <h2>Vista previa enmarcada no disponible</h2>
    <p>{message}</p>
    <a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="btn">Abrir en pestaña externa</a>
  </div>
</body>
</html>"""


@router.get("/proxy")
async def proxy_website(url: str = Query(..., description="URL to proxy and preview inside iframe")):
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if not _is_ssrf_safe(url):
        return HTMLResponse(
            content=_build_error_page(url, "La dirección solicitada no está permitida por políticas de seguridad de red."),
            status_code=400
        )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
    }

    try:
        async with httpx.AsyncClient(timeout=12.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            effective_url = str(resp.url)
            content_type = resp.headers.get("content-type", "").lower()

            if "text/html" not in content_type and "application/xhtml" not in content_type:
                # Direct content (like an image or pdf), pass through without frame headers
                passthrough_headers = {
                    "Content-Type": content_type or "application/octet-stream",
                    "X-Content-Type-Options": "nosniff"
                }
                return Response(content=resp.content, status_code=resp.status_code, headers=passthrough_headers)

            html_text = resp.text

            # Neutralize framebusting code
            html_text = _neutralize_framebusting(html_text)

            # Inject <base href="...">
            base_tag = f'<base href="{effective_url}">'
            if "<head" in html_text.lower():
                # Insert right after <head...>
                html_text = re.sub(r'(<head[^>]*>)', r'\1\n  ' + base_tag, html_text, count=1, flags=re.IGNORECASE)
            elif "<html" in html_text.lower():
                html_text = re.sub(r'(<html[^>]*>)', r'\1\n<head>' + base_tag + '</head>', html_text, count=1, flags=re.IGNORECASE)
            else:
                html_text = f"<head>{base_tag}</head>\n" + html_text

            # Prevent beforeunload prompts inside iframe
            cleanup_script = "<script>window.onbeforeunload = null;</script>"
            if "</body>" in html_text.lower():
                html_text = re.sub(r'(</body>)', cleanup_script + r'\n\1', html_text, count=1, flags=re.IGNORECASE)
            else:
                html_text += cleanup_script

            response_headers = {
                "Content-Type": "text/html; charset=utf-8",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store, no-cache, must-revalidate",
            }
            return HTMLResponse(content=html_text, status_code=200, headers=response_headers)

    except httpx.TimeoutException:
        return HTMLResponse(
            content=_build_error_page(url, "El sitio web tardó demasiado tiempo en responder (tiempo de espera agotado)."),
            status_code=504
        )
    except httpx.ConnectError:
        return HTMLResponse(
            content=_build_error_page(url, "No se pudo establecer conexión con el servidor del sitio web."),
            status_code=502
        )
    except Exception as e:
        logger.error(f"Error proxying {url}: {e}")
        return HTMLResponse(
            content=_build_error_page(url, f"Error al procesar el sitio web: {str(e)}"),
            status_code=500
        )
