import os
import sys
import time
from typing import Dict, Any
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import redis

app = FastAPI(
    title="CRM Engine API",
    description="Backend API for Local Lead Acquisition, Prospecting and CRM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "crm_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "crm_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "crm_password")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

START_TIME = time.time()


def check_postgres() -> Dict[str, Any]:
    try:
        conninfo = (
            f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} "
            f"user={POSTGRES_USER} password={POSTGRES_PASSWORD} connect_timeout=3"
        )
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return {"status": "connected", "latency_ms": 0}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def check_redis() -> Dict[str, Any]:
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            socket_timeout=3
        )
        if r.ping():
            return {"status": "connected"}
        return {"status": "unreachable"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@app.get("/health")
def health(response: Response) -> Dict[str, Any]:
    pg_status = check_postgres()
    rd_status = check_redis()
    
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
        "version": "1.0.0",
        "phase": "Fase 1 - Infraestructura, Docker Compose y Gestion de Puertos",
        "city_coverage": "Tijuana, Baja California",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "status": "operational"
    }


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "CRM Core API operational. Access /docs for API documentation."}
