import sqlite3

usersdb = sqlite3.connect("users.db")
udbcursor = usersdb.cursor()

udbcursor.execute("""CREATE TABLE "users" (
"id"    INTEGER NOT NULL,
"username" TEXT DEFAULT NULL,
"phone" TEXT DEFAULT NULL,
"reputation" INTEGER NOT NULL DEFAULT 0,
"money"	INTEGER NOT NULL DEFAULT 0,
"contacts" TEXT DEFAULT NULL,
"opendms" BOOLEAN NOT NULL,
PRIMARY KEY ("id")
)""")



altnamesdb = sqlite3.connect("altnames.db")
aldbcursor = altnamesdb.cursor()

aldbcursor.execute("""CREATE TABLE "altnames" (
"id" INTEGER NOT NULL,
"altnames" TEXT DEFAULT NULL,
PRIMARY KEY("id")
)""")


chatsdb = sqlite3.connect("chats.db")
chdbcursor = chatsdb.cursor()

chdbcursor.execute("""CREATE TABLE chats (
"chid"     INTEGER NOT NULL,
"mute_admins_allowed"	BOOLEAN NOT NULL DEFAULT 0,
"react_on_xiaomi"	BOOLEAN NOT NULL DEFAULT 1,
"react_on_ping"	BOOLEAN NOT NULL DEFAULT 1,
"allow_invite_links"	BOOLEAN NOT NULL DEFAULT 1,
"allow_tiktok_links"    BOOLEAN NOT NULL DEFAULT 1,
"custom_hello" TEXT NOT NULL DEFAULT 'None', 
"captcha" TEXT NOT NULL DEFAULT 'ad_only',
"who_can_change_settings" TEXT NOT NULL DEFAULT 'CreatorOnly',
"howyourbot" BOOLEAN NOT NULL DEFAULT 1,
PRIMARY KEY (chid)
)""")

otherDB = sqlite3.connect("other.db")
otherDBcursor = otherDB.cursor()
otherDBcursor.execute("""CREATE TABLE "ban_history" (
"ban_number"	INTEGER,
"id"	INTEGER NOT NULL,
"chat_id"	INTEGER NOT NULL,
"chat_title"	TEXT,
"reason"	TEXT,
"datetime"	TEXT,
"banned_by_id"	INTEGER,
"banned_by_name"	TEXT,
PRIMARY KEY("ban_number" AUTOINCREMENT)
)""")
otherDBcursor.execute("""CREATE TABLE "notes" (
"msgid"	INTEGER NOT NULL UNIQUE,
"chat_id"	INTEGER NOT NULL,
"note_author_id"	INTEGER NOT NULL,
"note_name"	TEXT NOT NULL UNIQUE
)""")

madb = sqlite3.connect("mutedadmins.db")
madb.cursor().execute("""CREATE TABLE "muted_admins" (
	"user_id"	INTEGER NOT NULL,
	"chid"	INTEGER NOT NULL,
	"mute_reason"	TEXT NOT NULL,
	PRIMARY KEY("user_id")
    )""")