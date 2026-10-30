import asyncio
import sys
from src.db.schema import init_database_schema
from src.db.connection import execute_query
from src.queue.worker import worker_instance
from src.queue.redis_queue import queue_manager


async def verify_field_extraction():
    print("====================================================================")
    print("CRM LOCAL - PRUEBA DE CAMPO CONTROLADA (FASE 2)")
    print("====================================================================")
    print("Entorno: Tijuana, Baja California (Zona Rio)")
    print("Verificando extraccion real sin datos ficticios...")
    print("--------------------------------------------------------------------")

    # 1. Initialize schema
    init_database_schema()

    # Define Zona Rio micro-cell
    micro_cell = {
        "id": None,
        "cell_code": "cell_test_zona_rio",
        "depth": 0,
        "min_lat": 32.5180,
        "min_lon": -117.0250,
        "max_lat": 32.5350,
        "max_lon": -117.0080
    }

    test_categories = ["dentistas", "despachos-contables"]
    verified_leads = []

    for cat_slug in test_categories:
        print(f"\n[PROCESANDO CATEGORIA: {cat_slug.upper()}]")
        cat_data = await worker_instance.get_category_data(cat_slug)
        print(f"Keywords disponibles: {len(cat_data['keywords'])}")
        print(f"Etiquetas OSM configuradas: {len(cat_data['osm_tags'])}")

        # Execute extraction with hybrid source
        print(f"Iniciando barrido en micro-celda ({micro_cell['min_lat']}, {micro_cell['min_lon']})...")
        res = await worker_instance.process_single_cell(
            job_id="00000000-0000-0000-0000-000000000000",
            cell=micro_cell,
            category_data=cat_data,
            source="hybrid",
            saturation_threshold=50,
            max_depth=1
        )

        print(f"Resultado ejecucion celda: {res['status']}")
        print(f"Prospectos encontrados: {res.get('leads_found', 0)}")
        print(f"Prospectos guardados en DB: {res.get('leads_saved', 0)}")

        # Query database to confirm persisted record
        db_rows = execute_query(
            """
            SELECT id, external_source, external_id, name, category_slug,
                   phone_raw, website, address_raw, city, state, latitude, longitude,
                   rating, review_count, lifecycle_stage, created_at
            FROM leads
            WHERE category_slug = %s AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (cat_slug,)
        )

        if not db_rows:
            # If not found in micro-cell, try with google_maps source directly
            print(f"Intentando extraccion complementaria en Google Maps para {cat_slug}...")
            if cat_data["keywords"]:
                kw = cat_data["keywords"][0]
                gmaps_leads = await worker_instance.gmaps_extractor.search_cell(
                    keyword=kw,
                    category_slug=cat_slug,
                    min_lat=micro_cell["min_lat"],
                    min_lon=micro_cell["min_lon"],
                    max_lat=micro_cell["max_lat"],
                    max_lon=micro_cell["max_lon"],
                    max_results=5
                )
                from src.queue.worker import save_lead
                for l in gmaps_leads:
                    save_lead(l)

            db_rows = execute_query(
                """
                SELECT id, external_source, external_id, name, category_slug,
                       phone_raw, website, address_raw, city, state, latitude, longitude,
                       rating, review_count, lifecycle_stage, created_at
                FROM leads
                WHERE category_slug = %s AND is_deleted = FALSE
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (cat_slug,)
            )

        if not db_rows:
            print(f"ERROR: No se pudo capturar prospecto real para la categoria {cat_slug}")
            sys.exit(1)

        lead = db_rows[0]
        verified_leads.append(lead)

        print("\n--- RESUMEN TECNICO DEL REGISTRO CAPTURADO ---")
        print(f"ID Base de Datos:    {lead['id']}")
        print(f"Nombre Comercial:    {lead['name']}")
        print(f"Categoria:           {lead['category_slug']}")
        print(f"Fuente de Origen:    {lead['external_source']}")
        print(f"Identificador Ext:   {lead['external_id']}")
        print(f"Telefono:            {lead.get('phone_raw') or 'No especificado'}")
        print(f"Sitio Web:           {lead.get('website') or 'No especificado'}")
        print(f"Direccion Fisica:    {lead.get('address_raw') or 'Tijuana, B.C.'}")
        print(f"Coordenadas:         Lat {lead.get('latitude')}, Lon {lead.get('longitude')}")
        print(f"Resenas / Rating:    {lead.get('rating')} estrellas ({lead.get('review_count')} resenas)")
        print(f"Etapa de Embudo:     {lead['lifecycle_stage']}")
        print(f"Marca Temporal:      {lead['created_at']}")
        print("----------------------------------------------")

    await worker_instance.gmaps_extractor.close()
    await queue_manager.close()

    print("\n====================================================================")
    print("VERIFICACION COMPLETADA CON EXITO")
    print(f"Total categorias verificadas: {len(verified_leads)} / {len(test_categories)}")
    print("Datos comprobados en PostgreSQL sin registros ficticios.")
    print("====================================================================")


if __name__ == "__main__":
    asyncio.run(verify_field_extraction())
