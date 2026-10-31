from typing import Dict, Any, Optional
import json


def build_commercial_pitch(lead: Dict[str, Any], audit: Optional[Dict[str, Any]] = None) -> str:
    name = lead.get("name", "su negocio")
    category = lead.get("primary_category") or lead.get("category_slug", "su sector")
    custom = lead.get("commercial_pitch")
    if custom and custom.strip():
        return custom.strip()

    has_web = bool(lead.get("has_dedicated_website"))
    web_url = lead.get("website")

    if not has_web or not web_url:
        return (
            f"Hola, revise la presencia digital de {name} y note que aun no cuentan "
            f"con una pagina web propia adaptada a celulares para captar clientes en internet. "
            f"Con gusto podemos disenarles una presencia moderna que les permita recibir mensajes y llamadas directas."
        )

    # Has website, analyze flaws in natural human words
    flaws = []
    if audit:
        if not audit.get("has_ssl") or not audit.get("ssl_valid"):
            flaws.append("aparece como no segura (sin el candado de proteccion)")
        if not audit.get("has_viewport"):
            flaws.append("no se adapta comodamente a pantallas de celular")
        if audit.get("ttfb_ms") and audit.get("ttfb_ms") > 1200:
            flaws.append("tarda varios segundos en cargar")
        if not audit.get("has_meta_pixel") and not audit.get("has_google_analytics"):
            flaws.append("no tiene herramientas para medir visitas de clientes ni efectividad de anuncios")
        if not audit.get("has_schema_local_business"):
            flaws.append("esta poco visible en los resultados de busqueda locales")

    if not flaws:
        # Check sales arguments or default
        return (
            f"Hola, estuve revisando el sitio web de {name} ({web_url}). Cuentan con buena base, "
            f"pero podemos ayudarles a incorporar botones de contacto directo a WhatsApp y optimizar "
            f"su presentacion para aumentar las consultas y citas semanales."
        )

    flaws_text = ", ".join(flaws[:-1]) + " y " + flaws[-1] if len(flaws) > 1 else flaws[0]
    return (
        f"Hola, revise la presencia en internet de {name} ({web_url}) y note que su pagina {flaws_text}. "
        f"Con gusto podemos apoyarles a modernizarla para que brinde total confianza y capte mas pacientes y clientes en Tijuana."
    )
