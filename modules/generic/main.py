from aethermanager import bot, events
from modules.generic.strings.str import *

@bot.on(events.NewMessage(pattern="/a"))
async def boobs(msg):
    print(msg.text)
