import sqlite3
import os
from database.classes import *
from dataclasses import asdict as asdict
from aethermanager import logger

def generateDB(cursor, database):
    logger.debug("Generating database...")
    command = """CREATE TABLE IF NOT EXISTS "users" (
id INTEGER,
firstname TEXT NOT NULL, 
lastname TEXT DEFAULT NULL,
phone INTEGER DEFAULT NULL, 
langcode TEXT DEFAULT "RU",
opendms BOOLEAN DEFAULT FALSE, 
balance INTEGER DEFAULT 0,
reputation INTEGER DEFAULT 0,
PRIMARY KEY (id))
"""
    cursor.execute(command)
    database.commit()
    logger.debug("Database created")


if not os.path.exists("database/main.db"):
    logger.debug("Database generation required")
    database = sqlite3.connect("database/main.db")
    cursor = database.cursor()
    generateDB(cursor, database)
else: 
    database = sqlite3.connect("database/main.db")
    cursor = database.cursor()
    