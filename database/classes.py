from dataclasses import dataclass

@dataclass()
class dbUser:
    id: int
    firstname: str = ""
    lastname: str = None
    phone: int = None
    langcode: str = "ru"
    opendms: bool = False
    balance: int = 0
    reputation: int = 0
    
@dataclass()
class dbChat:
    chid: int
    isparticipant: bool = True
    filtersActive: bool = False
    allowInvites: bool = True
    allowTT: bool = True
    allowHowYour: bool = True
    allowBots: bool = False
    settingsPermissionLevel: int = 2
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # 0 - Everyone
    # 1 - All admins
    # 2 - Admins with "Edit group" permission
    # 3 - Creator only
    
    allowMuteAdmins: bool = False
    
class Cursor: 
    def __init__(self, connection, autocommit = True):
        self.connection = connection
        self.autocommit = autocommit

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, typ, value, traceback):
        self.cursor.close()
        if self.autocommit:
            self.connection.commit()