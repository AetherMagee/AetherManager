import pytest
import database.dataAccess.dal as dal
from database.classes import *

def test_create_user():
    for i in range(1000):
        dal.writeNewUserEntry(dbUser(i))
        dal.eraseUserEntry(dbUser(i))

def test_read_user_id():
    for i in range(1000):
        dal.writeNewUserEntry(dbUser(i))
        assert dal.readUserEntryByID(i) == dbUser(i)
        dal.eraseUserEntry(dbUser(i))

def test_edit_user():
    for i in range(1000):
        userObject = dbUser(i)
        dal.writeNewUserEntry(userObject)
        userObject.phone = f"{str(i)}"
        userObject.firstname = f"{str(i)}"
        userObject.lastname = f"{str(i)}"
        userObject.username = f"{str(i)}"
        dal.editUserEntry(userObject)
        dal.eraseUserEntry(userObject)

def test_read_user_phone():
    for i in range(1000):
        a = dbUser(i)
        dal.writeNewUserEntry(a)
        a.phone = 727
        dal.editUserEntry(a)
        assert dal.readUserEntryByPhone(727) == a
        dal.eraseUserEntry(a)

def test_read_user_username():
    for i in range(1000):
        a = dbUser(i)
        dal.writeNewUserEntry(a)
        a.username = "cock"
        dal.editUserEntry(a)
        assert dal.readUserEntryByUsername("cock") == a
        dal.eraseUserEntry(a)