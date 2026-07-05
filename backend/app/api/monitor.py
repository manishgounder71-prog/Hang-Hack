"""Monitoring endpoint for production-readiness."""
import time
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
_start_time = time.time()

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/uptime")
async def uptime():
    return {"uptime_seconds": int(time.time() - _start_time), "started_at": _start_time}


@router.get("/health/detailed")
async def health_detailed():
    import psutil
    info = {
        "status": "healthy",
        "uptime_seconds": int(time.time() - _start_time),
        "version": "1.0.0",
        "environment": "production",
    }
    try:
        info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        info["memory_percent"] = psutil.virtual_memory().percent
        info["disk_percent"] = psutil.disk_usage("/").percent
    except Exception:
        info["system_metrics"] = "unavailable"
    return info


@router.get("/health/ready")
async def readiness():
    from app.core.database import get_session
    from app.core.cache import cache
    from app.core.config import settings

    checks = {
        "app": True,
        "database": False,
        "cache": False,
        "llm": False,
    }
    try:
        checks["database"] = settings.DATABASE_URL is not None
    except Exception:
        pass
    try:
        checks["cache"] = cache._redis is not None
    except Exception:
        pass
    try:
        checks["llm"] = settings.LLM_API_KEY is not None
    except Exception:
        pass

    all_healthy = all(checks.values())
    return {"healthy": all_healthy, "checks": checks}
