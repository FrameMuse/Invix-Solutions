from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update
from asyncpg import Pool


class DedupeMiddleware(BaseMiddleware):
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        async with self._pool.acquire() as connection:
            inserted = await connection.fetchval(
                """
                INSERT INTO processed_updates (update_id)
                VALUES ($1)
                ON CONFLICT DO NOTHING
                RETURNING update_id
                """,
                event.update_id,
            )
        if inserted is None:
            return None
        return await handler(event, data)
