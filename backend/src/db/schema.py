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
    phone_e164 VARCHAR(50),
    phone_country VARCHAR(10),
    phone_valid BOOLEAN,
    website TEXT,
    normalized_domain VARCHAR(255),
    has_dedicated_website BOOLEAN,
    social_links JSONB DEFAULT '{}'::jsonb,
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
    technical_health_score NUMERIC(5, 2),
    acceptance_probability_pct NUMERIC(5, 2),
    sales_arguments JSONB DEFAULT '[]'::jsonb,
    audited_at TIMESTAMPTZ,
    qualified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_seen_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT unique_source_external_id UNIQUE(external_source, external_id)
);

-- Migrations for existing tables if columns missing
ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_e164 VARCHAR(50);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_country VARCHAR(10);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_valid BOOLEAN;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS normalized_domain VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS has_dedicated_website BOOLEAN;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS social_links JSONB DEFAULT '{}'::jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS technical_health_score NUMERIC(5, 2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS acceptance_probability_pct NUMERIC(5, 2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS sales_arguments JSONB DEFAULT '[]'::jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS audited_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualified_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS lead_web_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    url_checked TEXT NOT NULL,
    dns_resolved BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(100),
    http_status_code INT,
    redirect_count INT DEFAULT 0,
    final_url TEXT,
    has_ssl BOOLEAN DEFAULT FALSE,
    ssl_valid BOOLEAN DEFAULT FALSE,
    ssl_days_remaining INT,
    ssl_issuer VARCHAR(255),
    is_self_signed BOOLEAN DEFAULT FALSE,
    redirects_to_https BOOLEAN DEFAULT FALSE,
    ttfb_ms NUMERIC(10, 2),
    download_time_ms NUMERIC(10, 2),
    html_size_bytes INT,
    compression_type VARCHAR(50),
    has_viewport BOOLEAN DEFAULT FALSE,
    viewport_content VARCHAR(255),
    technologies JSONB DEFAULT '[]'::jsonb,
    has_title BOOLEAN DEFAULT FALSE,
    title_text TEXT,
    has_description BOOLEAN DEFAULT FALSE,
    description_text TEXT,
    h1_count INT DEFAULT 0,
    has_canonical BOOLEAN DEFAULT FALSE,
    has_open_graph BOOLEAN DEFAULT FALSE,
    has_schema_local_business BOOLEAN DEFAULT FALSE,
    has_google_analytics BOOLEAN DEFAULT FALSE,
    has_google_tag_manager BOOLEAN DEFAULT FALSE,
    has_meta_pixel BOOLEAN DEFAULT FALSE,
    has_tiktok_pixel BOOLEAN DEFAULT FALSE,
    technical_health_score NUMERIC(5, 2),
    acceptance_probability_pct NUMERIC(5, 2),
    findings JSONB DEFAULT '[]'::jsonb,
    audit_duration_seconds NUMERIC(8, 3),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS deduplication_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    merged_lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    merge_reason VARCHAR(100) NOT NULL,
    similarity_score NUMERIC(5, 4),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Phase 4 Migrations: Channels, Activity, Calendar, and OAuth
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS has_whatsapp BOOLEAN DEFAULT TRUE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS channels_status JSONB DEFAULT '{}'::jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS first_contact_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS lead_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL DEFAULT 'Llamada',
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    notes TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    google_event_id VARCHAR(255),
    sync_status VARCHAR(50) NOT NULL DEFAULT 'LOCAL_ONLY',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL UNIQUE DEFAULT 'google',
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    scope TEXT,
    user_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Phase 5 Migrations: Pipeline 12 Stages, History, Stagnation, Notes, Blacklist
ALTER TABLE leads ADD COLUMN IF NOT EXISTS stage_entered_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE leads ADD COLUMN IF NOT EXISTS postponed_until TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS postponed_note TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS regret_reason VARCHAR(100);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS regret_details TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS regret_amount NUMERIC(12, 2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS regret_service VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS loss_reason VARCHAR(100);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS deleted_reason VARCHAR(255);

CREATE TABLE IF NOT EXISTS lead_stage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    from_stage VARCHAR(50),
    to_stage VARCHAR(50) NOT NULL,
    duration_seconds INTEGER DEFAULT 0,
    changed_by VARCHAR(50) DEFAULT 'user',
    notes TEXT,
    reason VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS lead_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author VARCHAR(100) DEFAULT 'Usuario',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS blacklist_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_e164 VARCHAR(50),
    normalized_domain VARCHAR(255),
    external_id VARCHAR(255),
    reason VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stage_history_lead ON lead_stage_history(lead_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lead_notes_lead ON lead_notes(lead_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blacklist_phone ON blacklist_identifiers(phone_e164);
CREATE INDEX IF NOT EXISTS idx_blacklist_domain ON blacklist_identifiers(normalized_domain);
CREATE INDEX IF NOT EXISTS idx_blacklist_ext_id ON blacklist_identifiers(external_id);

CREATE INDEX IF NOT EXISTS idx_leads_phone_e164 ON leads(phone_e164);
CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads(normalized_domain);
CREATE INDEX IF NOT EXISTS idx_leads_acceptance_score ON leads(acceptance_probability_pct);
CREATE INDEX IF NOT EXISTS idx_web_audits_lead ON lead_web_audits(lead_id);
CREATE INDEX IF NOT EXISTS idx_dedup_master ON deduplication_history(master_lead_id);
CREATE INDEX IF NOT EXISTS idx_activity_lead ON lead_activity_log(lead_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_lead ON calendar_events(lead_id);

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

            # Seed default system settings
            cur.execute(
                """
                INSERT INTO system_settings (key, value, description)
                VALUES ('whatsapp_template', 'Hola, buen día.', 'Mensaje inicial predeterminado para WhatsApp')
                ON CONFLICT (key) DO NOTHING;
                """
            )

            logger.info("Initial seed categories and keywords committed.")
