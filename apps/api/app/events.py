import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import asyncpg

CHANNEL = "catalog"


class CatalogEvents:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._connection: asyncpg.Connection | None = None
        self._subscribers: set[asyncio.Queue[str]] = set()

    async def start(self) -> None:
        connection = await asyncpg.connect(self._dsn)
        try:
            await connection.add_listener(CHANNEL, self._on_notify)
        except Exception:
            await connection.close()
            raise
        self._connection = connection

    async def stop(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is None:
            return

        with suppress(Exception):
            await connection.remove_listener(CHANNEL, self._on_notify)
        await connection.close()

    def _on_notify(
        self,
        _: asyncpg.Connection,
        __: int,
        ___: str,
        payload: str,
    ) -> None:
        for queue in tuple(self._subscribers):
            queue.put_nowait(payload)

    async def publish(self, payload: str) -> None:
        if self._connection is None:
            raise RuntimeError("Catalog events are not started")
        await self._connection.execute("SELECT pg_notify($1, $2)", CHANNEL, payload)

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)
