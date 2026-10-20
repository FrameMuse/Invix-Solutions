from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import ProductRead
from app.security import require_service_token
from app.services.products import ProductError, ProductService, get_product_service

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_service_token)],
)


@router.post("/products", response_model=ProductRead)
async def create_product(
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[ProductService, Depends(get_product_service)],
    title: Annotated[str, Form()],
    photo: Annotated[UploadFile, File()],
) -> ProductRead:
    try:
        return await service.create(session, title, photo)
    except ProductError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
