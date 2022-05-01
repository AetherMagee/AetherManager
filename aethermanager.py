from loguru import logger
from telethon import TelegramClient, events
from telethon.sessions import StringSession as strsession
import config as cfg
import moduleLoader


try:
    bot = TelegramClient(strsession(cfg.STR_SESSION), cfg.API_ID, cfg.API_HASH)
    bot.start()
except Exception:
    logger.exception("Failed to connect to Telegram")
    exit(1)


if __name__ == "__main__":
    moduleLoader.loadAllModules()

    logger.success("Online!")
    bot.run_until_disconnected()
else:
    print("[AetherCore] Being loaded from " + __name__)