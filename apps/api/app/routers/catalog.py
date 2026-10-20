import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.events import CatalogEvents
from app.schemas import ProductRead
from app.services.products import ProductService, get_product_service

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[ProductService, Depends(get_product_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProductRead]:
    return await service.list(session, limit, offset)


@router.get("/events")
async def catalog_events(request: Request) -> StreamingResponse:
    events: CatalogEvents = request.app.state.events

    async def stream():
        yield "retry: 5000\n\n"
        async with events.subscribe() as queue:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield f"data: {payload}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/images/{key:path}")
async def get_image(
    key: str,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> Response:
    image = await service.image(key)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    data, content_type = image
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
