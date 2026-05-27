from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import init_db, close_db
from backend.redis_client import init_redis, close_redis
from backend.api import router as api_router
from backend.tasks.daily_update import scheduler, setup_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_redis()
    setup_scheduler()
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()
    await close_db()
    await close_redis()


settings = get_settings()

app = FastAPI(
    title="Fund Analyzer API",
    description="基金分析系统后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
