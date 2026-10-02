import sqlite3
from pathlib import Path

from Program import Schema

class ValidationError(Exception): #Custom Error
    pass
def init_database(database_path: str):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.executescript(Schema)
    conn.commit()

def close_database(conn: sqlite3.Connection):
    if conn:
        conn.close()

def get_database_connection(database_path: str):
    conn = sqlite3.connect(database_path)
    return conn


def Create_to(conn: sqlite3.Connection, name: str, start_date: str, end_date: str):