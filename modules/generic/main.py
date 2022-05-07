from aethermanager import bot, events, logger
from modules.generic.strings.str import *

@logger.catch
@bot.on(events.NewMessage(pattern="/a"))
async def boobs(msg):
    logger.info("Detected message!")
    print(msg.text)

logger.info("Loaded!")
