import pytest
import database.dataAccess.dal as dal
from database.classes import *

def test_create_chat():
    for i in range(1000):
        dal.writeNewChatEntry(dbChat(i))
        dal.eraseChatEntry(dbChat(i))