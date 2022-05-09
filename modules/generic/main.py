from aethermanager import bot, events, logger
from modules.generic.strings.str import *
from database.dataAccess.dal import *


@logger.catch
@bot.on(events.NewMessage(pattern="/status"))
async def boobs(msg):
    logger.debug(f"Retrieved /status command from ID{msg.sender.id} CHID-100{msg.chat.id}")
    

logger.info("Loaded!")
