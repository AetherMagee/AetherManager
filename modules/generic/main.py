from aethermanager import bot, events, logger
from modules.generic.strings import *
import database.service as db
import asyncio
from telethon import Button


@logger.catch
@bot.on(events.NewMessage(pattern="/status"))
async def status(msg):
    logger.debug(
        f"Got /status command from ID{msg.sender.id} CHID{msg.chat.id}")
    requesterInfo = db.getUser(msg.sender, createNewIfNone=True)
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


@logger.catch
@bot.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(msg):
    logger.debug(f"Got /start command from ID{msg.sender.id}")
    userFromDB = db.getUser(msg.sender.id)
    if not userFromDB:
        userLangcode = msg.sender.langcode
        if not userLangcode in availableLangCodes:
            userLangcode = "en"
        db.writeUser(msg.sender.id, msg.sender.first_name,
                     msg.sender.last_name, msg.sender.username, msg.sender.phone, userLangcode, True)
    else:
        userLangcode = userFromDB.langcode
    await msg.reply("👋")
    async with bot.action(msg.sender, "typing"):
        await asyncio.sleep(1.25)
        await msg.reply(startStrings["first_" + userLangcode])
        await asyncio.sleep(2)
        await msg.reply(startStrings["second_" + userLangcode])
        await asyncio.sleep(2)
        await msg.reply(startStrings["third_" + userLangcode], link_preview=False,
                        buttons=Button.url(startStrings["third_button_" + userLangcode], "https://t.me/aethermgr_bot?startgroup=start"))


@logger.catch
@bot.on(events.NewMessage(pattern="/who"))
async def who(msg):
    logger.debug(f"Got /who from ID{msg.sender.id} CHID-100{msg.chat.id}")
    if msg.is_reply:
        targetmsg = await msg.get_reply_message()
    userFromDb = db.getUser(targetmsg.sender)
    await msg.reply("Я - дебаг, а ты - чурка, твоя репа с бд - " + str(userFromDb.reputation))

logger.info("Loaded!")
