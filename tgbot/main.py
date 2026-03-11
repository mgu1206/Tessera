import asyncio
import logging

from telegram.ext import Application

from tgbot.config import settings
from tgbot.events.listener import listen_events
from tgbot.handlers.command import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    app = Application.builder().token(settings.telegram_bot_token).build()
    register_handlers(app)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logger.info("Bot started, launching SSE listener")
    sse_task = asyncio.create_task(
        listen_events(app.bot, settings.telegram_chat_id)
    )

    try:
        await sse_task
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Shutting down")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
