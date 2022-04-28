from telethon import TelegramClient, events
from telethon.sessions import StringSession as strsession
from loguru import logger
from config import *

bot = TelegramClient(strsession())