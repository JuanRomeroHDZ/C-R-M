import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.db.connection import get_db_connection
from src.db.schema import init_database_schema
from src.queue.worker import worker_instance
from src.queue.redis_queue import queue_manager
from src.api.categories import router as categories_router
from src.api.jobs import router as jobs_router
from src.api.leads import router as leads_router
from src.api.audit import router as audit_router
from src.api.deduplication import router as dedup_router
from src.api.calendar import router as calendar_router
from src.api.interactions import router as interactions_router
from src.api.settings import router as settings_router
from src.api.dev_reload import router as dev_reload_router, broadcast_reload

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("crm.main")

START_TIME = time.time()
worker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database schema and seeds...")
    try:
        init_database_schema()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")

    # Start background worker loop
    global worker_task
    worker_task = asyncio.create_task(worker_instance.run_worker_loop())
    logger.info("Background extraction worker started.")

    yield

    # Shutdown
    logger.info("Shutting down extraction worker...")
    worker_instance.is_running = False
    if worker_task:
        worker_task.cancel()
    await worker_instance.gmaps_extractor.close()
    await queue_manager.close()
    logger.info("Shutdown completed.")


app = FastAPI(
    title="CRM Engine API",
    description="Backend API for Local Lead Acquisition, Prospecting and CRM",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(categories_router)
app.include_router(jobs_router)
app.include_router(leads_router)
app.include_router(audit_router)
app.include_router(dedup_router)
app.include_router(calendar_router)
app.include_router(interactions_router)
app.include_router(settings_router)
app.include_router(dev_reload_router)


def check_postgres() -> Dict[str, Any]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return {"status": "connected", "latency_ms": 0}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def check_redis() -> Dict[str, Any]:
    try:
        r = await queue_manager.get_client()
        if await r.ping():
            return {"status": "connected"}
        return {"status": "unreachable"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@app.get("/health")
async def health(response: Response) -> Dict[str, Any]:
    pg_status = check_postgres()
    rd_status = await check_redis()

    is_healthy = pg_status["status"] == "connected" and rd_status["status"] == "connected"
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": time.time(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "services": {
            "backend": "online",
            "postgres": pg_status,
            "redis": rd_status
        }
    }


@app.get("/api/v1/status")
def system_status() -> Dict[str, Any]:
    return {
        "system": "Sistema de Captacion, Prospeccion y CRM Local",
        "version": "4.0.0",
        "phase": "Fase 4 - Enriquecimiento de Contactos, Redirecciones, Calendario y Modo Desarrollador",
        "city_coverage": "Tijuana, Baja California",
        "environment": settings.ENVIRONMENT,
        "status": "operational"
    }


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "CRM Core API operational. Access /docs for API documentation."}
