import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as aioredis
from src.config import settings

logger = logging.getLogger("crm.queue.redis")

STATE_QUEUED = "QUEUED"
STATE_RUNNING = "RUNNING"
STATE_PAUSED = "PAUSED"
STATE_COOLDOWN = "COOLDOWN"
STATE_COMPLETED = "COMPLETED"
STATE_FAILED = "FAILED"
STATE_CANCELLED = "CANCELLED"


class RedisJobQueue:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )
        return self._redis

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None

    # Job Management
    async def enqueue_job(self, job_id: str):
        r = await self.get_client()
        await r.rpush("crm:queue:jobs", job_id)
        await r.hset(f"crm:job:{job_id}:state", mapping={"status": STATE_QUEUED, "pause": "0", "cancel": "0"})

    async def get_next_job(self) -> Optional[str]:
        r = await self.get_client()
        return await r.lpop("crm:queue:jobs")

    async def set_job_status(self, job_id: str, status: str):
        r = await self.get_client()
        await r.hset(f"crm:job:{job_id}:state", "status", status)

    async def get_job_status(self, job_id: str) -> Optional[str]:
        r = await self.get_client()
        return await r.hget(f"crm:job:{job_id}:state", "status")

    async def pause_job(self, job_id: str):
        r = await self.get_client()
        await r.hset(f"crm:job:{job_id}:state", mapping={"pause": "1", "status": STATE_PAUSED})

    async def resume_job(self, job_id: str):
        r = await self.get_client()
        await r.hset(f"crm:job:{job_id}:state", mapping={"pause": "0", "status": STATE_RUNNING})

    async def cancel_job(self, job_id: str):
        r = await self.get_client()
        await r.hset(f"crm:job:{job_id}:state", mapping={"cancel": "1", "status": STATE_CANCELLED})
        await r.delete(f"crm:queue:cells:{job_id}")

    async def is_job_paused(self, job_id: str) -> bool:
        r = await self.get_client()
        val = await r.hget(f"crm:job:{job_id}:state", "pause")
        return val == "1"

    async def is_job_cancelled(self, job_id: str) -> bool:
        r = await self.get_client()
        val = await r.hget(f"crm:job:{job_id}:state", "cancel")
        return val == "1"

    # Cell Task Queue
    async def enqueue_cell(self, job_id: str, cell_data: Dict[str, Any]):
        r = await self.get_client()
        payload = json.dumps(cell_data)
        await r.rpush(f"crm:queue:cells:{job_id}", payload)

    async def get_next_cell(self, job_id: str) -> Optional[Dict[str, Any]]:
        r = await self.get_client()
        payload = await r.lpop(f"crm:queue:cells:{job_id}")
        if payload:
            return json.loads(payload)
        return None

    async def get_pending_cells_count(self, job_id: str) -> int:
        r = await self.get_client()
        return await r.llen(f"crm:queue:cells:{job_id}")

    # Circuit Breaker Cooldown
    async def set_circuit_breaker(self, cooldown_seconds: int, reason: str = ""):
        r = await self.get_client()
        await r.setex("crm:circuit_breaker:gmaps", cooldown_seconds, reason)

    async def is_circuit_breaker_active(self) -> bool:
        r = await self.get_client()
        return await r.exists("crm:circuit_breaker:gmaps") > 0


queue_manager = RedisJobQueue()
