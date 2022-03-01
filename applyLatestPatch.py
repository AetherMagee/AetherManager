# # Apply HowYourBot patch
# import sqlite3
# dbObject = sqlite3.connect("database/chats.db")
# cursor = dbObject.cursor()
# cursor.execute("ALTER TABLE chats ADD howyourbot BOOLEAN NOT NULL DEFAULT 1")
# dbObject.commit()

# Apply BotIsParticipant patch
import sqlite3
dbObject = sqlite3.connect("database/chats.db")
cursor = dbObject.cursor()
cursor.execute("ALTER TABLE chats ADD isparticipant BOOLEAN NOT NULL DEFAULT 1")
dbObject.commit()