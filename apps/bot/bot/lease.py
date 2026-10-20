import asyncio
import logging

import asyncpg

logger = logging.getLogger(__name__)

LEASE_NAME = "polling"
LEASE_SECONDS = 15
RENEW_SECONDS = 5


async def acquire_lease(pool: asyncpg.Pool, owner: str) -> bool:
    result = await pool.fetchval(
        """
        INSERT INTO bot_lease (name, owner, expires_at)
        VALUES ($1, $2, now() + ($3 * interval '1 second'))
        ON CONFLICT (name) DO UPDATE
        SET owner = EXCLUDED.owner, expires_at = EXCLUDED.expires_at
        WHERE bot_lease.expires_at < now() OR bot_lease.owner = EXCLUDED.owner
        RETURNING owner
        """,
        LEASE_NAME,
        owner,
        LEASE_SECONDS,
    )
    return result == owner


async def renew_lease(pool: asyncpg.Pool, owner: str) -> bool:
    result = await pool.fetchval(
        """
        UPDATE bot_lease
        SET expires_at = now() + ($3 * interval '1 second')
        WHERE name = $1 AND owner = $2
        RETURNING owner
        """,
        LEASE_NAME,
        owner,
        LEASE_SECONDS,
    )
    return result == owner


async def release_lease(pool: asyncpg.Pool, owner: str) -> None:
    await pool.execute(
        "DELETE FROM bot_lease WHERE name = $1 AND owner = $2",
        LEASE_NAME,
        owner,
    )


async def wait_for_lease(
    pool: asyncpg.Pool,
    owner: str,
    stop: asyncio.Event,
) -> bool:
    while not stop.is_set():
        try:
            acquired = await acquire_lease(pool, owner)
        except Exception as error:
            logger.warning("Failed to acquire polling lease: %s", error)
        else:
            if acquired:
                logger.info("Polling lease acquired")
                return True
            logger.info("Polling lease is held by another instance")

        try:
            await asyncio.wait_for(stop.wait(), timeout=RENEW_SECONDS)
        except TimeoutError:
            pass

    return False


async def hold_lease(
    pool: asyncpg.Pool,
    owner: str,
    lost: asyncio.Event,
) -> None:
    while not lost.is_set():
        try:
            await asyncio.wait_for(lost.wait(), timeout=RENEW_SECONDS)
        except TimeoutError:
            pass

        if lost.is_set():
            return

        try:
            renewed = await renew_lease(pool, owner)
        except Exception as error:
            logger.warning("Failed to renew polling lease: %s", error)
            lost.set()
            return

        if not renewed:
            logger.warning("Polling lease lost")
            lost.set()
            return
