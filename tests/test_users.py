import pytest
import database.dataAccess.dal as dal
from database.classes import *

@pytest.mark.run(order=1)
def test_create_user():
    for i in range(1000):
        dal.writeNewUserEntry(dbUser(i))

@pytest.mark.run(order=2)
def test_read_user_id():
    for i in range(1000):
        assert dal.readUserEntryByID(i) == dbUser(i)
        

@pytest.mark.run(order=999)
def test_erase_user():
    for i in range(1000):
        dal.eraseUserEntry(dbUser(i))
