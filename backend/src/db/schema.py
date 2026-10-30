import logging
from src.db.connection import get_db_connection

logger = logging.getLogger("crm.db.schema")

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS category_keywords (
    id SERIAL PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT unique_cat_keyword UNIQUE(category_id, keyword)
);

CREATE TABLE IF NOT EXISTS category_osm_tags (
    id SERIAL PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT unique_cat_osm_tag UNIQUE(category_id, key, value)
);

CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    category_slug VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'hybrid',
    zone_name VARCHAR(100) NOT NULL DEFAULT 'tijuana-full',
    status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
    total_cells INT NOT NULL DEFAULT 0,
    completed_cells INT NOT NULL DEFAULT 0,
    failed_cells INT NOT NULL DEFAULT 0,
    leads_found INT NOT NULL DEFAULT 0,
    leads_saved INT NOT NULL DEFAULT 0,
    leads_skipped INT NOT NULL DEFAULT 0,
    cooldown_until TIMESTAMPTZ,
    config_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS extraction_grid_cells (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    cell_code VARCHAR(100) NOT NULL,
    parent_cell_id UUID REFERENCES extraction_grid_cells(id) ON DELETE SET NULL,
    depth INT NOT NULL DEFAULT 0,
    min_lat DOUBLE PRECISION NOT NULL,
    min_lon DOUBLE PRECISION NOT NULL,
    max_lat DOUBLE PRECISION NOT NULL,
    max_lon DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    results_count INT NOT NULL DEFAULT 0,
    last_scanned_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_source VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category_slug VARCHAR(100) NOT NULL,
    primary_category VARCHAR(255),
    subcategories JSONB DEFAULT '[]'::jsonb,
    phone_raw VARCHAR(100),
    phone_normalized VARCHAR(50),
    website TEXT,
    address_raw TEXT,
    street VARCHAR(255),
    house_number VARCHAR(50),
    suburb VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100) DEFAULT 'Tijuana' NOT NULL,
    state VARCHAR(100) DEFAULT 'Baja California' NOT NULL,
    country VARCHAR(50) DEFAULT 'Mexico' NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    rating NUMERIC(3, 2),
    review_count INT DEFAULT 0,
    opening_hours_raw TEXT,
    is_claimed BOOLEAN,
    lifecycle_stage VARCHAR(50) DEFAULT 'EXTRACTED' NOT NULL,
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_seen_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT unique_source_external_id UNIQUE(external_source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_category ON leads(category_slug);
CREATE INDEX IF NOT EXISTS idx_leads_lifecycle ON leads(lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_leads_deleted ON leads(is_deleted);
CREATE INDEX IF NOT EXISTS idx_leads_geo ON leads(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_grid_cells_job ON extraction_grid_cells(job_id, status);
"""

INITIAL_SEEDS = [
    {
        "slug": "dentistas",
        "name": "Dentistas",
        "keywords": [
            "dentista",
            "clínica dental",
            "consultorio dental",
            "ortodoncia",
            "odontólogo",
            "cirujano dentista",
            "endodoncia",
            "implantología dental"
        ],
        "osm_tags": [
            ("amenity", "dentist"),
            ("healthcare", "dentist"),
            ("healthcare:speciality", "orthodontics")
        ]
    },
    {
        "slug": "despachos-contables",
        "name": "Despachos Contables",
        "keywords": [
            "despacho contable",
            "contador público",
            "asesoría fiscal",
            "contabilidad",
            "consultoría fiscal",
            "despacho fiscal",
            "auditoría contable"
        ],
        "osm_tags": [
            ("office", "accountant"),
            ("office", "tax_advisor"),
            ("office", "financial_advisor")
        ]
    }
]


def init_database_schema():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            logger.info("Database schema migration executed successfully.")

            # Seed categories
            for cat in INITIAL_SEEDS:
                cur.execute(
                    """
                    INSERT INTO categories (slug, name, is_active)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                    """,
                    (cat["slug"], cat["name"])
                )
                row = cur.fetchone()
                category_id = row["id"]

                # Seed keywords
                for kw in cat["keywords"]:
                    cur.execute(
                        """
                        INSERT INTO category_keywords (category_id, keyword)
                        VALUES (%s, %s)
                        ON CONFLICT (category_id, keyword) DO NOTHING;
                        """,
                        (category_id, kw)
                    )

                # Seed OSM tags
                for key, val in cat["osm_tags"]:
                    cur.execute(
                        """
                        INSERT INTO category_osm_tags (category_id, key, value)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (category_id, key, value) DO NOTHING;
                        """,
                        (category_id, key, val)
                    )

            logger.info("Initial seed categories and keywords committed.")
