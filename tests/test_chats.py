import pytest
import database.dataAccess.dal as dal
from database.classes import *


def test_create_chat():
    for i in range(1000):
        dal.writeNewChatEntry(dbChat(i))
        dal.eraseChatEntry(dbChat(i))


def test_read_chat_id():
    for i in range(1000):
        dal.writeNewChatEntry(dbChat(i))
        assert dal.readChatEntryByID(i) == dbChat(i)
        dal.eraseChatEntry(dbChat(i))


def test_edit_chat():
    for i in range(1000):
        newEntry = dbChat(i)
        dal.writeNewChatEntry(newEntry)
        newEntry.allowBots = True
        newEntry.allowInvites = False
        dal.editChatEntry(newEntry)
        dal.eraseChatEntry(dbChat(i))
