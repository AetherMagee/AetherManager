from database.classes import *
from dataclasses import asdict as classAsDict
from database.db import database as dbConnection
from dataclasses import astuple as classAsTuple


def writeNewUserEntry(entry: dbUser, commit=True):
    """
    Writes user entry to the database
    """
    command = "INSERT INTO users ("
    for element in classAsDict(entry).keys():
        command += element + ", "
    command = command[:-2] + ") VALUES ("
    command += "?, " * len(classAsTuple(entry))
    command = command[:-2] + ")"

    with Cursor(dbConnection, autocommit=commit) as cursor:
        cursor.execute(command, classAsTuple(entry))


def eraseUserEntry(entry: dbUser, commit=True):
    """
    TESTING PURPOSE ONLY
    """
    command = "DELETE FROM users WHERE id = ?"
    with Cursor(dbConnection, autocommit=commit) as cursor:
        cursor.execute(command, (entry.id, ))


def readUserEntryByID(searchRequest: int):
    command = "SELECT * FROM users WHERE id = ?"
    with Cursor(dbConnection) as cursor:
        cursor.execute(command, (searchRequest, ))
        result = cursor.fetchone()
    if result:
        return dbUser(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
    else:
        return None


def readUserEntryByPhone(searchRequest: int):
    command = "SELECT * FROM users WHERE phone = ?"
    with Cursor(dbConnection) as cursor:
        cursor.execute(command, (searchRequest, ))
        result = cursor.fetchone()
    if result:
        return dbUser(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
    else:
        return None


def readUserEntryByUsername(searchRequest: str):
    command = "SELECT * FROM users WHERE username = ?"
    with Cursor(dbConnection) as cursor:
        cursor.execute(command, (searchRequest, ))
        result = cursor.fetchone()
    if result:
        return dbUser(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
    else:
        return None


def editUserEntry(entry: dbUser, commit=True):
    command = "UPDATE users SET ("
    for element in classAsDict(entry).keys():
        if not element == "id":
            command += element + ", "
    command = command[:-2] + ") = ("
    command += "?, " * (len(classAsTuple(entry)) - 1)
    command = command[:-2] + ") WHERE id = ?"

    listToWrite = list(classAsTuple(entry))
    listToWrite.remove(entry.id)
    listToWrite.append(entry.id)

    print(command)
    print(str(listToWrite))

    with Cursor(dbConnection, autocommit=commit) as cursor:
        cursor.execute(command, tuple(listToWrite))


def manualCommit():
    dbConnection.commit()


def writeNewChatEntry(entry: dbChat, commit=True):
    command = "INSERT INTO chats ("
    for element in classAsDict(entry).keys():
        command += element + ", "
    command = command[:-2] + ") VALUES ("
    command += "?, " * len(classAsTuple(entry))
    command = command[:-2] + ")"

    with Cursor(dbConnection, autocommit=commit) as cursor:
        cursor.execute(command, classAsTuple(entry))


def eraseChatEntry(entry: dbChat, commit=True):
    command = "DELETE FROM chats WHERE chid = ?"
    with Cursor(dbConnection, autocommit=commit) as cursor:
        cursor.execute(command, (entry.chid, ))


def readChatEntryByID(searchRequest: int):
    command = "SELECT * FROM chats WHERE chid = ?"
    with Cursor(dbConnection) as cursor:
        cursor.execute(command, (searchRequest, ))
        result = cursor.fetchone()
    if result:
        return dbChat(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8])
    else:
        return None


def editChatEntry(entry: dbChat, commit=True):
    command = "UPDATE chats SET ("
    for element in classAsDict(entry).keys():
        if not element == "chid":
            command += element + ", "
    command = command[:-2] + ") = ("
    command += "?, " * (len(classAsTuple(entry)) - 1)
    command = command[:-2] + ") WHERE chid = ?"

    listToWrite = list(classAsTuple(entry))
    listToWrite.remove(entry.chid)
    listToWrite.append(entry.chid)

    with Cursor(dbConnection, autocommit=commit) as cursor:
        cursor.execute(command, tuple(listToWrite))
