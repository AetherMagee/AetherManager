# Welcome to AetherManager
# AetherManager is a new generation of chat managing!
# This bot will protect your chat against unwanted bots
# while keeping it clean!

# Importing stuff
from loguru import logger
from telethon import TelegramClient, events
from telethon.sessions import StringSession as strsession
import confidential as cfg
# Setting up logging
logger.add("logs/basic/basicLog_{time}.log", level="INFO")
logger.add("logs/full/fullLog_{time}.log", level="DEBUG")


# Initializing bot object and connecting to Telegram
try:
    bot = TelegramClient(strsession(cfg.STR_SESSION),
                         cfg.API_ID, cfg.API_HASH, base_logger=logger)
    bot.start(bot_token=cfg.BOT_TOKEN)
except Exception:
    logger.exception("Failed to connect to Telegram")
    exit(1)

# Importing modules
if __name__ == "__main__":

    from moduleLoader import loadAllModules as lmod
    lmod()  # WHY THE FUCK WHEN I USE BASIC IMPORT THIS SHIT DOES NOT WORK, BUT IT DOES WHEN I IMPORT IT WITH "FROM", WHAT THE ACTUAL FUCK

    logger.success("Online!")
    bot.run_until_disconnected()
else:
    logger.debug("Being loaded from " + __name__)
