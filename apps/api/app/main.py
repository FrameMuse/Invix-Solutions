from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import engine, session_factory
from app.events import CatalogEvents
from app.routers import catalog, internal
from app.storage import Storage


def create_app() -> FastAPI:
    settings = get_settings()
    storage = Storage(settings)
    events = CatalogEvents(settings.asyncpg_dsn)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await storage.ensure_bucket()
        await events.start()
        try:
            yield
        finally:
            await events.stop()
            await engine.dispose()

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

    application = FastAPI(title="Invix Solutions API", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    application.state.storage = storage
    application.state.events = events
    application.include_router(catalog.router)
    application.include_router(internal.router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as error:
            raise HTTPException(status_code=503, detail="Database unavailable") from error
        return {"status": "ok"}

    return application


app = create_app()
