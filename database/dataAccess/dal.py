from database.classes import *
import sqlite3
from dataclasses import asdict as classAsDict
from database.db import database as dbConnection
from dataclasses import astuple as classAsTuple

def writeNewUserEntry(entry: dbUser):
    """
    Writes user entry to the database
    """
    command = "INSERT INTO users ("
    for element in classAsDict(entry).keys(): 
        command += element + ", "
    command = command[:-2] + ") VALUES ("
    command += "?, " * len(classAsTuple(entry))
    command = command[:-2] + ")"
    
    with Cursor(dbConnection) as cursor:
        cursor.execute(command, classAsTuple(entry))

def eraseUserEntry(entry: dbUser):
    """
    TESTING PURPOSE ONLY
    """
    command = "DELETE FROM users WHERE id = ?"
    with Cursor(dbConnection) as cursor:
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

# def readUserEntryByPhone(searchRequest: str):
#     command = "SELECT * FROM users WHERE phone = ?"
#     with Cursor(dbConnection) as cursor:
#         cursor.execute(command, (searchRequest, ))
#         result = cursor.fetchone()
#     if result:
#         return dbUser(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
#     else:
#         return None

def editUserEntry(entry: dbUser):
    command = "UPDATE users SET ("
    for element in classAsDict(entry).keys(): 
        if not element == "id":
            command += element + ", "
    command = command[:-2] + ") = ("
    command += "?, " * (len(classAsTuple(entry)) - 1)
    command = command[:-2] + ") WHERE id = ?"
    
