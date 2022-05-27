from xml.dom import NotFoundErr
from database.classes import *
from aethermanager import logger
import database.dataAccess.dal as dal
from telethon.tl.types import User as tlUser


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
    instanceToWrite = dbUser(
        id, firstname, lastname, username, phone, langcode, opendms, balance, reputation)
    if instanceToWrite.langcode is None:
        instanceToWrite.langcode = "ru"
    dal.writeNewUserEntry(instanceToWrite)


def getUser(searchRequest: int or str or dbUser or tlUser, errorOnNone=False, createNewIfNone=True):
    if isinstance(searchRequest, int):
        result = dal.readUserEntryByID(searchRequest)
        if not result:
            dal.readUserEntryByPhone(searchRequest)
            if not result:
                if errorOnNone:
                    raise NotFoundErr
                if createNewIfNone:
                    writeUser(searchRequest)
                    result = getUser(searchRequest)
                    return result
                return None
            return result
        return result
    elif isinstance(searchRequest, str):
        result = dal.readUserEntryByUsername(searchRequest)
        if not result:
            if errorOnNone:
                raise NotFoundErr
            else:
                return None
        return result
    elif isinstance(searchRequest, tlUser):
        searchRequest = dbUser(searchRequest.id, searchRequest.first_name, searchRequest.last_name,
                               searchRequest.username, searchRequest.phone, searchRequest.lang_code)
    if isinstance(searchRequest, dbUser):
        result = dal.readUserEntryByID(searchRequest.id)
        if not result:
            if errorOnNone:
                raise NotFoundErr
            if createNewIfNone:
                dal.writeNewUserEntry(searchRequest)
                return searchRequest
        if result.firstname != searchRequest.firstname or result.lastname != searchRequest.lastname or result.phone != searchRequest.phone or result.username != searchRequest.username:
            searchRequest.reputation = result.reputation
            searchRequest.balance = result.balance
            if result.langcode is None:
                searchRequest.langcode = "ru"
            updateUser(searchRequest)
        if result.langcode is None:
            result.langcode = "ru"
        return result


def updateUser(newInstance: dbUser or tlUser, createNewIfNotFound=True):
    if isinstance(newInstance, tlUser):
        newInstance = dbUser(newInstance.id, newInstance.first_name, newInstance.last_name,
                             newInstance.username, newInstance.phone, newInstance.lang_code)
    checkResult = dal.readUserEntryByID(newInstance.id)
    if not checkResult:
        logger.debug("Not found")
        if createNewIfNotFound:
            dal.writeNewUserEntry(newInstance)
            return
        else:
            raise NotFoundErr
    logger.debug("Editing user...")
    dal.editUserEntry(newInstance)


def writeChat(chid: int,
              isparticipant: bool = True,
              filtersActive: bool = False,
              allowInvites: bool = True,
              allowTT: bool = True,
              allowHowYour: bool = True,
              allowBots: bool = False,
              settingsPermissionLevel: int = 2,
              allowMuteAdmins: bool = False):
    instanceToWrite = dbChat(chid, isparticipant, filtersActive, allowInvites,
                             allowTT, allowHowYour, allowBots, settingsPermissionLevel, allowMuteAdmins)
    dal.writeNewChatEntry(instanceToWrite)


def getChat(searchRequest: int, errorOnNone=False, createNewIfNone=False):
    if isinstance(searchRequest, dbChat):
        searchRequest = searchRequest.chid
    result = dal.readChatEntryByID(searchRequest)
    if not result:
        if errorOnNone:
            raise NotFoundErr
        if createNewIfNone:
            writeChat(searchRequest)
            return getChat(searchRequest)
        else:
            return None
    return result


def updateChat(newInstance: dbChat, createNewIfNotFound=False):
    checkResult = dal.readChatEntryByID(newInstance.chid)
    if not checkResult:
        if createNewIfNotFound:
            dal.writeNewChatEntry(newInstance)
            return
        else:
            raise NotFoundErr
    dal.editChatEntry(newInstance)
