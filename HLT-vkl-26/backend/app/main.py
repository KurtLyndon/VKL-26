from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.services.scheduler import SchedulerLoop
from app.services.worker import WorkerLoop
from app import models  # noqa: F401
from database.migrations import ensure_schema_up_to_date

settings = get_settings()
scheduler_loop = SchedulerLoop(settings.scheduler_poll_seconds)
worker_loop = WorkerLoop(settings.worker_poll_seconds)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    ensure_schema_up_to_date(auto_apply=settings.auto_apply_migrations)
    if settings.scheduler_enabled:
        scheduler_loop.start()
    if settings.worker_enabled:
        worker_loop.start()


@app.on_event("shutdown")
def on_shutdown():
    scheduler_loop.stop()
    worker_loop.stop()


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.app_env}


app.include_router(api_router, prefix=settings.api_v1_prefix)
