"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import health, search, sources, summary, topics, trends
from backend.app.config import settings
from backend.app.db.session import init_db
from backend.app.utils.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log = get_logger()
    log.info("startup", env=settings.app_env)
    await init_db()
    yield
    log.info("shutdown")


app = FastAPI(
    title="AI Developer Trends Intelligence Platform",
    version="0.1.0",
    description=(
        "Free, local-first platform for scraping, embedding, searching, "
        "and summarizing developer/AI trends across Reddit, HN, GitHub, and arXiv."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sources.router)
app.include_router(search.router)
app.include_router(trends.router)
app.include_router(topics.router)
app.include_router(summary.router)


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "endpoints": ["/health", "/sources", "/search", "/trends", "/topics", "/summary"],
    }
