from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.services.state import read_state

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    read_state()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Single-user crypto bot console for OKX/Binance dry-run and live-account readiness. Live start requires preflight and manual acknowledgement.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok", "safety": "live_requires_preflight_and_manual_ack"}
