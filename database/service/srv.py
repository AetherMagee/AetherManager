from xml.dom import NotFoundErr
from database.classes import *
from aethermanager import logger
import database.dataAccess.dal as dal


def writeUser(id: int, 
    firstname: str = "",
    lastname: str = None,
    username: str = None,
    phone: int = None,
    langcode: str = "ru",
    opendms: bool = False,
    balance: int = 0,
    reputation: int = 0,
    ):
    instanceToWrite = dbUser(id, firstname, lastname, username, phone, langcode, opendms, balance, reputation)
    dal.writeNewUserEntry(instanceToWrite)


def getUser(searchRequest, errorOnNone = False, createNewIfNone = False):
    if isinstance(searchRequest, int):
        result = dal.readUserEntryByID(searchRequest)
        if not result:
            dal.readUserEntryByPhone(searchRequest)
            if not result:
                if errorOnNone: raise NotFoundErr
                if createNewIfNone: writeUser(searchRequest); result = getUser(searchRequest); return result
                return None
            return result
        return result
    else:
        result = dal.readUserEntryByUsername(searchRequest)
        if not result:
            if errorOnNone: raise NotFoundErr
            else: return None
        return result


def updateUser(newInstance: dbUser, createNewIfNotFound = False):
    checkResult = dal.readUserEntryByID(newInstance.id)
    if not checkResult:
        if createNewIfNotFound: 
            dal.writeNewUserEntry(dbUser)
            updateUser(newInstance)
            return
        else: raise NotFoundErr
    dal.editUserEntry(newInstance)


