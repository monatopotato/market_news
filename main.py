import os
import asyncio
import logging
import sys
import aiohttp
from aiohttp import web

import config
from database import init_db
from fetchers.async_news_fetcher import fetch_all_sources
from bot.telegram_notifier import send_telegram_alert, send_digest_summary
from bot.telegram_bot import build_telegram_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint for free web service hosting platforms (Render/Koyeb)."""
    return web.Response(text="🟢 Stock & Fed News Telegram Bot is Running 24/7!", status=200)

async def start_web_server() -> web.AppRunner:
    """Start lightweight HTTP server for Render/Koyeb free web service health checks."""
    port = int(os.getenv("PORT", "10000"))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"HTTP Web Server running on port {port} (Render Free Tier Ready).")
    return runner

async def scanner_loop() -> None:
    """Continuous low-latency news scanner loop for instant major news (Condition 2)."""
    logger.info(f"Starting instant news scanner loop (interval: {config.POLL_INTERVAL_SECONDS}s)...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                logger.debug("Scanning feeds for instant alerts...")
                articles = await fetch_all_sources()
                
                if articles:
                    logger.info(f"Discovered {len(articles)} new market announcement(s).")
                    for article in articles:
                        await send_telegram_alert(session, article)
                        await asyncio.sleep(0.5) # Brief pause between messages
                        
            except asyncio.CancelledError:
                logger.info("Scanner loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in scanner loop: {e}", exc_info=True)

            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)

async def periodic_digest_loop() -> None:
    """Periodic market news summary digest loop every 2 hours (Condition 1)."""
    logger.info(f"Starting periodic digest loop (interval: {config.PERIODIC_DIGEST_INTERVAL_SECONDS}s / {config.PERIODIC_DIGEST_INTERVAL_SECONDS // 3600} hours)...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await asyncio.sleep(config.PERIODIC_DIGEST_INTERVAL_SECONDS)
                logger.info("Triggering periodic 2-hour market news digest...")
                await send_digest_summary(session)
            except asyncio.CancelledError:
                logger.info("Periodic digest loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in periodic digest loop: {e}", exc_info=True)

async def main() -> None:
    """Main application launcher."""
    logger.info("Initializing Stock & Fed News Telegram Bot...")
    init_db()

    # Start HTTP server for Render/Koyeb Free Tier
    web_runner = await start_web_server()

    # Create background scanner and digest tasks
    scanner_task = asyncio.create_task(scanner_loop())
    digest_task = asyncio.create_task(periodic_digest_loop())

    if config.TELEGRAM_BOT_TOKEN:
        logger.info("Starting Telegram Bot interactive polling (Condition 3)...")
        app = build_telegram_app()
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        try:
            # Keep process alive
            await asyncio.gather(scanner_task, digest_task)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Stopping Telegram Bot...")
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            await web_runner.cleanup()
    else:
        logger.warning(
            "TELEGRAM_BOT_TOKEN not configured in environment! "
            "Running in MOCK CONSOLE MODE (alerts will print to logs)."
        )
        try:
            await asyncio.gather(scanner_task, digest_task)
        except KeyboardInterrupt:
            scanner_task.cancel()
            digest_task.cancel()
            await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot execution terminated by user.")
