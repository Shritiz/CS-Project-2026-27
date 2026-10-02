import sqlite3
from pathlib import Path

from Program import Schema

class ValidationError(Exception): #Custom Error
    pass
def init_database(schema, database_path: str):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()

def close_database(conn: sqlite3.Connection):
    if conn:
        conn.close()

def get_database_connection(database_path: str):
    conn = sqlite3.connect(database_path)
    return conn

def isRequired(conn: sqlite3.Connection, value: str, label: str):
    val = str(value).strip()
    if not val:
        raise ValidationError(f"{label} is required.")
    return val
def Create_To(conn: sqlite3.Connection, name: str,sport: str,format:str, status: str, Sdate: str, Edate: str):
    name = isRequired(conn, name, "Tournament Name")
    sport = isRequired(conn, sport, "Sport")
    format = isRequired(conn, format, "Format")
    if status not in ['Scheduled', 'Ongoing', 'Completed']:
        raise ValidationError("Invalid status. Must be 'Scheduled', 'Ongoing', or 'Completed'.")
    
    Sdate = Sdate if Sdate else None
    Edate = Edate if Edate else None
    try:
        cursoe = conn.execute(
            
            "INSERT INTO tournaments (name, sport, format, status, Sdate, Edate) VALUES (?, ?, ?, ?, ?, ?)",
            (name, sport, format, status, Sdate, Edate)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"{e}: Tornmant with same name alredy exist") from e
    return int(cursoe.lastrowid)


def get_To(conn: sqlite3.connection, Toid):
    Toid = isRequired(conn, Toid, "Tournament ID")
    try:
        Toid = int(Toid)
    except (TypeError, ValueError):
        raise ValidationError("Tournament ID must be a Whole number.")
    if Toid <= 0:
        raise ValidationError("Tournament ID must be a positive Whole number.")
    cursor = conn.execute("SELECT * FROM tournaments WHERE toid = ?", (Toid,))
    row = cursor.fetchone()
    if row is None:
        raise ValidationError(f"Tournament with ID {Toid} not found.")
    return row

def add_Te(conn: sqlite3.Connection, name:str, Toid: int):
    Tour = get_To(conn, Toid)
    name = isRequired(conn, name, "Team Name")
    try:
        cursor = conn.execute(
            "INSERT INTO teams (name, Toid) VALUES (?, ?)",
            (Tour["Toid"], Toid)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"{e}: Team with same name alredy exist") from e
    return int(cursor.lastrowid)

def add_P(conn: sqlite3.Connection, name:str, Teid: int):
    Teid = isRequired(conn, Teid, "Team ID")
    name = isRequired(conn, name, "Player Name")
    try:
        Teid = int(Teid)
    except (TypeError, ValueError):
        raise ValidationError("Team ID must be a Whole number.")
    if Teid <= 0:
        raise ValidationError("Team ID must be a positive Whole number.")
    cursor = conn.execute("SELECT * FROM teams WHERE Teid = ?", (Teid,))
    row = cursor.fetchone()
    if row is None:
        raise ValidationError(f"Team with ID {Teid} not found.")
    try:
        cursor = conn.execute(
            "INSERT INTO players (name, Teid) VALUES (?, ?)",
            (name, Teid)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"{e}: Player with same name alredy exist") from e
    return int(cursor.lastrowid)


def lst_To(conn: sqlite3.Connection):
    cursor = conn.execute("SELECT * FROM tournaments ORDER BY toid")
    return cursor.fetchall()

def lst_Te(conn: sqlite3.Connection, Toid: int):
    Tour = get_To(conn, Toid)
    cursor = conn.execute("SELECT * FROM teams WHERE Toid = ? ORDER BY name", (Tour["Toid"],))
    return cursor.fetchall()

def lst_P