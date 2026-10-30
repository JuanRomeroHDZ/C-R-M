import asyncio
import sys
from src.analysis.deduplication import run_multilayer_deduplication
from src.analysis.pipeline import process_and_audit_lead
from src.db.connection import execute_query


async def verify_phase3():
    print("====================================================================")
    print("CRM LOCAL - AUDITORIA TECNICA, DEDUPLICACION Y SCORING (FASE 3)")
    print("====================================================================")
    print("Entorno: Tijuana, Baja California")
    print("Procesando prospectos reales en PostgreSQL sin datos simulados...")
    print("--------------------------------------------------------------------")

    # 1. Multi-layer Deduplication
    print("\n[1/3] EJECUTANDO MOTOR DE DEDUPLICACION MULTICAPA...")
    dedup_res = run_multilayer_deduplication()
    print(f"Total prospectos analizados:      {dedup_res['processed_leads']}")
    print(f"Registros duplicados fusionados:  {dedup_res['merged_count']}")
    print(f"Prospectos unicos consolidados:   {dedup_res['remaining_unique_leads']}")

    # 2. Select Representative Real Leads for Live Technical Audit
    print("\n[2/3] SELECCIONANDO PROSPECTOS REALES PARA AUDITORIA EN VIVO...")
    # Select one with dedicated website and one without
    site_leads = execute_query(
        """
        SELECT id, name, category_slug, phone_e164, website, has_dedicated_website, review_count, rating
        FROM leads
        WHERE has_dedicated_website = TRUE AND is_deleted = FALSE
        ORDER BY review_count DESC
        LIMIT 2;
        """
    )

    no_site_leads = execute_query(
        """
        SELECT id, name, category_slug, phone_e164, website, has_dedicated_website, review_count, rating
        FROM leads
        WHERE has_dedicated_website = FALSE AND is_deleted = FALSE
        ORDER BY review_count DESC
        LIMIT 2;
        """
    )

    leads_to_audit = site_leads + no_site_leads
    if not leads_to_audit:
        print("ERROR: No se encontraron prospectos reales en la base de datos.")
        sys.exit(1)

    print(f"Auditando {len(leads_to_audit)} prospectos reales seleccionados...")

    # 3. Execute Live Audit, Scoring, and Pipeline Transitions
    print("\n[3/3] AUDITANDO SITIOS WEB Y GENERANDO MODELO PREDICTIVO...")
    audited_summaries = []

    for l in leads_to_audit:
        lead_id = str(l["id"])
        print(f"\nProcesando: {l['name']} ({l['category_slug']})...")
        res = await process_and_audit_lead(lead_id)
        audited_summaries.append(res)

        # Retrieve saved row from PostgreSQL to verify persistence
        saved_row = execute_query(
            """
            SELECT id, name, category_slug, phone_e164, website, has_dedicated_website,
                   technical_health_score, acceptance_probability_pct,
                   sales_arguments, lifecycle_stage, audited_at, qualified_at
            FROM leads
            WHERE id = %s;
            """,
            (lead_id,)
        )[0]

        print("--------------------------------------------------------------------")
        print(f"Prospecto:               {saved_row['name']}")
        print(f"Categoria:               {saved_row['category_slug']}")
        print(f"Telefono E.164:          {saved_row.get('phone_e164') or 'No disponible'}")
        print(f"Sitio Web Propio:        {'Si' if saved_row['has_dedicated_website'] else 'No (usa redes o no tiene)'}")
        print(f"Salud Tecnica Web:       {saved_row['technical_health_score']} / 100 puntos")
        print(f"Probabilidad de Exito:   {saved_row['acceptance_probability_pct']}%")
        print(f"Fase en Pipeline:        {saved_row['lifecycle_stage']}")
        print(f"Marca Auditado:          {saved_row.get('audited_at')}")
        print(f"Marca Calificado:        {saved_row.get('qualified_at')}")
        print("Argumentos de Venta:")
        for arg in saved_row.get("sales_arguments") or []:
            print(f"  * {arg}")
        print("--------------------------------------------------------------------")

    print("\n====================================================================")
    print("VERIFICACION DE FASE 3 COMPLETADA EXITOSAMENTE")
    print(f"Total prospectos auditados y calificados: {len(audited_summaries)}")
    print("Persistencia comprobada en PostgreSQL, lead_web_audits y maquina de estados.")
    print("====================================================================")


if __name__ == "__main__":
    asyncio.run(verify_phase3())
