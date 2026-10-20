import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.config import get_settings


async def require_service_token(
    x_service_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = get_settings().service_token
    if not x_service_token or not secrets.compare_digest(x_service_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token",
        )
