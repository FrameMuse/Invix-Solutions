import asyncio
import logging
import secrets
import signal
from typing import Any
from uuid import uuid4

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiohttp import web

from bot import handlers
from bot.api import ProductApi
from bot.config import Settings
from bot.dedupe import DedupeMiddleware
from bot.lease import hold_lease, release_lease, wait_for_lease

logger = logging.getLogger(__name__)


def build_web_app(
    *,
    dispatcher: Dispatcher,
    bot: Bot,
    pool: asyncpg.Pool,
    settings: Settings,
    workflow: dict[str, Any],
    with_webhook: bool,
) -> web.Application:
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        try:
            async with pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
        except Exception:
            return web.json_response({"status": "error"}, status=503)
        return web.json_response({"status": "ok"})

    app.router.add_get("/health", health)

    if with_webhook:

        async def webhook(request: web.Request) -> web.Response:
            provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not settings.bot_webhook_secret or not secrets.compare_digest(
                provided, settings.bot_webhook_secret
            ):
                return web.json_response({"ok": False}, status=401)

            try:
                update = Update.model_validate(await request.json())
            except ValueError:
                return web.json_response({"ok": False}, status=400)

            await dispatcher.feed_update(bot, update, **workflow)
            return web.json_response({"ok": True})

        app.router.add_post("/telegram/webhook", webhook)

    return app


async def start_http_server(
    *,
    dispatcher: Dispatcher,
    bot: Bot,
    pool: asyncpg.Pool,
    settings: Settings,
    workflow: dict[str, Any],
    with_webhook: bool,
) -> web.AppRunner:
    app = build_web_app(
        dispatcher=dispatcher,
        bot=bot,
        pool=pool,
        settings=settings,
        workflow=workflow,
        with_webhook=with_webhook,
    )
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.http_port)
    await site.start()
    return runner


async def wait_for_shutdown(stop: asyncio.Event | None = None) -> None:
    loop = asyncio.get_running_loop()
    stopped = stop if stop is not None else asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stopped.set)

    try:
        await stopped.wait()
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)


async def run_polling(
    *,
    dispatcher: Dispatcher,
    bot: Bot,
    pool: asyncpg.Pool,
    settings: Settings,
    workflow: dict[str, Any],
) -> None:
    runner = await start_http_server(
        dispatcher=dispatcher,
        bot=bot,
        pool=pool,
        settings=settings,
        workflow=workflow,
        with_webhook=False,
    )

    owner = uuid4().hex
    stop = asyncio.Event()
    shutdown = asyncio.create_task(wait_for_shutdown(stop))
    lease_lost = asyncio.Event()
    lease_acquired = False
    heartbeat: asyncio.Task[None] | None = None

    try:
        lease_acquired = await wait_for_lease(pool, owner, stop)
        if not lease_acquired:
            return

        heartbeat = asyncio.create_task(hold_lease(pool, owner, lease_lost))
        polling = asyncio.create_task(
            dispatcher.start_polling(
                bot,
                handle_signals=False,
                close_bot_session=False,
                **workflow,
            )
        )
        done, _ = await asyncio.wait(
            {polling, shutdown, heartbeat},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if (shutdown in done or heartbeat in done) and not polling.done():
            await dispatcher.stop_polling()

        await polling
    finally:
        if heartbeat is not None:
            heartbeat.cancel()
            await asyncio.gather(heartbeat, return_exceptions=True)
        shutdown.cancel()
        await asyncio.gather(shutdown, return_exceptions=True)
        if lease_acquired:
            try:
                await release_lease(pool, owner)
            except Exception as error:
                logger.warning("Failed to release polling lease: %s", error)
        await runner.cleanup()


async def run_webhook(
    *,
    dispatcher: Dispatcher,
    bot: Bot,
    pool: asyncpg.Pool,
    settings: Settings,
    workflow: dict[str, Any],
) -> None:
    runner = await start_http_server(
        dispatcher=dispatcher,
        bot=bot,
        pool=pool,
        settings=settings,
        workflow=workflow,
        with_webhook=True,
    )

    try:
        await bot.set_webhook(
            url=f"{settings.bot_webhook_base_url.rstrip('/')}/telegram/webhook",
            secret_token=settings.bot_webhook_secret,
            allowed_updates=dispatcher.resolve_used_update_types(),
            drop_pending_updates=False,
        )
        await wait_for_shutdown()
    finally:
        await runner.cleanup()


async def run() -> None:
    settings = Settings()

    if not settings.bot_token:
        logger.error("BOT_TOKEN is not set")
        return

    if settings.bot_mode == "webhook" and (
        not settings.bot_webhook_base_url or not settings.bot_webhook_secret
    ):
        logger.error("BOT_WEBHOOK_BASE_URL and BOT_WEBHOOK_SECRET are required in webhook mode")
        return

    pool = await asyncpg.create_pool(settings.asyncpg_dsn, min_size=1, max_size=5)
    product_api = ProductApi(settings.api_url, settings.service_token)
    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(DedupeMiddleware(pool))
    dispatcher.include_router(handlers.router)

    workflow = {"settings": settings, "product_api": product_api}
    logger.info("Bot started in %s mode", settings.bot_mode)

    try:
        if settings.bot_mode == "webhook":
            await run_webhook(
                dispatcher=dispatcher,
                bot=bot,
                pool=pool,
                settings=settings,
                workflow=workflow,
            )
        else:
            await run_polling(
                dispatcher=dispatcher,
                bot=bot,
                pool=pool,
                settings=settings,
                workflow=workflow,
            )
    finally:
        await product_api.close()
        await bot.session.close()
        await pool.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
