import sqlite3

usersDB, chatsDB, altnamesDB, mutedadminsDB, otherDB = None, None, None, None, None
usersCursor, chatsCursor, altnamesCursor, mutedadminsCursor, otherCursor = None, None, None, None, None



def deleteNonASCII(string):
    return string # string.encode('ascii', 'replace').decode() <-- Turns out this one deletes cirillyc characters too, and im just too lazy to remove it from all the functions.



def addUserEntry(id, username = None, phone = None, reputation = 0, money = 0, contacts = None, opendms = False, withCommit = True):
    try:
        command = f"""INSERT INTO users (id, username, phone, reputation, money, contacts, opendms) VALUES ({id}, "{str(username)}", "{str(phone)}", "{str(reputation)}", "{str(money)}", "{str(contacts)}", {"1" if opendms else "0"})"""
        usersCursor.execute(command)
        if withCommit:
            usersDB.commit()
    except: 
        return "AlreadyInDBError"
    altnamesCursor.execute(f"INSERT INTO altnames (id) VALUES ({str(id)})")
    if withCommit:
        altnamesDB.commit()
    return "Success"



def commitToUsersDB():
    usersDB.commit()



def getUserEntry(searchRequest, searchMethod = "all", objectToReturn = "all"):
    # Chosing how to search for user
    searchMethodsToUse = []
    availableSearchMethods = ["id", "username", "phone"]
    if not searchMethod == "all":
        if searchMethod.lower() in availableSearchMethods:
            searchMethodsToUse += searchMethod.lower()
        else:
            raise "The search method that you specified is invalid. Availible methods: " + str(availableSearchMethods)
    else:
        searchMethodsToUse = availableSearchMethods
    
    # Chosing what to return
    if objectToReturn == "all":
        objectToReturn = "*"
    
    # Searching
    found = False
    if "id" in searchMethodsToUse:
        if str(searchRequest).isnumeric():
            usersCursor.execute(f"SELECT {objectToReturn} FROM users WHERE id={str(searchRequest)}")
            result = usersCursor.fetchall()
            if result:
                found = True
    if "username" in searchMethodsToUse and not found:
        usersCursor.execute(f"SELECT {objectToReturn} FROM users WHERE username=\"{str(searchRequest)}\"")
        result = usersCursor.fetchall()
        if result:
            found = True
    if "phone" in searchMethodsToUse and not found:
        usersCursor.execute(f"SELECT {objectToReturn} FROM users WHERE phone=\"{str(searchRequest)}\"")
        result = usersCursor.fetchall()
        if result:
            found = True
    
    # Returning the result
    if found and result:
        return(result)
    else:
        return("NotFound")
    


def editUserEntry(userID, whatToEdit, editToWhat):
    if not str(editToWhat).isnumeric():
        editToWhat = "\"" + str(editToWhat) + "\""
    try:
        usersCursor.execute(f"UPDATE users SET {whatToEdit} = {str(editToWhat)} WHERE id = {userID}")
        usersDB.commit()
        return "Success"
    except:
        return("Error")



def getAltNames(userID):
    altnamesCursor.execute(f"SELECT altnames FROM altnames WHERE id = {userID}")
    result = altnamesCursor.fetchall()[0][0]
    if result:
        return result.split(" | ")
    else:
        return []



def addAltName(userID, altName):
    # Cleaning the altname to avoid errors and SQL-injections. 
    altName = altName.lower()
    altName = deleteNonASCII(altName)
    forbiddenCharsAndWords = ["\"", "'", "select", "drop", ";", "]", "[", "{", "}", "|", "(", ")", "delete"]
    for item in forbiddenCharsAndWords:
        altName = altName.replace(item, "").replace(" ", "_")
    
    # Checking if altName is already claimed
    try:
        altnamesCursor.execute(f"SELECT altnames FROM altnames WHERE id = {str(userID)}")
        result = altnamesCursor.fetchall()[0][0]
    except:
        return "DoesNotExistsInDBError"
    if result:
        altNamesAvailible = result
    else:
        altNamesAvailible = ""
    try:
        altNamesList = altNamesAvailible.split(" | ")
    except:
        altNamesList = []
    if altName in altNamesList:
        return "AlreadyClaimedError"
    
    # Writing and sending the altname
    if altNamesAvailible != "": splitter = " | "
    else: splitter = ""
    altNamesAvailible += splitter + str(altName)
    try:
        altnamesCursor.execute(f"UPDATE altnames SET altnames = \"{str(altNamesAvailible)}\" WHERE id={str(userID)}")
        altnamesDB.commit()
        return "Success"
    except Exception as e:
        return "Error: " + str(e)



def deleteAltName(userID, altName):
    # Cleaning the altname to avoid errors and SQL-injections. 
    altName = altName.lower()
    altName = deleteNonASCII(altName)
    forbiddenCharsAndWords = ["\"", "'", "select", "drop", ";", "]", "[", "{", "}", "|", "(", ")", "delete"]
    for item in forbiddenCharsAndWords:
        altName = altName.replace(item, "").replace(" ", "_")
    
    # Checking if altName is present
    altnamesCursor.execute(f"SELECT altnames FROM altnames WHERE id = {str(userID)}")
    result = altnamesCursor.fetchall()[0][0]
    if result:
        altNamesAvailible = result
    else:
        altNamesAvailible = ""
    try:
        altNamesList = altNamesAvailible.split(" | ")
    except:
        altNamesList = []
    if not altName in altNamesList:
        return "DoesNotExistsError"
    
    # Removing it from the list, turning the list back to string and sending it
    altNamesList.remove(altName)
    altNamesNew = ""
    for name in altNamesList:
        if altNamesNew != "": splitter = " | "
        else: splitter = ""
        altNamesNew += splitter + name
    try:
        altnamesCursor.execute(f"UPDATE altnames SET altnames = \"{altNamesNew}\" WHERE id={str(userID)}")
        altnamesDB.commit()
        return "Success"
    except Exception as e:
        return "Error: " + str(e)



def searchUserByAltName(altName):
    # Cleaning the altname to avoid errors and SQL-injections. 
    altName = altName.lower()
    altName = deleteNonASCII(altName)
    forbiddenCharsAndWords = ["\"", "'", "select", "drop", ";", "]", "[", "{", "}", "|", "(", ")", "delete"]
    for item in forbiddenCharsAndWords:
        altName = altName.replace(item, "").replace(" ", "_")

    # Searching
    altnamesCursor.execute(f"SELECT * FROM altnames")
    allAltNamesRaw = altnamesCursor.fetchall()
    for entry in allAltNamesRaw:
        userID = entry[0]
        altNames = entry[1]
        if altNames == "" or altNames == None:
            continue
        altNamesList = altNames.split(" | ")
        for name in altNamesList:
            if name == altName:
                return int(userID)
    return "NotFound"



def getSettingsForChat(chatID, itemToReturn = "all"):
    if itemToReturn == "all":
        itemToReturn = "*"
    chatsCursor.execute(f"SELECT {itemToReturn} FROM chats WHERE chid = {chatID}")
    result = chatsCursor.fetchall()
    if not bool(result):
        return "ChatNotFound"
    return result



def checkMutedAdmin(userID, chatID):
    mutedadminsCursor.execute(f"SELECT * FROM muted_admins WHERE user_id = {userID} AND chid = {chatID}")
    result = mutedadminsCursor.fetchall()
    if bool(result):
        return 1, result[0][2]
    return 0, None



def registerNewMutedAdmin(userID, chatID, reason):
    isAlreadyMuted = checkMutedAdmin(userID, chatID)[0]
    if isAlreadyMuted:
        return "AlreadyMutedError"
    mutedadminsCursor.execute(f"INSERT INTO muted_admins (user_id, chid, mute_reason) VALUES ({userID}, {chatID}, \"{reason}\")")
    mutedadminsDB.commit()
    return "Success"



def deleteMutedAdmin(userID, chatID):
    isAlreadyMuted = checkMutedAdmin(userID, chatID)[0]
    if isAlreadyMuted:
        try:
            mutedadminsCursor.execute(f"DELETE FROM muted_admins WHERE user_id = {userID} AND chid = {chatID}")
            mutedadminsDB.commit()
            return "Success"
        except Exception as e:
            print(str(e))
            return "Error"
    return "NotMuted"



def addChatEntry(chatID):
    try:
        chatsCursor.execute(f"INSERT INTO chats (chid) VALUES ({str(chatID)})")
        chatsDB.commit()
    except Exception as e: print(str(e)); return "Error"
    return "Success"


def editChatEntry(chatID, whatToEdit, editToWhat, mode = "bool"):
    if mode == "string":
        editToWhat = f"\"{editToWhat}\""
    try: 
        chatsCursor.execute(f"""UPDATE chats SET {whatToEdit} = {editToWhat} WHERE chid = {chatID}""")
        chatsDB.commit()
    except: return "Error"
    return "Success"

def init():
    global usersDB, chatsDB, altnamesDB, mutedadminsDB, otherDB, usersCursor, chatsCursor, altnamesCursor, mutedadminsCursor, otherCursor
    usersDB = sqlite3.connect("database/users.db")
    chatsDB = sqlite3.connect("database/chats.db")
    altnamesDB = sqlite3.connect("database/altnames.db")
    mutedadminsDB = sqlite3.connect("database/mutedadmins.db")
    otherDB = sqlite3.connect("database/other.db")
    usersCursor = usersDB.cursor()
    chatsCursor = chatsDB.cursor()
    altnamesCursor = altnamesDB.cursor()
    mutedadminsCursor = mutedadminsDB.cursor()
    otherCursor = otherDB.cursor()

if __name__ != "__main__":
    init()
else:
    print("AetherManager's database worker cannot be run as a standalone script!")