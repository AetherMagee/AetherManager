import sqlite3
# # Apply HowYourBot patch
# dbObject = sqlite3.connect("database/chats.db")
# cursor = dbObject.cursor()
# cursor.execute("ALTER TABLE chats ADD howyourbot BOOLEAN NOT NULL DEFAULT 1")
# dbObject.commit()

# # Apply BotIsParticipant patch
# dbObject = sqlite3.connect("database/chats.db")
# cursor = dbObject.cursor()
# cursor.execute("ALTER TABLE chats ADD isparticipant BOOLEAN NOT NULL DEFAULT 1")
# dbObject.commit()

# Apply Filters patch
dbObject = sqlite3.connect("database/chats.db")
cursor = dbObject.cursor()
cursor.execute("ALTER TABLE chats ADD filters TEXT DEFAULT NULL")
cursor.execute("ALTER TABLE chats ADD filters_active BOOLEAN NOT NULL DEFAULT 1")
dbObject.commit()

# Apply peopleCount patch
db = sqlite3.connect("database/other.db")
cursor = db.cursor()
cursor.execute("""CREATE TABLE "peopleCount" (
"chid" INTEGER NOT NULL,
"count" INTEGER NOT NULL,
"datetime" TEXT NOT NULL,
PRIMARY KEY("datetime")
)""")
db.commit()