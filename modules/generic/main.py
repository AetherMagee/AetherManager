from aethermanager import bot, events, logger
from modules.generic.strings import *
import database.service as db


@logger.catch
@bot.on(events.NewMessage(pattern="/status"))
async def status(msg):
    logger.debug(
        f"Got /status command from ID{msg.sender.id} CHID{msg.chat.id}")
    requesterInfo = db.getUser(msg.sender.id, createNewIfNone=True)
    await msg.reply(statusStrings["main_" + requesterInfo.langcode])


@logger.catch
@bot.on(events.NewMessage(pattern="/setlang"))
async def setlang(msg):
    logger.debug(
        f"Got /setlang command from ID{msg.sender.id} CHID{msg.chat.id}")
    langcode = msg.raw_text.replace("/setlang ", "").lower()
    userInfo = db.getUser(msg.sender.id, createNewIfNone=True)
    if len(langcode) == 2 and langcode in availableLangCodes:
        userInfo.langcode = langcode
        db.updateUser(userInfo)
        await msg.reply(setlangStrings["success_" + userInfo.langcode])
    else:
        await msg.reply(setlangStrings["fail_" + userInfo.langcode])


logger.info("Loaded!")
