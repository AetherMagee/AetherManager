# -*- coding: utf-8 -*-
# Importing a TON of shit
import asyncio
from zipfile import ZipFile
import datetime
from datetime import timedelta
import databaseworker as db
import random
import re
import signal
import subprocess
import time
from contextlib import contextmanager
import emoji
import psutil
import requests
import json
import speech_recognition
import telethon.errors
from loguru import logger
from telethon import *
from telethon import Button
from telethon.tl import types
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import *
import codepicgen
import schedule
import threading
logger.add("logs/bot_{time}.log")


try:
    import confidential as conf  # That's my file with data like bot token, etc...
except:
    logger.exception(
        "You have not created the confidential.py file! Please create it. It has to contain the bot token, your API hash/id and your DeepAI token (last one is optional)")
    exit()

# Creating required global variables, aliases and objects
recognizer = speech_recognition.Recognizer()
startTime = time.time()
requests_per_this_session = 0
todo_sec_links = ''
myid = 946202437
botid = int(conf.TOKEN.split(":")[0])
already_changed_rep = []
already_acted = []

filtersDictionary = {}  # <--- WIP
# Planned format: 
# {
#     chatID1: [{(filterString1, filterString2): replyString}, {(filterString3, filterString4): replyString}],
#     chatID2: [filter3String, filter4String]
# }
# Filters will also be stored in DB, but only for shutdown resistance
# DB will be called only in case of restart or filters edit
# Calling DB on every message is going to be extremly slow, so I decided to make something like this


# Initialising bot
bot = TelegramClient('bot', conf.api_id, conf.api_hash).start(bot_token=conf.TOKEN)


# Main shitcode starts here
class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    try:
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
    except:
        logger.error(
            "SIGALRM is not supported on Windows, unable to use timeout! Calculation can hang up endlessly or not work at all!")
        yield
        return
    try:
        yield
    finally:
        signal.alarm(0)


def get_timedelta(string):
    if type(string) is not list:
        try:
            string = string.split(' ')
            string = string[0]
        except:
            return 'Error'
    else:
        try:
            string = string[0]
        except:
            return 'Error'
    try:
        if 'h' in string or 'ч' in string:
            string = string.replace('h', '').replace('ч', '')
            timedelta = timedelta(hours=int(string))
        elif 'm' in string or 'м' in string:
            string = string.replace('м', '').replace('m', '')
            timedelta = timedelta(minutes=int(string))
        elif 'd' in string or 'д' in string:
            string = string.replace('d', '').replace('д', '')
            timedelta = timedelta(days=int(string))
        else:
            timedelta = 'Error'
    except:
        timedelta = 'Error'
    return timedelta


@bot.on(events.NewMessage(pattern='/start'))
@logger.catch
async def start(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    if msg.is_private:
        await asyncio.sleep(0.65)
        await msg.reply("👋")
        async with bot.action(msg.chat, "typing"):
            await asyncio.sleep(1.5)
            await msg.reply("Привет!")
        await asyncio.sleep(1)
        async with bot.action(msg.chat, "typing"):
            await asyncio.sleep(2)
            await msg.reply(
                "Я - бот, который поможет тебе управлять своим чатом! Для начала, давай добавим меня в твой чат и выдадим разрешения.")
        await asyncio.sleep(1)
        async with bot.action(msg.chat, "typing"):
            await asyncio.sleep(3.25)
            await msg.reply(
                "[Нажми здесь](https://t.me/aethermgr_bot?startgroup=start) или по кнопке ниже, чтобы добавить меня в чат",
                buttons=Button.url("Добавить в чат", "https://t.me/aethermgr_bot?startgroup=start"), link_preview=False)


@bot.on(events.NewMessage(pattern='/who|ты кто'))
@logger.catch
async def info_get(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    foundTarget = False
    if msg.is_reply:
        targetMsg = await msg.get_reply_message()
        target = targetMsg.sender
        foundTarget = True
    if not foundTarget:
        cleanSearchRequest = msg.raw_text.replace('/who ', '').replace('ты кто ', '').replace('/who@aethermgr_bot', '')
        try:
            target = await bot.get_entity(cleanSearchRequest)
            if not type(target) == telethon.tl.types.Channel:
                foundTarget = True
            else:
                raise "channel"
        except:
            targetID = db.searchUserByAltName(cleanSearchRequest)
            if targetID != "NotFound":
                target = await bot.get_entity(targetID)
                foundTarget = True
    if not foundTarget:
        await msg.reply("❌ **__Аккаунт не найден__**")
        return
    userDataFromDB = db.getUserEntry(target.id)
    if userDataFromDB == "NotFound":
        coins = "0"
        rep = "0"
        db.addUserEntry(target.id, target.username, target.phone)
    else:
        rep = str(userDataFromDB[0][3])
        coins = str(userDataFromDB[0][4])
    altNamesRaw = db.getAltNames(target.id)
    if not bool(altNamesRaw):
        altNames = "Отсутствуют"
    else:
        altNames = ""
        for name in altNamesRaw:
            if altNames != "":
                splitter = " | "
            else:
                splitter = ""
            altNames += splitter + str(name)
    if target.username:
        username = f"[{target.username}](tg://openmessage?user_id={target.id})"
    else:
        username = "Отсутствует"
    spyglass = await msg.reply("🔎")
    text = f"""🔎Имя: **__{target.first_name} {target.last_name if bool(target.last_name) else ""}__**
🔎Имя пользователя: **__{username}__**
⭐Telegram ID: **__{target.id}__**
↗Репутация: **__{rep}__**
💲AetherCoin'ов: **__{coins}__**
👨‍👩‍👧‍👧Альт. имена: **__{altNames}__**
"""
    await spyglass.delete()
    await msg.reply(text)


@bot.on(events.NewMessage(pattern=r'(?i)реп\+'))
@logger.catch
async def rep_plus(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    global already_changed_rep

    # Checks
    if not msg.is_reply: return
    targetMsg = await msg.get_reply_message()
    target = targetMsg.sender
    if msg.sender.id in already_changed_rep:
        return
    if msg.sender.id == target.id:
        myReply = await msg.reply("❌ **__Редактирование своей репутации запрещено__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return

    # Modifying the reputation
    currentReputation = db.getUserEntry(target.id, objectToReturn="reputation")
    if currentReputation == "NotFound":
        db.addUserEntry(target.id)
        await rep_plus(msg)
        return
    newReputation = str(int(currentReputation) + 1)
    db.editUserEntry(target.id, "reputation", newReputation)
    myReply = await msg.reply("✅ **__Поднял пользователю репутацию__**")
    already_changed_rep.append(msg.sender.id)
    await asyncio.sleep(2)
    await myReply.delete()
    await asyncio.sleep(28)
    already_changed_rep.remove(msg.sender.id)


@bot.on(events.NewMessage(pattern=r'(?i)реп-'))
@logger.catch
async def rep_minus(msg):
    global requests_per_this_session
    requests_per_this_session += 1

    # Checks
    if not msg.is_reply: return
    targetMsg = await msg.get_reply_message()
    target = targetMsg.sender
    if msg.sender.id in already_changed_rep:
        return
    if msg.sender.id == target.id:
        myReply = await msg.reply("❌ **__Редактирование своей репутации запрещено__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return

    # Modifying the reputation
    currentReputation = db.getUserEntry(target.id, objectToReturn="reputation")
    if currentReputation == "NotFound":
        db.addUserEntry(target.id)
        await rep_minus(msg)
        return
    newReputation = str(int(currentReputation) + 1)
    db.editUserEntry(target.id, "reputation", newReputation)
    myReply = await msg.reply("✅ **__Понизил пользователю репутацию__**")
    already_changed_rep.append(msg.sender.id)
    await asyncio.sleep(2)
    await myReply.delete()
    await asyncio.sleep(28)
    already_changed_rep.remove(msg.sender.id)


@bot.on(events.NewMessage(pattern='/remember *', func=lambda x: x.is_reply and not x.is_private))
@logger.catch
async def altNameAddCommand(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    requester_perms = await bot.get_permissions(msg.chat_id, msg.sender)
    # Checking if person is an admin
    if not requester_perms.is_admin:
        await msg.reply('❌ **__Эта команда доступна только админам__**')
    else:
        reply = await msg.get_reply_message()
        # Cleaning up the input
        nameToSave = msg.raw_text.lower().replace('/remember ', '').replace('/remember@aethermgr_bot ', '').replace(
            '/remember', '').replace('/remember@aethermgr_bot', '').replace('\"', '').replace('\'', '').replace("\\",
                                                                                                                '').replace(
            ";", "")
        while "  " in nameToSave:
            nameToSave - nameToSave.replace("  ", " ")
        # Checking if name is too short or too long
        if len(nameToSave) < 5 or len(nameToSave) > 25:
            await msg.reply("❌ **__Указанное имя не подходит по длинне! (От 5 до 25 символов)__**")
            return
        # Writing
        funcOutput = db.addAltName(reply.sender.id, nameToSave)
        # Getting write result
        if funcOutput == 'Success':
            await msg.reply("✅ **__Имя успешно установлено__**")
        elif funcOutput == 'AlreadyClaimedError':
            await msg.reply("❌ **__Имя уже занято__**")
        elif funcOutput == 'DoesNotExistsInDBError':
            await msg.reply(
                "**__Произошла ошибка, уже запущены механизмы исправления. Попробуйте ещё раз примерно через минуту__**")
            await parseAllUsers(msg)


@bot.on(events.NewMessage(pattern='/helpme'))
@logger.catch
async def help(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    pureCommand = msg.text.replace("/helpme@aethermgr_bot", "").replace("/helpme", "").replace(" ", "")
    availibleCommands = {"aboutbot": "**__Информация о боте и данные о его создателях__**",
                         "who": "**__Получение информации о пользователе.\n\nИспользование: /who @username | /who альт.имя | /who (ответом на сообщение необходимого пользователя)__**",
                         "rep": "**__Повышает/понижает репутацию пользователю. \n\nИспользование: \"реп+\" ответом на сообщение пользователя__**",
                         "remember": "**__Добавляет пользователю альтернативное имя. Доступно только админам. \n\nИспользование: /remember ИМЯ - ответом на сообщение пользователя__**",
                         "forget": "**__Удаляет альтернативное имя пользователя. \n\nИспользование: По аналогии с /remember__**",
                         "anon": "**__Выводит помощь по механике анонимных сообщений__**",
                         "administration": "**__Базовые команды для администрирования чата: mute, ban, другие.\n\nИспользование: Так же, как и в других ботах__**",
                         "report": "**__Отправка жалобы на пользователя администратором путём рассылки уведомления в личные сообщения администраторов (требует от администраторов запущенного диалога с ботом)\n\nИспользование: /report ПРИЧИНА - ответом на сообщение пользователя__**",
                         "cube": "**__Сыграть с ботом в кубик\n\nАльтернативная команда: /dice__**",
                         "darts": "**__Сыграть с ботом в дартс__**",
                         "save": "**__Сохранение заметки\n\nИспользование: /save имя.заметки - в ответ на сообщение__**",
                         "get": "**__Получение заметки\n\nИспользование: /get имя.заметки__**",
                         "notes": "**__Получение всех заметок в чате__**",
                         "delnote": "**__Удаление заметки\n\nИспользование: /delnote имя.заметки__**",
                         "settings": "**__Просмотр доступных для изменения параметров__**",
                         "set": "**__Установка параметра для чата. \n\nИспользование: /set название.параметра значение.из./settings__**",
                         "getsettings": "**__Просмотр всех установленных значений__**",
                         "baltop": "**__Получение лидеров чата по балансу__**",
                         "reptop": "**__Получение лидеров чата по репутации__**",
                         "checkdb": "**__Ручная проверка базы данных. Используйте, если испытываете проблемы с командами /set, /settings и /getsettings__**"
                         }
    try:
        await msg.reply(f"Помощь по команде /{pureCommand}:\n\n{availibleCommands[pureCommand]}")
    except KeyError:
        commandsList = ""
        for key in availibleCommands.keys():
            commandsList += "`" + key + "`\n"
        await msg.reply("Вы не указали команду.\n\nДоступные команды:\n" + commandsList)
    except Exception as m:
        await msg.reply("**__Произошла ошибка__**")
        raise m


@bot.on(events.NewMessage(pattern='рестарт|/restart', from_users=myid))
@logger.catch
async def restart(msg):
    my = await bot.send_message(msg.chat_id, '🕗 **__Окей, перезагружаюсь...__**', reply_to=msg)
    os.system('echo {},{} >> after-restart'.format(str(msg.chat_id), str(my.id)))
    os.system('pkill python3')


@logger.catch
async def check_for_ad(event):
    user = await bot(GetFullUserRequest(event.user))
    forbidden = ["🍓", "Wewbsz6IMYxmMmMy", "joinchat"]
    for word in forbidden:
        if word in user.about:
            return True
    emoji_count = 0
    for character in user.first_name + " " + user.last_name:
        if character in emoji.UNICODE_EMOJI:
            if emoji_count < 3:
                emoji_count += 1
            else:
                return True
    return False


@logger.catch
async def captcha(event):
    code = str(random.randint(1000, 9999))
    codepicgen.generate(code)
    code_notify = await event.reply(
        "⚠️ **__Приветствую! Вам необходимо пройти дополнительную проверку. Ответьте на это сообщение кодом с картинки в течении следующих 10 секунд.__**",
        file=f"temp/code_{code}.jpg")
    subprocess.run(f"del temp\\code_{code}.jpg || rm -f temp/code_{code}.jpg", shell=True)
    try:
        async with bot.conversation(event.chat, timeout=10) as conv:
            reply = await conv.get_reply(code_notify)
            while not reply.text.isnumeric() or not event.user.id == reply.sender.id:
                reply = await conv.get_reply(code_notify)
    except asyncio.exceptions.TimeoutError:
        try:
            await code_notify.delete()
            await event.delete()
        except:
            pass
        try:
            await bot.kick_participant(event.chat, event.user)
        except:
            return 'Error'
        return 'NotPass'
    if reply.text == code:
        success = await event.reply("✅ **__Вы прошли проверку!__**")
        try:
            await code_notify.delete()
            await reply.delete()
        except:
            pass
        await asyncio.sleep(1)
        await success.delete()
        return 'Pass'
    else:
        try:
            await code_notify.delete()
            await event.delete()
            await reply.delete()
        except:
            pass
        await bot.kick_participant(event.chat, event.user)
        return 'NotPass'


@logger.catch
async def say_hello(event, custom_hello):
    if custom_hello != 'None':
        greeting = await bot.get_messages(-1001766720438, ids=int(custom_hello))
        await event.reply(greeting)
    else:
        await event.reply("Привет!")


@logger.catch
async def notify_admins(chat, text):
    notified = 0
    async for admin in bot.iter_participants(chat, filter=ChannelParticipantsAdmins):
        if admin.lang_code:
            try:
                await bot.send_message(admin, text)
                notified += 1
            except:
                logger.error("Failed to notify " + admin.first_name)
    return notified


@bot.on(events.ChatAction)
@logger.catch
async def hello(event):
    user = await bot.get_entity(event.user_id)
    if event.user_joined:
        chatInfoFromDB = db.getSettingsForChat(event.chat_id, "custom_hello, captcha")
        if chatInfoFromDB[0][1] == "on":
            captchaResult = await captcha(event)
            if captchaResult == "Pass":
                await say_hello(event, chatInfoFromDB[0][0])
            elif captchaResult == "NotPass":
                try:
                    await bot.edit_permissions(event.chat, user, view_messages=False)
                    await bot.edit_permissions(event.chat, user, view_messages=True)
                    return
                except:
                    await notify_admins(event.chat,
                                        f"🔔 **__Сервисное уведомление из {event.chat.title}\nБоту не удалось исключить из чата пользователя, не прошедшего капчу. Пожалуйста, проверьте разрешения бота в чате. Если вы считаете, что проблема не в них, используйте /bugreport в чате, указанном выше")
                    return
            else:
                await notify_admins(event.chat,
                                    f"🔔 **__Сервисное уведомление из {event.chat.title}\nВо время работы капчи произошла ошибка. Пожалуйста, проверьте разрешения бота в чате. Если вы считаете, что проблема не в них, используйте /bugreport в указанном выше чате__**")
                return

        if chatInfoFromDB[0][1] == "adonly":
            adBot = False
            fullUserEntity = await bot(GetFullUserRequest(event.user))
            forbiddenWordsInDescription = ["t.me", "joinchat", "🍓"]
            forbiddenWordsInName = ["link", "desc", "сылк", "описани"]
            for word in forbiddenWordsInDescription:
                if word in str(fullUserEntity.about):
                    adBot = True
                    break
            for word in forbiddenWordsInName:
                if word in str(fullUserEntity.about):
                    adBot = True
                    break
            if adBot:
                captchaResult = await captcha(event)
                if captchaResult == "Pass":
                    await say_hello(event, chatInfoFromDB[0][0])
                elif captchaResult == "NotPass":
                    try:
                        await bot.edit_permissions(event.chat, user, view_messages=False)
                        await bot.edit_permissions(event.chat, user, view_messages=True)
                        return
                    except:
                        await notify_admins(event.chat,
                                            f"🔔 **__Сервисное уведомление из {event.chat.title}\nБоту не удалось исключить из чата пользователя, не прошедшего капчу. Пожалуйста, проверьте разрешения бота в чате. Если вы считаете, что проблема не в них, используйте /bugreport в чате, указанном выше")
                        return
                else:
                    await notify_admins(event.chat,
                                        f"🔔 **__Сервисное уведомление из {event.chat.title}\nВо время работы капчи произошла ошибка. Пожалуйста, проверьте разрешения бота в чате. Если вы считаете, что проблема не в них, используйте /bugreport в указанном выше чате__**")
                    return

        if chatInfoFromDB[0][1] == "off":
            await say_hello(event, chatInfoFromDB[0][0])

    if event.user_added and user.id == botid:
        await asyncio.sleep(1.5)
        await event.reply("👋")
        async with bot.action(event.chat, "typing"):
            await asyncio.sleep(4)
            await bot.send_message(event.chat, "**__Привет, чат!__**")
        chatInDB = db.getSettingsForChat(event.chat_id)
        if chatInDB == "ChatNotFound":
            funcOut = db.addChatEntry(event.chat_id)
            if funcOut == "Error":
                await notify_admins(event.chat,
                                    f"🔔 **__Сервисное уведомление из {event.chat.title}\nСожалею, что надоедаю уведомлениями с самого момента добавления, но во время добавления вашего чата в базу данных произошла ошибка. Пожалуйста, используйте /bugreport в чате, указанном выше")
                return
            await parseAllUsers(event.chat)


# @bot.on(events.ChatAction)
# @logger.catch
# async def hello(event):
#     user = await bot.get_entity(event.user_id)
#     if event.user_joined:
#         cursor.execute(f"SELECT custom_hello, captcha FROM settings WHERE chat_id = {event.chat_id}")
#         custom_hello, captcha_status = cursor.fetchone()
#         if captcha_status == 'on':
#             result = await captcha(event)
#             if result == 'Pass':
#                 await say_hello(event, custom_hello)
#             elif result == 'Error':
#                 await notify_admins(event.chat, f"🔔 **__Сервисное уведомление из {event.chat.title}\nВо время работы капчи произошла ошибка. Пожалуйста, проверьте разрешения бота в чате. Если вы считаете, что проблема не в них, используйте /bugreport в указанном выше чате__**")
#             else:
#                 pass
#         elif captcha_status == 'ad_only':
#             ad_bot = False
#             full_user_instance = await bot(GetFullUserRequest(event.user))
#             forbidden_words_desc = ['t.me', 'joinchat', '🍓']
#             forbidden_words_name = ["link", "desc", "описание"]
#             for word in forbidden_words_desc:
#                 if word in str(full_user_instance.about):
#                     ad_bot = True
#             for word in forbidden_words_name:
#                 if word in str(user.first_name) + " " + str(user.last_name):
#                     ad_bot = True
#             if ad_bot:
#                 result = await captcha(event)
#                 if result == 'Pass':
#                     await say_hello(event, custom_hello)
#                 elif result == 'Error':
#                     await notify_admins(event.chat, f"🔔 **__Сервисное уведомление из {event.chat.title}\nВо время работы капчи произошла ошибка. Пожалуйста, проверьте разрешения бота в чате. Если вы считаете, что проблема не в них, используйте /bugreport в указанном выше чате__**")
#                 else:
#                     pass
#             else:
#                 await say_hello(event, custom_hello)
#         else:
#             await say_hello(event, custom_hello)
#     if event.user_added:
#         if not user.bot:
#             await event.reply('Интересно, не против ли его воли его сюда добавили?')
#         elif user.id == 2028159238:
#             logger.info('Обнаружил добавление в новый чат ({chid})'.format(chid=str(event.chat.title)))
#             cursor.execute(f"SELECT EXISTS(SELECT * FROM settings WHERE chat_id = {event.chat_id})")
#             if not bool(cursor.fetchone()[0]):
#                 cursor.execute(f"INSERT INTO settings (chat_id) VALUES ({event.chat_id})")
#                 db_main.commit()
#                 logger.info("Записал настройки для чата")
#             else:
#                 logger.info('Настройки чата уже есть в базе.')
#             async with bot.action(event.chat, "typing"):
#                 await asyncio.sleep(random.randint(1,3))
#             await event.reply("👋")
#             async with bot.action(event.chat, "typing"):
#                 await asyncio.sleep(random.randint(1,3))
#             await event.reply(
#                 '**__Здрасьте :P\nЯ - бот, призванный упростить администрирование групп\nБольше обо мне можно узнать с помощью /helpme и /aboutbot__**')
#             await parseall(event)
#         else:
#             await event.reply('Кхем...')


@bot.on(events.NewMessage(pattern=r'(?i)бот'))
@logger.catch
async def ping(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    result = str(db.getSettingsForChat(msg.chat_id, "react_on_ping")[0][0])
    if result == '1':
        e = msg.raw_text.split(' ')
        if not len(e) > 1:
            if not msg.is_reply:
                logger.info('Got a ping from ' + msg.sender.first_name)
                answer_list = ['что?', "✅ Онлайн", 'чё?', '?', "✅ Онлайн", 'слава украине', "✅ Онлайн",
                               "чё надо", 'м', 'онлине', "ацтань, я дед инсайд", "👋"]
                select = random.randint(0, len(answer_list) - 1)
                await msg.reply(answer_list[select])


@bot.on(events.NewMessage(pattern=r'(?i)мут|/mute', func=lambda x: not x.is_private))
@logger.catch
async def mute(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    msgTextSplit = msg.raw_text.lower().replace('мут ', '').replace('/mute ', '').replace('мут', '').replace('/mute',
                                                                                                             '').split(
        ' ')
    # Checking requester permissions
    try:
        requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
        if not requesterPermissions.ban_users:
            await msg.reply("❌ **__Вы не являетесь админом__**")
            return
    except:
        await msg.reply("❌ **__Произошла ошибка. Попробуйте позже__**")
        return

    found = False
    # Trying to get target from reply
    if msg.is_reply:
        targetMsg = await msg.get_reply_message()
        target = targetMsg.sender
        found = True
    if not found:
        # Trying to get target by get_entity()
        try:
            target = await bot.get_entity(msgTextSplit[0].replace("@", ""))
            msgTextSplit.remove(msgTextSplit[0])
            found = True
        except:
            try:
                target = await bot.get_entity(int(msgTextSplit[0].replace("@", "")))
                msgTextSplit.remove(msgTextSplit[0])
                found = True
            except:
                found = False
    if not found:
        # Finally, if none of above worked, searching user by altname
        altNameCurrentString = ""
        for word in msgTextSplit:
            if not found:
                if altNameCurrentString == "":
                    altNameCurrentString = word
                else:
                    altNameCurrentString = altNameCurrentString + " " + word
                result = db.searchUserByAltName(altNameCurrentString)
                if result != "NotFound":
                    target = await bot.get_entity(result)
                    found = True
            else:
                break
    if not found:
        await msg.reply("❌ **__Пользователь не найден__**")
        return

    # Finally, muting
    try:
        targetPermissions = await bot.get_permissions(msg.chat, target)
    except Exception as e:
        logger.warning(str(e))
        myReply = await msg.reply("❌ **__В данный момент пользователь не находится в чате__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    myPermissions = await bot.get_permissions(msg.chat, botid)
    if not myPermissions.ban_users or not myPermissions.delete_messages:
        myReply = await msg.reply(
            "❌ **__У меня недостаточно прав для этого. Пожалуйста, уведомите создателя чата, что для моей корректной работы требуются следующие разрешения: Удаление сообщений, Блокировка участников__**")
        await asyncio.sleep(7.5)
        await myReply.delete()
        return
    if not targetPermissions.is_admin:
        timedelta = get_timedelta(msgTextSplit)  # <- TODO: Rewrite this sh*t
        if timedelta != "Error":
            await bot.edit_permissions(msg.chat, target, timedelta, send_messages=False)
            myReply = await msg.reply("✅ **__Готово, пользователь был замучен__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        else:
            # Same actions, just without timedelta
            await bot.edit_permissions(msg.chat, target, send_messages=False)
            myReply = await msg.reply("✅ **__Готово, пользователь был замучен__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
    else:
        # Here the real sh*t comes...
        # First of all, lets check if we even allowed to mute an admin...
        muteAdmins = db.getSettingsForChat(msg.chat_id, "mute_admins_allowed")
        if muteAdmins == "ChatNotFound": db.addChatEntry(msg.chat_id); await mute(msg)
        if not bool(muteAdmins):
            myReply = await msg.reply(
                "❌ **__Функция MuteAdmins в настоящее время отключена в этом чате. Если вы - создатель чата, используйте /settings для подробностей__**")
            await asyncio.sleep(7.5)
            await myReply.delete()
            return
        # Now we are sure that we can mute the user, so we can continue...
        functionOutput = db.registerNewMutedAdmin(target.id, msg.chat_id, "muteRequest")
        if functionOutput == "AlreadyMutedError":
            myReply = await msg.reply("❌ **__Пользователь уже находится в муте__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        myReply = await msg.reply("✅ **__Готово, пользователь был замучен__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return


@bot.on(events.NewMessage(pattern=r'(?i)размут|/unmute', func=lambda x: not x.is_private))
@logger.catch
async def unmute(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    msgTextSplit = msg.raw_text.lower().replace('размут ', '').replace('/unmute ', '').replace('размут', '').replace(
        '/unmute', '').split(' ')
    # Checking requester permissions
    try:
        requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
        if not requesterPermissions.ban_users:
            await msg.reply("❌ **__Вы не являетесь админом__**")
            return
    except:
        await msg.reply("❌ **__Произошла ошибка. Попробуйте позже__**")
        return

    found = False
    # Trying to get target from reply
    if msg.is_reply:
        targetMsg = await msg.get_reply_message()
        target = targetMsg.sender
        found = True
    if not found:
        # Trying to get target by get_entity()
        try:
            target = await bot.get_entity(msgTextSplit[0])
            if not target.left:
                msgTextSplit.remove(msgTextSplit[0])
                found = True
        except:
            try:
                target = await bot.get_entity(int(msgTextSplit[0]))
                if not target.left:
                    msgTextSplit.remove(msgTextSplit[0])
                    found = True
            except:
                found = False
    if not found:
        # Finally, if none of above worked, searching user by altname
        altNameCurrentString = ""
        for word in msgTextSplit:
            if not found:
                if altNameCurrentString == "":
                    altNameCurrentString = word
                else:
                    altNameCurrentString + " " + word
                result = db.searchUserByAltName(altNameCurrentString)
                if result != "NotFound":
                    target = await bot.get_entity(result)
                    found = True
            else:
                break
    if not found:
        await msg.reply("❌ **__Пользователь не найден__**")
        return

    # Finally, muting
    try:
        targetPermissions = await bot.get_permissions(msg.chat, target)
    except:
        myReply = await msg.reply("❌ **__В данный момент пользователь не находится в чате__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    myPermissions = await bot.get_permissions(msg.chat, botid)
    if not myPermissions.ban_users or not myPermissions.delete_messages:
        myReply = await msg.reply(
            "❌ **__У меня недостаточно прав для этого. Пожалуйста, уведомите создателя чата, что для моей корректной работы требуются следующие разрешения: Удаление сообщений, Блокировка участников__**")
        await asyncio.sleep(7.5)
        await myReply.delete()
        return
    if not targetPermissions.is_admin:
        await bot.edit_permissions(msg.chat, target, send_messages=True)
        myReply = await msg.reply("✅ **__Готово, пользователь был размучен__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    else:
        functionOutput = db.deleteMutedAdmin(target.id, msg.chat_id)
        if functionOutput == "Success":
            text = "✅ **__Готово, пользователь был размучен__**"
        elif functionOutput == "NotMuted":
            text = "❌ **__Пользователь не находится в муте__**"
        else:
            text = "❌ **__Произошла ошибка, пожалуйста, попробуйте еще раз. Если не поможет, можно отключить мут админов - `/set MuteAdmins 0'__**"
        myReply = await msg.reply(text)
        await asyncio.sleep(7)
        await myReply.delete()


@bot.on(events.NewMessage(pattern=r'(?i)бан|/ban', func=lambda x: not x.is_private))
@logger.catch
async def ban(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    msgTextSplit = msg.raw_text.lower().replace('бан ', '').replace('/ban ', '').replace('бан', '').replace('/ban',
                                                                                                            '').split(
        ' ')
    # Checking requester permissions
    try:
        requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
        if not requesterPermissions.ban_users:
            await msg.reply("❌ **__Вы не являетесь админом__**")
            return
    except:
        await msg.reply("❌ **__Произошла ошибка. Попробуйте позже__**")
        return

    found = False
    # Trying to get target from reply
    if msg.is_reply:
        targetMsg = await msg.get_reply_message()
        target = targetMsg.sender
        found = True
    if not found:
        # Trying to get target by get_entity()
        try:
            target = await bot.get_entity(msgTextSplit[0])
            if not target.left:
                msgTextSplit.remove(msgTextSplit[0])
                found = True
        except:
            try:
                target = await bot.get_entity(int(msgTextSplit[0]))
                if not target.left:
                    msgTextSplit.remove(msgTextSplit[0])
                    found = True
            except:
                found = False
    if not found:
        # Finally, if none of above worked, searching user by altname
        altNameCurrentString = ""
        for word in msgTextSplit:
            if not found:
                if altNameCurrentString == "":
                    altNameCurrentString = word
                else:
                    altNameCurrentString + " " + word
                result = db.searchUserByAltName(altNameCurrentString)
                if result != "NotFound":
                    target = await bot.get_entity(result)
                    found = True
            else:
                break
    if not found:
        await msg.reply("❌ **__Пользователь не найден__**")
        return

    # Finally, muting
    try:
        targetPermissions = await bot.get_permissions(msg.chat, target)
    except:
        myReply = await msg.reply("❌ **__В данный момент пользователь не находится в чате__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    myPermissions = await bot.get_permissions(msg.chat, botid)
    if not myPermissions.ban_users or not myPermissions.delete_messages:
        myReply = await msg.reply(
            "❌ **__У меня недостаточно прав для этого. Пожалуйста, уведомите создателя чата, что для моей корректной работы требуются следующие разрешения: Удаление сообщений, Блокировка участников__**")
        await asyncio.sleep(7.5)
        await myReply.delete()
        return
    if not targetPermissions.is_admin:
        timedelta = get_timedelta(msgTextSplit)
        if timedelta != "Error":
            await bot.edit_permissions(msg.chat, target, timedelta, view_messages=False)
            myReply = await msg.reply("✅ **__Готово, пользователь был забанен__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        else:
            # Same actions, just without timedelta
            await bot.edit_permissions(msg.chat, target, view_messages=False)
            myReply = await msg.reply("✅ **__Готово, пользователь был забанен__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
    else:
        myReply = await msg.reply("❌ **__Пользователь является админом__**")
        await asyncio.sleep(5)
        await myReply.delete()


@bot.on(events.NewMessage(pattern=r'(?i)разбан|/unban', func=lambda x: not x.is_private))
@logger.catch
async def unban(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    msgTextSplit = msg.raw_text.lower().replace('разбан ', '').replace('/unban ', '').replace('разбан', '').replace(
        '/unban', '').split(' ')
    # Checking requester permissions
    try:
        requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
        if not requesterPermissions.ban_users:
            await msg.reply("❌ **__Вы не являетесь админом__**")
            return
    except:
        await msg.reply("❌ **__Произошла ошибка. Попробуйте позже__**")
        return

    found = False
    # Trying to get target from reply
    if msg.is_reply:
        targetMsg = await msg.get_reply_message()
        target = targetMsg.sender
        found = True
    if not found:
        # Trying to get target by get_entity()
        try:
            target = await bot.get_entity(msgTextSplit[0])
            if not target.left:
                msgTextSplit.remove(msgTextSplit[0])
                found = True
        except:
            try:
                target = await bot.get_entity(int(msgTextSplit[0]))
                if not target.left:
                    msgTextSplit.remove(msgTextSplit[0])
                    found = True
            except:
                found = False
    if not found:
        # Finally, if none of above worked, searching user by altname
        altNameCurrentString = ""
        for word in msgTextSplit:
            if not found:
                if altNameCurrentString == "":
                    altNameCurrentString = word
                else:
                    altNameCurrentString + " " + word
                result = db.searchUserByAltName(altNameCurrentString)
                if result != "NotFound":
                    target = await bot.get_entity(result)
                    found = True
            else:
                break
    if not found:
        await msg.reply("❌ **__Пользователь не найден__**")
        return

    # Finally, muting
    myPermissions = await bot.get_permissions(msg.chat, botid)
    if not myPermissions.ban_users or not myPermissions.delete_messages:
        myReply = await msg.reply(
            "❌ **__У меня недостаточно прав для этого. Пожалуйста, уведомите создателя чата, что для моей корректной работы требуются следующие разрешения: Удаление сообщений, Блокировка участников__**")
        await asyncio.sleep(7.5)
        await myReply.delete()
        return
    try:
        await bot.edit_permissions(msg.chat, target, send_messages=True)
        myReply = await msg.reply("✅ **__Готово, пользователь был размучен__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    except:
        pass


@bot.on(events.NewMessage(pattern=r'(?i)кик|/kick', func=lambda x: not x.is_private))
@logger.catch
async def kick(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    msgTextSplit = msg.raw_text.lower().replace('кик ', '').replace('/kick ', '').replace('кик', '').replace('/kick',
                                                                                                             '').split(
        ' ')
    # Checking requester permissions
    try:
        requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
        if not requesterPermissions.ban_users:
            await msg.reply("❌ **__Вы не являетесь админом__**")
            return
    except:
        await msg.reply("❌ **__Произошла ошибка. Попробуйте позже__**")
        return

    found = False
    # Trying to get target from reply
    if msg.is_reply:
        targetMsg = await msg.get_reply_message()
        target = targetMsg.sender
        found = True
    if not found:
        # Trying to get target by get_entity()
        try:
            target = await bot.get_entity(msgTextSplit[0])
            if not target.left:
                msgTextSplit.remove(msgTextSplit[0])
                found = True
        except:
            try:
                target = await bot.get_entity(int(msgTextSplit[0]))
                if not target.left:
                    msgTextSplit.remove(msgTextSplit[0])
                    found = True
            except:
                found = False
    if not found:
        # Finally, if none of above worked, searching user by altname
        altNameCurrentString = ""
        for word in msgTextSplit:
            if not found:
                if altNameCurrentString == "":
                    altNameCurrentString = word
                else:
                    altNameCurrentString + " " + word
                result = db.searchUserByAltName(altNameCurrentString)
                if result != "NotFound":
                    target = await bot.get_entity(result)
                    found = True
            else:
                break
    if not found:
        await msg.reply("❌ **__Пользователь не найден__**")
        return

    # Finally, muting
    try:
        targetPermissions = await bot.get_permissions(msg.chat, target)
    except:
        myReply = await msg.reply("❌ **__В данный момент пользователь не находится в чате__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    myPermissions = await bot.get_permissions(msg.chat, botid)
    if not myPermissions.ban_users or not myPermissions.delete_messages:
        myReply = await msg.reply(
            "❌ **__У меня недостаточно прав для этого. Пожалуйста, уведомите создателя чата, что для моей корректной работы требуются следующие разрешения: Удаление сообщений, Блокировка участников__**")
        await asyncio.sleep(7.5)
        await myReply.delete()
        return
    if not targetPermissions.is_admin:
        await bot.kick_participant(msg.chat, target)
        myReply = await msg.reply("✅ **__Готово, пользователь был кикнут__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    else:
        myReply = await msg.reply("❌ **__Пользователь является админом__**")
        await asyncio.sleep(5)
        await myReply.delete()


@bot.on(events.NewMessage(pattern='/act '))
@logger.catch
async def me(msg):
    global requests_per_this_session
    global already_acted
    if msg.sender.id in already_acted:
        return
    requests_per_this_session += 1
    chid = msg.chat_id
    m = msg.raw_text
    firstname = msg.sender.first_name
    m = m.replace('/act ', '')
    await msg.delete()
    await bot.send_message(chid, '* **__{fname} {action}__**'.format(fname=firstname, action=m))
    already_acted.append(msg.sender.id)
    await asyncio.sleep(30)
    already_acted.remove(msg.sender.id)


@bot.on(events.NewMessage(pattern="/parseall", from_users=myid))
@logger.catch
async def parseAllUsers(event):
    logger.debug(f"Starting parse in {event.chat.title}")
    importedAmount = 0
    erroredAmount = 0
    async for user in bot.iter_participants(event.chat):
        functionOutput = db.addUserEntry(user.id, withCommit=False)
        if functionOutput == "Success":
            importedAmount += 1
        else:
            erroredAmount += 1
    db.usersDB.commit()
    db.altnamesDB.commit()
    logger.debug(f"Parse in {event.chat.title} complete, imported {str(importedAmount)}, errored {str(erroredAmount)}")


@bot.on(events.NewMessage(pattern=r'(?i)чатид'))
@logger.catch
async def chatid(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    await msg.reply('`' + str(msg.chat_id) + '`')


@bot.on(events.NewMessage(pattern='/forget *', func=lambda x: not x.is_private))
@logger.catch
async def db_erase_handler(msg):
    if msg.is_reply:
        global requests_per_this_session
        requests_per_this_session += 1
        try:
            requester_perms = await bot.get_permissions(msg.chat_id, msg.sender.id)
        except ValueError:
            return
        if requester_perms.is_admin:
            reply = await msg.get_reply_message()
            if reply.sender.id == msg.sender.id:
                await msg.reply("❌ **__Вы не можете удалять свои альтернативные имена__**")
                return
            altname = msg.raw_text.replace("/forget ", "").replace("forget@aethermgr_bot", "").lower()
            function_output = db.deleteAltName(reply.sender.id, altname)
            if function_output == "Success":
                myReply = await msg.reply("✅ **__Удалил это имя__**")
            elif function_output == 'DoesNotExistsError':
                myReply = await msg.reply('❌ **__Имя отсуствует в базе__**')
            else:
                myReply = await msg.reply("❌ **__Произошла ошибка__**")
            await asyncio.sleep(7)
            await myReply.delete()
        else:
            await msg.reply('❌ **__Вы не являетесь админом__**')


@bot.on(events.NewMessage(func=lambda x: not x.is_private))
@logger.catch
async def muteAdminsWorker(msg):
    try:
        targetPerms = await bot.get_permissions(msg.chat, msg.sender)
    except:
        logger.warning(f"Error while getting permissions of {msg.sender.id} in {msg.chat_id}, msgid: {msg.id}")
        return
    if targetPerms.is_admin:
        checkIfIsMutedResult = db.checkMutedAdmin(msg.sender.id, msg.chat_id)
        if not bool(str(checkIfIsMutedResult[0])):
            return
        if checkIfIsMutedResult[1] == "stabilityBreaker":
            try:
                await msg.delete()
            except:
                logger.warning(
                    f"Error while deleting stabilityBreaker's message: {msg.sender.id} in {msg.chat_id}, msgid: {msg.id}")
        elif checkIfIsMutedResult[0]:
            checkIfAllowedResult = db.getSettingsForChat(msg.chat_id, "mute_admins_allowed")[0][0]
            if checkIfAllowedResult == "ChatNotFound":
                logger.warning(
                    f"Failed to get chat settings while working with muted admin's message in {msg.chat_id}. Trying to fix automatically...")
                funcOut = db.addChatEntry(msg.chat_id)
                if funcOut == "Success":
                    logger.success("Fixed successfully!")
                    await muteAdminsWorker(msg)
                    return
                else:
                    logger.error("Failure while fixing!")
                    return
            if bool(checkIfAllowedResult):
                try:
                    await msg.delete()
                except:
                    logger.warning(
                        f"Error while deleting mutedAdmin's message: {msg.sender.id} in {msg.chat_id}, msgid: {msg.id}")




@bot.on(events.NewMessage(pattern='/settings'))
@logger.catch
async def settings_helper(msg):
    if "@" in msg.text and not "@aethermgr_bot" in msg.text:
        return
    global requests_per_this_session
    requests_per_this_session += 1
    try:
        requester_perms = await bot.get_permissions(msg.chat_id, msg.sender_id)
    except:
        logger.warning("Settings cmd in pm from {str(msg.sender.id)}")
        return
    if not requester_perms.change_info and msg.sender_id != myid:
        pass
    else:
        await msg.reply(
            '__Доступные настройки:__\n\n**MuteAdmins** - __разрешает всем администраторам мутить друг друга путём авто удаления сообщений. По умолчанию отключено.__\n\n**ReactOnXiaomi** - __Отправляет бассбустед голосовое при упоминании сей компании или MIUI. По умолчанию включено.__\n\n**ReactOnPing** - __Реакция на сообщение **бот**, что является заменой /ping. Используется для проверки работоспособности бота. По умолчанию включено.__\n\n**AllowTiktokLinks** - __Разрешать ли ссылки, ведущие на TikTok. По умолчанию включено (не удалять)__\n\n**Greeting** - Позволяет установить собственное приветствие. Не требует значений True/False.\n\n**Captcha** - __Заставлять ли пользователей проходить капчу на входе. Принимаемые значения: \"on\"(Заставлять всех), \"ad_only\"(Заставлять только похожих на ботов) и \"off\"(Не заставлять)__\n\n**WhoCanChangeSettings** - __Параметр позволяет устанавливать, кто может редактировать настройки. Допустимые значения - \"CreatorOnly\" - только создатель, и \"AllAdmins\" - все администраторы с правом изменения профиля группы__\n\n\nИспользуйте /set [НазваниеПараметра] [Значение(True\\False)] для изменения параметров')


@bot.on(events.NewMessage(pattern="/set"))
@logger.catch
async def setCommand(msg):
    if "settings" in msg.raw_text.split(" ")[0]:
        return
    global requests_per_this_session
    requests_per_this_session += 1
    try:
        requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
    except Exception as e:
        logger.debug("Failure while getting permissions: " + str(e))
        return
    checkIfCreatorOnly = db.getSettingsForChat(msg.chat_id, "who_can_change_settings")
    if checkIfCreatorOnly == "ChatNotFound":
        funcOut = db.addChatEntry(msg.chat_id)
        if funcOut == "Success":
            await setCommand(msg)
        else:
            return
    if checkIfCreatorOnly == "CreatorOnly":
        if not requesterPermissions.is_creator:
            myReply = await msg.reply("❌ **__Только создатель чата может изменять параметры__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
    else:
        if not requesterPermissions.is_admin:
            myReply = await msg.reply("❌ **__Только администраторы могут изменять параметры__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
    # Editing settings
    settingsDictionary = {
        "muteadmins": "BOOL_mute_admins_allowed",
        "reactonxiaomi": "BOOL_react_on_xiaomi",
        "reactonping": "BOOL_react_on_ping",
        "allowinvitelinks": "BOOL_allow_invite_links",
        "allowtiktoklinks": "BOOL_allow_tiktok_links",
        "greeting": "SPECIFIC_custom_hello",
        "whocanchangesettings": "STRING_who_can_change_settings",
        "captcha": "STRING_captcha"
    }
    textSplit = msg.raw_text.replace("/set ", "").replace("/set@aethermgr_bot ", "").replace("_", "").replace("-",
                                                                                                              "").lower().split(
        " ")
    if not bool(textSplit) or len(textSplit) > 2:
        return
    try:
        settingToChange = settingsDictionary[textSplit[0]]
    except:
        myReply = await msg.reply(
            "❌ **__Настройка не найдена. Пожалуйста, убедитесь в правильности написания. Список доступных настроек можно посмотреть в /settings__**")
        await asyncio.sleep(7.5)
        await myReply.delete()
        return
    if settingToChange.startswith("BOOL_"):
        actualSettingToChange = settingToChange.replace("BOOL_", "")
        try:
            booleanToSet = textSplit[1].lower().replace("false", "0").replace("no", "0").replace("yes", "1").replace(
                "true", "1")
            if len(booleanToSet) > 1: return
            functionOutput = db.editChatEntry(msg.chat_id, actualSettingToChange, booleanToSet)
            if functionOutput == "Error":
                raise "someErrorToTriggerExcept"
            myReply = await msg.reply("✅ **__Параметр установлен__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        except:
            myReply = await msg.reply("❌ **__Произошла ошибка__**")
            logger.error(f"Exception at editing settings in CHID:{msg.chat_id} by ID:{msg.sender.id}")
            await asyncio.sleep(4)
            await myReply.delete()
            return
    if settingToChange.startswith("SPECIFIC_"):
        someVariableIDontKnowHowToName = settingToChange.replace("SPECIFIC_", "")
        if someVariableIDontKnowHowToName == "custom_hello":
            if not msg.is_reply:
                myRequest = await msg.reply(
                    "🕒 **__Хорошо, сейчас вам необходимо отправить новое приветствие в ответ на это сообщение в течении двух минут__**")
                try:
                    async with bot.conversation(msg.chat, timeout=120) as conversation:
                        newGreeting = await conversation.get_reply(myRequest)
                        while newGreeting.sender.id != msg.sender.id:
                            newGreeting = await conversation.get_reply(myRequest)
                except asyncio.exceptions.TimeoutError:
                    myReply = await msg.reply("❌ **__К сожалению, вы не успели__**")
                    await asyncio.sleep(5)
                    await myRequest.delete()
                    await myReply.delete()
                    return
            else:
                newGreeting = await msg.get_reply_message()
            savedGreeting = await bot.send_message(-1001766720438, newGreeting)
            db.editChatEntry(msg.chat_id, "greeting", str(savedGreeting.id), mode="string")
            myReply = await msg.reply("✅ **__Приветствие сохранено__**")
            await asyncio.sleep(5)
            await myReply.delete()
            await myRequest.delete()
            return
    if settingToChange.startswith("STRING_"):
        settingName = settingToChange.replace("STRING_", "")
        allowedStringValues = {
            "who_can_change_settings": ["creatoronly", "alladmins"],
            "captcha": ["on", "adonly", "off"]
        }
        goodToGo = False  # <--- Useless variable
        try:
            if textSplit[1] in allowedStringValues[settingName]:
                goodToGo = True
            else:
                await msg.reply(
                    f"❌ **__Вы указали неверное значение для параметра. Доступные: {str(allowedStringValues[settingName])}__**")
                return
        except:
            myReply = await msg.reply("❌ **__Вы указали неверный параметр__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        functionResult = db.editChatEntry(msg.chat_id, settingName, textSplit[1], mode="string")
        if functionResult == "Success":
            myReply = await msg.reply("✅ **__Параметр установлен__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        else:
            myReply = await msg.reply("❌ **__Произошла ошибка__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return


@bot.on(events.NewMessage(
    pattern=r'(?i).*miui*|.*миуи*|.*миюай*|.*memeui*|.*xiaomi*|.*ximi*|.*кси*оми*|.*ксяоми*'))
@logger.catch
async def memeui(msg):
    try:
        get_command = """SELECT react_on_xiaomi FROM settings WHERE chat_id = {cid}""".format(cid=str(msg.chat_id))
        db.chatsCursor.execute(get_command)
        result = db.chatsCursor.fetchall()
        result = str(result).replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace("'",
                                                                                                         '').replace(
            ",", "")
    except:
        logger.exception('Error on xiaomi')
        return
    if result == '1':
        global requests_per_this_session
        requests_per_this_session += 1
        choise = random.randint(-1, 5)
        if choise == 1:
            await bot.send_file(msg.chat_id, 'miui.ogg', voice_note=True, reply_to=msg)
        elif choise == 2:
            await bot.send_file(msg.chat_id, 'ximi.jpg', reply_to=msg)
        else:
            pass


@bot.on(events.NewMessage(pattern='мсгид'))
@logger.catch
async def msgid(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    if msg.is_reply:
        reply = await msg.get_reply_message()
        await msg.reply('`' + str(reply.id) + '`')
    else:
        await msg.reply('`' + str(msg.id) + '`')


@bot.on(events.NewMessage(pattern='/purge|пург'))
@logger.catch
async def purge(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    if msg.is_reply:
        reply = await msg.get_reply_message()
        try:
            requester_perms = await bot.get_permissions(msg.chat_id, msg.sender_id)
        except:
            return
        if requester_perms.is_admin:
            end_of_purge_id = msg.id
            start_of_purge_id = reply.id
            to_delete_amount = end_of_purge_id - start_of_purge_id
            now_adding = 0
            messages_to_delete = []
            while now_adding <= to_delete_amount:
                messages_to_delete.append(start_of_purge_id + now_adding)
                now_adding += 1
            if len(messages_to_delete) > 99:
                await msg.reply("**__Вы выбрали много сообщений, они будут удалены со временем__**")
                errored = 0
                for message in messages_to_delete:
                    try:
                        await bot.delete_messages(msg.chat_id, message)
                    except:
                        errored += 1
                        logger.error("Errored while deleting message " + str(message))
                await bot.send_message(msg.chat,
                                       "✅ **__Удаление завершено.__**" + f" **__Произошла ошибка во время удаления {str(errored)} сообщений.__**" if errored != 0 else "")
            else:
                await bot.delete_messages(msg.chat_id, messages_to_delete)
            my_reply = await bot.send_message(msg.chat_id, '✅ **__Готово. Было удалено {msgs} сообщений.__**'.format(
                msgs=str(now_adding)))
            await asyncio.sleep(5)
            await my_reply.delete()


@bot.on(events.NewMessage(pattern=r"(?i)сколько будет"))
@logger.catch
async def counter(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    requestRaw = msg.raw_text.lower().replace("\n", "")
    forbidden_words = ['os', 'import', 'subprocess', 'rm', 'ssh', 'ip', 'process', 'run', 'exec', 'eval', 'kill',
                       'exit', 'thread']
    ban = False
    for word in forbidden_words:
        if word in requestRaw:
            ban = True
    if ban:
        if msg.is_private:
            return
        requesterPerms = await bot.get_permissions(msg.chat, msg.sender)
        if not requesterPerms.is_admin:
            try:
                await bot.edit_permissions(msg.chat, msg.sender, timedelta(days=3), send_messages=False)
                await msg.delete()
                return
            except Exception as e:
                logger.error(e)
                return
        else:
            db.registerNewMutedAdmin(msg.sender.id, msg.chat_id, "stabilityBreaker")
            await msg.delete()
            return
    requestPure = requestRaw.replace('сколько будет ', '').replace('\"', '').replace('\'', '').replace('\\',
                                                                                                       '/').replace('[',
                                                                                                                    '').replace(
        ']', '').replace("'", '').replace(",", "").replace(":", "/")
    lettersSearch = re.search('[а-яА-ЯA-Za-z]', requestPure)
    if lettersSearch:
        myReply = await msg.reply("❌ **__Буквы в выражении запрещены__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    myReply, result = None, None
    with time_limit(3):
        try:
            result = eval(requestPure)
        except ZeroDivisionError:
            myReply = await msg.reply("❌ **__Напоминаю, что на ноль делить нельзя__**")
        except TimeoutException:
            myReply = await msg.reply("❌ **__Вычисление продлилось слишком долго__**")
        except SyntaxError as error:
            myReply = await msg.reply("❌ **__Некорректное выражение__**")
            logger.error(error)
    if result:
        result = str(result).split("e+")
        text = f"🧮 **__{str(result[0])}"
        if len(result) == 2:
            if result[0].startswith("-"):
                text += " * -10 в степени " + str(result[1]) + "__**"
            else:
                text += " * 10 в степени " + str(result[1]) + "__**"
        else:
            text += "__**"
        myReply = await msg.reply(text)
        await asyncio.sleep(15)
        await myReply.delete()
        return
    await asyncio.sleep(5)
    await myReply.delete()


@bot.on(events.NewMessage(pattern=r'(?i)бот, го|@aethermgr_bot го'))
@logger.catch
async def go(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    answers = ['го', "не", 'давай', 'нет', 'не хочу', 'погнали', 'хз']
    select = random.randint(0, len(answers) - 1)
    async with bot.action(msg.chat_id, 'typing'):
        await asyncio.sleep(random.randint(1, 4))
        await msg.reply(answers[select])


@bot.on(events.NewMessage(pattern='/aboutbot'))
@logger.catch
async def aboutbot(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    text = f"""[Новостной канал бота](https://t.me/aethermanager)
[Обсуждение бота](https://t.me/aethermanagerchat)

Credits:
**Mirivan** - За большое количество подсказок на раннем этапе разработки.
**zhazhazha** - За пинок заняться этим. Нет, серьёзно, спасибо. Кстати, [его сайтик](http://www.zhazhazha.space/about)
**𝖀𝕾𝕰𝕽 𝕹𝕬𝕸𝕰** - За моральную поддержку и стресс-тесты бота во время ранней разработки.
**Avadamiao** - За стресс-тесты бота.

Всех перечисленных можно найти в @kali_nh

Если вы желаете дать идею/рассказать об ошибке/получить канал связи с базой данных бота, напишите об этом в чате обсуждения бота"""
    await msg.reply(text, link_preview=False)


@bot.on(events.NewMessage(pattern="/anon"))
@logger.catch
async def anon(msg):
    myReply = await msg.reply("❌ **__Функция временно отключена__**")
    await asyncio.sleep(5)
    await myReply.delete()


# TODO: Rewrite
# @bot.on(events.NewMessage(pattern=r'(?i)/anon'))
# @logger.catch
# async def anon(msg):
#     global requests_per_this_session
#     requests_per_this_session += 1
#     if msg.is_private:
#         msg_text = msg.raw_text
#         msg_text = msg_text.lower().split(' ')
#         if len(msg_text) > 2:
#             found = False
#             id = None
#             msg_text.remove(msg_text[0])
#             fakename = msg_text[0]
#             msg_text.remove(msg_text[0])
#             try:
#                 target = await bot.get_entity(msg_text[0])
#                 id = target.id
#                 found = True
#             except:
#                 current_altname = ''
#                 for i in msg_text:
#                     if id == None:
#                         current_altname += i
#                         id = db_get_id(current_altname)
#                         if id != 'NotFound':
#                             found = True
#                             id = int(id)
#                     else:
#                         break
#             if found:
#                 target_info = await bot.get_entity(id)
#                 if target_info.lang_code != None:
#                     async with bot.conversation(msg.chat_id) as conv:
#                         my_ask_for_message = await msg.reply('Введите текст сообщения')
#                         response = await conv.get_response(msg.chat_id)
#                         text_to_send = response.raw_text + '\n\n\n(c) ' + fakename
#                     await bot.send_message(id, 'Новое анонимное сообщение:')
#                     await bot.send_message(id, text_to_send)
#                     await msg.reply('✅ **__Сообщение передано__**')
#                 else:
#                     await msg.reply('❌ **__Пользователь {fname} не запускал чата с ботом__**'.format(fname = str(target_info.first_name)))
#             else:
#                 await msg.reply('❌ **__Пользователь не найден__**')
#         else:
#             await msg.reply('**__Использование: /anon [YOURFAKENAME] [NAME], где [YOURFAKENAME] - имя, которым вы хотите представиться(лимит - 1 слово), и [NAME] - имя пользователя или альтернативное имя.__**')
#     else:
#         await msg.reply('**__Использовать можно только в личных сообщениях с ботом. Начните диалог с ним, чтобы иметь возможность принимать анонимные сообщения__**')


@bot.on(events.NewMessage(pattern='/status'))
@logger.catch
async def status(msg):
    if "@" in msg.text and not "@aethermgr_bot" in msg.text:
        return
    global requests_per_this_session
    requests_per_this_session += 1
    now_time = time.time()
    uptime = str(int((int(now_time) - int(startTime)) / 60))
    text = """✅ **__Онлайн
Загруженность процессора: {cpuloadpercent}%
Занятая ОЗУ: {rampercent} MB
Время работы: {uptime} мин
Обработано запросов за сессию: {requests}__**""".format(cpuloadpercent=str(psutil.cpu_percent()), rampercent=str(
        round(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)), uptime=uptime,
                                                        requests=str(requests_per_this_session))
    my_msg = await msg.reply(text)
    await asyncio.sleep(10)
    await my_msg.delete()




@bot.on(events.NewMessage(pattern='/kickme'))
@logger.catch
async def kickme(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    try:
        perms = await bot.get_permissions(msg.chat_id, msg.sender)
    except:
        return
    if not perms.is_admin:
        await bot.kick_participant(msg.chat_id, msg.sender)


@bot.on(events.NewMessage(pattern="/cube|/dice"))
@logger.catch
async def cube(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    messages_to_delete = []
    my_darts = await bot.send_file(msg.chat_id, types.InputMediaDice('🎲'), reply_to=msg)
    messages_to_delete.append(my_darts.id)
    can_continue = False
    try:
        async with bot.conversation(msg.chat_id, timeout=20) as conv:
            reply_darts = await conv.get_reply(my_darts)
            while reply_darts.sender.id != msg.sender.id:
                reply_darts = await conv.get_reply(my_darts)
        messages_to_delete.append(reply_darts.id)
        can_continue = True
    except asyncio.exceptions.TimeoutError:
        timeout_notification = await msg.reply('**__Вы не успели кинуть кубик!__**')
        messages_to_delete.append(timeout_notification.id)
    if reply_darts.media:
        if reply_darts.media.emoticon != "🎲":
            fake_notification = await msg.reply("**__Это не кубик!__**")
            messages_to_delete.append(fake_notification.id)
            can_continue = False
    else:
        fake_notification = await msg.reply("**__Это не кубик!__**")
        messages_to_delete.append(fake_notification.id)
        can_continue = False
    if can_continue:
        my_value = my_darts.media.value
        his_value = reply_darts.media.value
        await asyncio.sleep(3.5)
        if my_value == his_value:
            result = await msg.reply("**__Увы, ничья__**")
            num = None
        elif my_value > his_value:
            num = 0 - (random.randint(1, 20) * (my_value - his_value))
            result = await msg.reply(f"**__Вы проиграли, и теряете {str(num).replace('-', '')} монет.__**")
        else:
            num = random.randint(1, 20) * (his_value - my_value)
            result = await msg.reply(f"**__Вы выиграли, и получаете {str(num)} монет.__**")
        messages_to_delete.append(result.id)
        if num:
            dbEntry = db.getUserEntry(msg.sender.id)
            if dbEntry == "NotFound":
                await parseAllUsers(msg.chat)
                return
            moneyCurrent = dbEntry[0][4]
            moneyNew = moneyCurrent + num
            db.editUserEntry(msg.sender.id, "money", str(moneyNew))
    await asyncio.sleep(5)
    for message in messages_to_delete:
        try:
            await bot.delete_messages(msg.chat, message)
        except:
            pass


@bot.on(events.NewMessage(pattern='/screenshot|/url|скриншот|screenshot|\?'))
@logger.catch
async def get_link_for_scrn(msg):
    return  # Turned off until I find a valid screenshoting API
    global requests_per_this_session
    requests_per_this_session += 1
    if msg.is_reply:
        message = await msg.get_reply_message()
        if message.entities:
            global todo_sec_links
            timestamp = int(time.time() * 2)
            urls = ""
            for ent in message.entities:
                if type(ent) in [MessageEntityUrl, MessageEntityTextUrl]:
                    if type(ent) == MessageEntityUrl:
                        offset = ent.offset
                        length = ent.length
                        url = message.raw_text[offset:offset + length]
                    else:
                        url = ent.url
                    if not (url.startswith("http") or url.startswith("https")):
                        url = "http://" + url
                    urls += ", " + url
                    todo_sec_links = urls
            if todo_sec_links != '':
                urls_list = todo_sec_links.split(", ")
                if len(urls_list) > 4:
                    await msg.reply('❌ **__В сообщении слишком много ссылок!__**')
                else:
                    a = await msg.reply('🔎 **__В процессе...__**')
                    for link in urls_list:
                        if not link == '':
                            link = link.lower()
                            try:
                                await asyncio.subprocess.create_subprocess_exec(
                                    await link_screenshot(message, msg, timestamp, link, a))
                            except:
                                pass
                    await a.delete()
                # p = Process(target=aboba, args=(message, msg, timestamp))
                # p.start()
                # await link_screenshot(message, msg, timestamp)


@logger.catch
async def link_screenshot(event, msg, url, my_msg):
    with time_limit(60):
        try:
            global requests_per_this_session
            requests_per_this_session += 1
            ban = False
            banlist = ['porn', 'xvideos', 'hent', 'bigboss', 'xhamster', 'yaeby']  # A list of bannable words in links.
            for banword in banlist:
                if banword in url:
                    ban = True
                    break
                else:
                    reban = re.search(fr'(?i).*{banword}*', url)
                    if reban:
                        ban = True
                        break
            if ban:
                await msg.reply('❌ **__Такие ссылки запрещены!__**')
            else:
                target = url
                column = 0
                if not target == '':
                    logger.info('Making a screenshot of {}... (Requester: {})'.format(target, msg.sender.first_name))
                    await my_msg.edit('🔎 **__В процессе... (Получение)__**')
                    url = f"https://image.thum.io/get/width/1920/crop/1080/wait/3/{target}"
                    file = requests.get(url.format(url))
                    if not file.ok:
                        await bot.send_message(event.chat_id, f"❌ **__Не удалось получить скриншот__**: `{target}`")
                        return
                    else:
                        logger.info(f'Checking {target} for nudity... (Requester: {msg.sender.first_name})')
                        await my_msg.edit('🔎 **__В процессе... (Проверка)__**')
                        nudity_check = requests.post("https://api.deepai.org/api/nsfw-detector",
                                                     files={'image': file.content, },
                                                     headers={'api-key': conf.deepai_token,
                                                              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
                        nc_inpython = json.loads(str(nudity_check.json()).replace('\'', '\"'))
                        try:
                            output = nc_inpython['output']
                            nsfw_score = dict(output)['nsfw_score']
                            logger.info('NSFW Score = ' + str(nsfw_score))
                        except:
                            print(str(nc_inpython))
                            nsfw_score = 0
                    if not float(nsfw_score) > 0.25:
                        await my_msg.edit('🔎 **__В процессе... (Отправка)__**')
                        num = str(random.randint(0, 999999))
                        with open(f"temp/siteScreenshot_{num}.jpg", "wb") as fileToWrite:
                            fileToWrite.write(file.content)
                        await bot.send_file(event.chat_id,
                                            caption=f"✅ **__Вот, скриншот сайта {target}.\nШанс наготы: {nsfw_score * 100}%\nPowered by image.thum.io and deepai.org__**",
                                            file=f"temp/siteScreenshot_{num}.jpg", reply_to=msg, force_document=True)
                    else:
                        logger.info('Detected nudity!')
                        await msg.reply(f'❌ **__На сайте обнаружена нагота! (Уверенность: {nsfw_score * 100}%)__**')
                await asyncio.sleep(1)
                column += 1
        except TimeoutException:
            await msg.reply('❌ **__Процесс занял слишком много времени и был прерван.__**')


@logger.catch
async def preinit():
    schedule.every(30).minutes.do(backupDatabase)
    backgroundScheduleThread = threading.Thread(target=scheduleThreader, daemon=True)
    backgroundScheduleThread.start()
    logger.debug("Scheduled database backup for 30 mins")
    logger.info('PreInit success!')


@bot.on(events.NewMessage(pattern="/darts"))
@logger.catch
async def darts(msg):
    myReply = await msg.reply("❌ **__Функция временно отключена__**")
    await asyncio.sleep(5)
    await myReply.delete()
    return
    global requests_per_this_session
    requests_per_this_session += 1
    messages_to_delete = []
    my_darts = await bot.send_file(msg.chat_id, types.InputMediaDice('🎯'), reply_to=msg)
    messages_to_delete.append(my_darts.id)
    my_hint = await msg.reply('**__Сыграйте в дартс в ответ на мой выше, посмотрим, кому повезёт больше! :P__**')
    messages_to_delete.append(my_hint.id)
    can_continue = False
    try:
        async with bot.conversation(msg.chat_id, timeout=20) as conv:
            reply_darts = await conv.get_reply(my_darts)
            while reply_darts.sender.id != msg.sender.id:
                reply_darts = await conv.get_reply(my_darts)
        messages_to_delete.append(reply_darts.id)
        can_continue = True
    except asyncio.exceptions.TimeoutError:
        timeout_notification = await msg.reply('**__Вы не успели сыграть в дартс!__**')
        messages_to_delete.append(timeout_notification.id)
    if reply_darts.media:
        if reply_darts.media.emoticon != "🎯":
            fake_notification = await msg.reply("**__Это не дартс!__**")
            messages_to_delete.append(fake_notification.id)
            can_continue = False
    else:
        fake_notification = await msg.reply("**__Это не дартс!__**")
        messages_to_delete.append(fake_notification.id)
        can_continue = False
    if can_continue:
        my_value = my_darts.media.value
        his_value = reply_darts.media.value
        await asyncio.sleep(3.5)
        if my_value == his_value:
            result = await msg.reply("**__Увы, ничья__**")
        elif my_value > his_value:
            num = 0 - (random.randint(1, 20) * (my_value - his_value))
            result = await msg.reply(f"**__Вы проиграли, и теряете {str(num).replace('-', '')} монет.__**")
        else:
            num = random.randint(1, 20) * (his_value - my_value)
            result = await msg.reply(f"**__Вы выиграли, и получаете {str(num)} монет.__**")
        messages_to_delete.append(result.id)
        if num:
            cursor.execute(f"SELECT money FROM fetched_users WHERE id={msg.sender.id}")
            current_coins = int(cursor.fetchone()[0])
            new_coins = current_coins + num
            cursor.execute(f"UPDATE fetched_users SET money = {str(new_coins)} WHERE id = {msg.sender.id}")
            db_main.commit()
    await asyncio.sleep(5)
    await bot.delete_messages(msg.chat, messages_to_delete)


@bot.on(events.NewMessage(pattern="/note|сохранить|/save", func=lambda x: not x.is_private and x.is_reply))
@logger.catch
async def noteSave(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    requesterPermissions = await bot.get_permissions(msg.chat, msg.sender)
    if not requesterPermissions.is_admin:
        return
    targetMessage = await msg.get_reply_message()
    noteName = msg.raw_text.replace('/note ', '').replace('/note@aethermgr_bot ', '').replace('/note', '').replace(
        '/note@aethermgr_bot', '').replace('сохранить ', '').replace('сохранить', '').replace('/save ', '').replace(
        '/save@aethermgr_bot ', '').replace('/save', '').replace('/save@aethermgr_bot', '').lower().replace('\"',
                                                                                                            '').replace(
        '\'', '').replace(',', '').replace("#", "").replace(' ', '_').replace(";", "")
    noteNameCheck = re.search('[a-zA-Zа-яА-Я]', noteName)
    if not noteNameCheck:
        myReply = await msg.reply("❌ **__Название заметки не указано__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    db.otherCursor.execute(
        f"SELECT EXISTS(SELECT * FROM notes WHERE note_name = \"{noteName}\" AND chat_id = {msg.chat_id})")
    checkIfExistsOutput = db.otherCursor.fetchall()[0][0]
    if bool(checkIfExistsOutput):
        myReply = await msg.reply("❌ **__Такая заметка уже существует__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    savedNoteMessage = await bot.send_message(-1001766720438, targetMessage)
    try:
        db.otherCursor.execute(
            f"INSERT INTO notes (msgid, chat_id, note_name, note_author_id) VALUES ({str(savedNoteMessage.id)}, {msg.chat_id}, \"{noteName}\", {msg.sender.id})")
        db.otherDB.commit()
        myReply = await msg.reply("✅ **__Заметка сохранена__**")
        await asyncio.sleep(7)
        await myReply.delete()
    except:
        myReply = await msg.reply("❌ **__Произошла ошибка__**")
        await asyncio.sleep(5)
        await myReply.delete()


@bot.on(events.NewMessage(pattern="/get|получить|#", func=lambda x: not x.is_private and not x.forward))
@logger.catch
async def noteGet(msg):
    if "getsetting" in msg.text:
        return
    global requests_per_this_session
    requests_per_this_session += 1
    annoyOnNotFound = True
    noteName = msg.raw_text.replace('/get ', '').replace('/get@aethermgr_bot ', '').replace('/get', '').replace(
        '/get@aethermgr_bot', '').replace('получить ', '').replace('получить', '').lower().replace('\"', '').replace(
        '\'', '').replace(";", "")
    if "#" in noteName:
        annoyOnNotFound = False
        noteName = noteName.replace('#', "")
    db.otherCursor.execute(
        f"SELECT EXISTS(SELECT * FROM notes WHERE note_name = \"{noteName}\" and chat_id = {msg.chat_id})")
    checkExistance = db.otherCursor.fetchall()
    if not bool(checkExistance[0][0]):
        if annoyOnNotFound:
            myReply = await msg.reply("❌ **__Такой заметки не существует__**")
            await asyncio.sleep(5)
            await myReply.delete()
            return
        return
    db.otherCursor.execute(f"SELECT msgid FROM notes WHERE note_name = \"{noteName}\" and chat_id = {msg.chat_id}")
    noteMessageID = int(db.otherCursor.fetchall()[0][0])
    try:
        noteMessage = await bot.get_messages(-1001766720438, ids=noteMessageID)
        await bot.send_message(msg.chat, noteMessage, reply_to=msg)
    except Exception as error:
        myReply = await msg.reply("❌ **__Произошла ошибка__**")
        await asyncio.sleep(5)
        await myReply.delete()
        logger.error(error)
        return


@bot.on(events.NewMessage(pattern="/delnote|удалить", func=lambda x: not x.is_private))
@logger.catch
async def noteDelete(msg):
    global requests_per_this_session
    requests_per_this_session += 1
    requesterPerms = await bot.get_permissions(msg.chat, msg.sender)
    if not requesterPerms.is_admin:
        return
    noteNameRaw = msg.raw_text.replace('/delnote ', '').replace('/delnote@aethermgr_bot ', '').replace('/delnote',
                                                                                                       '').replace(
        '/delnote@aethermgr_bot', '').replace('удалить ', '').replace('удалить', '')
    nameExistanceCheck = re.search('[a-zA-Zа-яА-Я]', noteNameRaw)
    if not nameExistanceCheck:
        myReply = await msg.reply("❌ **__Вы не указали название заметки__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    noteNamePure = noteNameRaw.lower().replace('\"', '').replace('\'', '').replace(',', '').replace("#", "").replace(
        ' ', '_').replace(";", "")
    db.otherCursor.execute(
        f"SELECT EXISTS(SELECT * FROM notes WHERE note_name = \"{noteNamePure}\" and chat_id = {msg.chat_id})")
    if not bool(db.otherCursor.fetchall[0][0]):
        myReply = await msg.reply("❌ **__Такой заметки не существует__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    try:
        db.otherCursor.execute(f"DELETE FROM notes WHERE note_name = \"{noteNamePure}\" and chat_id = {msg.chat_id}")
        db.otherDB.commit()
        myReply = await msg.reply("✅ **__Заметка удалена__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    except Exception as error:
        myReply = await msg.reply("❌ **__Произошла ошибка__**")
        await asyncio.sleep(5)
        await myReply.delete()
        logger.error(error)
        return


@bot.on(events.NewMessage(pattern="/notes|заметки", func=lambda x: not x.is_private))
@logger.catch
async def noteList(msg):
    db.otherCursor.execute(f"SELECT EXISTS(SELECT * FROM notes WHERE chat_id = {msg.chat_id})")
    if not bool(db.otherCursor.fetchall()[0][0]):
        myReply = await msg.reply("📔 **__Заметки в этом чате отсутствуют__**")
        await asyncio.sleep(5)
        await myReply.delete()
        return
    db.otherCursor.execute(f"SELECT note_name FROM notes WHERE chat_id = {msg.chat_id}")
    notesList = db.otherCursor.fetchall()
    text = "📔 **__Заметки в этом чате:__**\n"
    for note in notesList:
        text += f"`#{note[0]}`"
    myReply = await msg.reply(text)


@bot.on(events.NewMessage(pattern=r'(?i).*nullify.cc*'))
@logger.catch
async def nullify_warning(msg):
    m = msg.raw_text
    await msg.delete()
    myMsg = await bot.send_message(msg.chat_id,
                                   f'⚠**__Будьте осторожны! Эти ссылки могут содержать вредоносный код, который трудно выявить. Даже если ссылка кажется пустой - будьте внимательны! Сервисы по типу nullify.cc могут использовать невидимые символы. Переходите по ссылке только в том случае, если доверяете отправителю. \nТекст сообщения:\n__**{msg.sender.first_name}: {m}')
    await asyncio.sleep(10)
    await myMsg.delete()


@bot.on(events.NewMessage(pattern='/shutdown', from_users=myid))
@logger.catch
async def stop(msg):
    await msg.reply('Остановка бота...')
    os.system('touch stopping')
    await bot.disconnect()


@bot.on(events.NewMessage(pattern='/recognize|/voice|/recognise|\?', func=lambda x: x.is_reply))
@logger.catch
async def recognize_voice(msg):
    text = '🎧 **__Распознавание...__**\n'
    if msg.is_reply:
        target = await msg.get_reply_message()
    else:
        target = msg
    if target.voice:
        my_msg = await msg.reply(text)
        num = str(random.randint(10000, 99999))
        await target.download_media(f'temp/audio{num}.mp3')
        subprocess.run(f'ffmpeg -hide_banner -loglevel error -i temp/audio{num}.mp3 temp/audio{num}.wav', shell=True,
                       text=True, stdout=subprocess.PIPE)
        audio_file = speech_recognition.AudioFile(f'temp/audio{num}.wav')
        with audio_file as source:
            audio_data = recognizer.record(source)
        try:
            recognized_google = recognizer.recognize_google(audio_data, language='ru-RU')
            text += '\n__' + recognized_google + '__\n\n'
            await my_msg.edit(text)
        except speech_recognition.UnknownValueError:
            text += f'Google Engine:\n__Не удалось разпознать сообщение...__\n\n'
            await my_msg.edit(text)
        except Exception as error:
            text += f'Google Engine:\n__Ошибка распознавания: {error}__\n\n'
            await my_msg.edit(text)

        await my_msg.edit(text.replace('🎧 **__Распознавание...__**\n', '🎧 **__Распознано!__**\n'))
        subprocess.run(f'rm temp/audio{num}.*', shell=True)


@bot.on(events.NewMessage(func=lambda x: x.is_private and x.voice))
@logger.catch
async def recogInPM(msg):
    await recognize_voice(msg)


@bot.on(events.NewMessage(pattern='/bhist'))
@logger.catch
async def banhistory(msg):
    found = False
    if msg.is_reply:
        reply = await msg.get_reply_message()
        target = reply.sender
        found = True
    if found:
        db.otherCursor.execute(f"SELECT * FROM ban_history WHERE id = {target.id}")
        data = db.otherCursor.fetchall()
        text = "**__История блокировок:\n\n"
        if len(data) > 0:
            for line in data:
                text += f"""
====================================
Блокировка в чате "{line[3]}"
Причина: {line[4].replace("[", "").replace("]", '')}
Дата и время: {line[5]}
Блокировку выдал(а) [{line[7]}](tg://openmessage?id={line[6]})
===================================="""
        else:
            text = "**__Блокировок не найдено"

        await msg.reply(text + "__**")


@bot.on(events.NewMessage(pattern='/del|дел'))
@logger.catch
async def delete(msg):
    if msg.is_reply:
        try:
            await msg.delete()
            reply = await msg.get_reply_message()
            await reply.delete()
        except:
            my_msg = await msg.reply("❌ **__Ошибка при удалении сообщения__**")
            await asyncio.sleep(2)
            await my_msg.delete()


@bot.on(events.NewMessage(pattern='/baltop'))
@logger.catch
async def baltop(msg):
    db.usersCursor.execute("SELECT * FROM users ORDER BY money DESC")
    data = db.usersCursor.fetchmany(10)
    text = "**__Глобальный топ по балансу:\n"
    for line in data:
        if int(line[4]) > 0:
            text += f"{line[1]} - {line[4]} коинов\n"
    await msg.reply(text + "__**")


@bot.on(events.NewMessage(pattern='/reptop'))
@logger.catch
async def baltop(msg):
    db.usersCursor.execute("SELECT * FROM users ORDER BY reputation DESC")
    data = db.usersCursor.fetchmany(10)
    text = "**__Глобальный топ по репутации:\n"
    for line in data:
        if int(line[3]) > 0:
            text += f"{line[1]} - {line[3]} очков репутации\n"
    await msg.reply(text + "__**")


@bot.on(events.NewMessage(pattern="/fullstring", from_users=myid))
@logger.catch
async def fullstring(msg):
    reply = await msg.get_reply_message()
    await msg.reply(reply.stringify())


@bot.on(events.NewMessage(pattern="/fulluser", from_users=myid))
@logger.catch
async def fulluser(msg):
    reply = await msg.get_reply_message()
    userString = reply.sender.stringify()
    fullUserString = await bot(GetFullUserRequest(reply.sender))
    await bot.send_message(myid, f"Normal data:\n{userString}\n\n\nGetFullUserRequest:\n{str(fullUserString)}")
    await msg.reply("Отправлено в лс")


@bot.on(events.NewMessage(pattern="/bugreport"))
@logger.catch
async def bugreport(msg):
    try:
        title = await bot.send_message(-776989017,
                                       f"Новый багрепорт от {msg.sender.first_name} ({str(msg.sender.id)})\nChatID: {str(msg.chat_id)}\nНазвание чата: {msg.chat.title}\n")
        await title.reply(
            msg.raw_text.replace("/bugreport", "") if not msg.raw_text.replace("/bugreport", "") == '' else 'None')
        my_reply = await msg.reply("✅ **__Багрепорт успешно отправлен!__**")
    except:
        my_reply = await msg.reply(
            "❌ **__Ошибка при отправке багрепорта... Да, вы правильно поняли... Баг при исправлении бага...__**")
        logger.exception("Well...")
    await asyncio.sleep(5)
    try:
        await my_reply.delete()
    except:
        pass



@bot.on(events.NewMessage(pattern="/getsettings", func=lambda x: not x.is_private))
@logger.catch
async def getsettings(msg):
    chatSettings = db.getSettingsForChat(msg.chat_id)
    if chatSettings == "ChatNotFound":
        db.addChatEntry(msg.chat_id)
        await getsettings(msg)
    text = f"""⚙️ **__Параметры чата:
Мут админов (`MuteAdmins`) - {str(chatSettings[0][1])}
Реагирование на Xiaomi (`ReactOnXiaomi`) - {str(chatSettings[0][2])}
Реагирование на 'бот' (`ReactOnPing`) - {str(chatSettings[0][3])}
Разрешены пригласительные ссылки (`AllowInviteLinks`) - {str(chatSettings[0][4])}
Разрешены TikTok ссылки (`AllowTiktokLinks`) - {str(chatSettings[0][5])}
Изменённое приветствие (`greeting`) - {"1" if chatSettings[0][6] != "None" else "0"}
Капча (`captcha`) - {str(chatSettings[0][7])}
{"Только создатель может" if chatSettings[0][8] == "creatoronly" else "Все администраторы могут"} изменять параметры (`whocanchangesettings`)
__**""".replace("1", "✅").replace("0", "❌").replace('adonly', 'Только подозрительные').replace('on', '✅').replace('off',
                                                                                                                  '❌')
    await msg.reply(text)


@bot.on(events.NewMessage(pattern="/report", func=lambda x: not x.is_private and x.is_reply))
@logger.catch
async def report(msg):
    reply = await msg.get_reply_message()
    chat_title = "c/" + str(msg.chat.id)
    if msg.chat.title:
        chat_title = msg.chat.title
    text = f"⚠️ **__Новая жалоба в {msg.chat.title}\nОт: {msg.sender.first_name + ' ' + str(msg.sender.last_name)}\nНа: {reply.sender.first_name + ' ' + str(reply.sender.last_name)}\nПричина: {msg.raw_text.replace('/report ', '').replace('/report@aethermgr_bot ', '').replace('/report', 'Не указана').replace('/report@aethermgr_bot', 'Не указана')}\n\n[Перейти к сообщению](https://t.me/{chat_title})__**".replace(
        " None", "")
    notified = 0
    async for admin in bot.iter_participants(msg.chat, filter=ChannelParticipantsAdmins):
        if admin.lang_code:
            try:
                admin_perms = await bot.get_permissions(msg.chat, admin)
                if admin_perms.ban_users:
                    try:
                        await bot.send_message(admin, text)
                        notified += 1
                    except:
                        logger.error("Failed to notify " + admin.first_name)
            except:
                pass
    await msg.reply(f"✅ **__Следующее кол-во администраторов было уведомлено: {str(notified)}__**")



def backupDatabase():
    logger.debug("Database backup begin...")
    backup = ZipFile(f"backups/dbBackup_{str(datetime.now()).replace(' ', '_').replace(':', '_')}.zip", "w")
    backup.write("database/altnames.db")
    backup.write("database/users.db")
    backup.write("database/other.db")
    backup.write("database/mutedadmins.db")
    backup.write("database/chats.db")
    backup.close()
    logger.debug("Database backup complete")


def scheduleThreader():
    while True:
        schedule.run_pending()
        time.sleep(1)


@bot.on(events.NewMessage(pattern="/userscleanup", func=lambda x: not x.is_private))
@logger.catch
async def chatCleaner(msg):
    requesterPerms = await bot.get_permissions(msg.chat, msg.sender)
    if not requesterPerms.ban_users:
        return
    myPerms = await bot.get_permissions(msg.chat, botid)
    if not myPerms.ban_users:
        myReply = await msg.reply(
            "❌ **__У меня нет необходимых разрешений для этого. Пожалуйста, выдайте мне разрешение 'Блокировка участников'__**")
        await asyncio.sleep(10)
        await myReply.delete()
        return
    myReply = await msg.reply(
        "📛 **__Начинаю очистку чата от удалённых аккаунтов. Это может занять некоторое время__**")
    deletedAmount = 0
    erroredAmount = 0
    async for user in bot.iter_participants(msg.chat):
        if user.deleted:
            try:
                await bot.kick_participant(msg.chat, user)
                deletedAmount += 1
            except:
                erroredAmount += 1
    await myReply.edit(
        f"""✅ **__Очистка чата завершена. Было удалено следующее количество пользователелей: {str(deletedAmount)}. {"Во время удаления " + str(erroredAmount) + " аккаунтов произошла ошибка" if erroredAmount > 0 else ""}__**""")
    await asyncio.sleep(15)
    await myReply.delete()


@bot.on(events.NewMessage(pattern="/exec", from_users=myid))
@logger.catch
async def executor(msg):
    result = exec(msg.raw_text.replace("/exec ", ""))
    await msg.reply(result)


# Checking if bot was restarted and other stuff (kinda useless now, but I'll let it be...)
logger.info("Running PreInit...")
bot.loop.run_until_complete(preinit())

# Starting the bot itself, all the code before is the initiation of functions and handlers
logger.info("Running Init...")


@logger.catch
def init():
    logger.success("Started!")
    bot.run_until_disconnected()


if __name__ == "__main__":
    init()
else:
    logger.exception("AetherManager's main file can't be used as a module!")
    exit()
#
# Closing cursor at the end of the job
logger.info("Exiting because of Ctrl+C...")
exit()

# TODO:
# Reform db                                             <-- DONE!!!!!!!!!!!!!!!!!! FUCKING FINALLY!!!!!!!!!!!!!!
# Make versioning system                                
# Make database backup system                           <-- DONE
# Filters...?                                           <-- Can cause a lot of performance issues
# More chat cleanup to the god of chat cleanup          <-- Can (probably) damage user experience when too much
# Optional disable reports
# Limit /act                                            <-- DONE
# Simplify cube/darts
