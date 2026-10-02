import sqlite3
from pathlib import Path

from Program import Schema

class ValidationError(Exception): #Custom Error
    pass
def init_database(schema, database_path: str): #connect database to the program
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()

def close_database(conn: sqlite3.Connection): #close the databse when done
    if conn:
        conn.close()

def get_connection(database_path: str):
    conn = sqlite3.connect(database_path)
    return conn

def isRequired(conn: sqlite3.Connection, value: str, label: str): #check if the value is present which cannot be empty
    val = str(value).strip()
    if not val:
        raise ValidationError(f"{label} is required.")
    return val
def Create_To(conn: sqlite3.Connection, name: str,sport: str,format:str, status: str, Sdate: str, Edate: str): #Creating a tournament 
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


def get_To(conn: sqlite3.connection, Toid): #getting To data based on Toid
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

def add_Te(conn: sqlite3.Connection, name:str, Toid: int): #New team here add
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

def add_P(conn: sqlite3.Connection, name:str, Teid: int): #New player add here
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

##------List functions-----#
def lst_To(conn: sqlite3.Connection):
    cursor = conn.execute("SELECT * FROM tournaments ORDER BY toid")
    return cursor.fetchall()

def lst_Te(conn: sqlite3.Connection, Toid: int):
    Tour = get_To(conn, Toid)
    cursor = conn.execute("SELECT * FROM teams WHERE Toid = ? ORDER BY name", (Tour["Toid"],))
    return cursor.fetchall()

def lst_P(conn: sqlite3.Connection, Teid: int, Toid: int):
    qry = "SELECT p.*, t.name AS Tname, t.Toid FROM players p JOIN teams t ON t.Teid = p.Teid" 
    parm = []
    if Teid is not None:
        qry += " WHERE p.Teid = ?"
        try:
            Teid = int(Teid)
        except (TypeError, ValueError):
            raise ValidationError("Team ID must be a Whole number.")
        if Teid <= 0:
            raise ValidationError("Team ID must be a positive Whole number.")
        parm.append(Teid)
    elif Toid is not None:
        Tour = get_To(conn, Toid)
        qry += " WHERE t.Toid = ?"
        parm.append(Tour["Toid"])
    qry += " ORDER BY p.name"
    cursor = conn.execute(qry, parm)
    return cursor.fetchall()

def lst_M(conn: sqlite3.Connection, Toid: int,status: str):
    Tour = get_To(conn, Toid)
    qry = "SELECT m.*, a.name AS t1_name, b.name AS t2_name, r.t1_score, r.t2_score FROM matches m JOIN teams a ON a.Teid = m.t1_id JOIN teams b ON b.Teid = m.t2_id JOIN results r ON r.match_id = m.match_id WHERE m.Toid = ?"
    parm = [Tour["Toid"]]
    if status:
        if status not in {"Scheduled", "Completed", "Cancelled"}:
            raise ValidationError("Invalid status. Must be 'Scheduled', 'Completed', or 'Cancelled'.")
        qry += " AND m.status = ?"
        parm.append(status)
    qry += " ORDER BY m.Mdate, m.Mtime"
    cursor = conn.execute(qry, parm)
    return cursor.fetchall()


def gen_round_robin():
    pass # take a crack at it when i know what it is 

def rec_r(conn: sqlite3.Connection, Mid: int, t1_score, t2_score): #record the results isn't that obv
    Mid = isRequired(conn, Mid, "Match ID")
    try:
        Mid = int(Mid)
    except (TypeError, ValueError):
        raise ValidationError("Match ID must be a Whole number.")
    if Mid <= 0:
        raise ValidationError("Match ID must be a positive Whole number.")
    cursor = conn.execute("SELECT * FROM matches WHERE Mid = ?", (Mid,))
    match = cursor.fetchone()
    if match is None:
        raise ValidationError(f"Match with ID {Mid} not found.")
    if match['Status'] == 'Completed':
        raise ValidationError(f"Match with ID {Mid} had been concluded .")
    t1_score = isRequired(conn, t1_score, "Team 1 Score")
    t2_score = isRequired(conn, t2_score, "Team 2 Score")
    if t1_score < 0 or t2_score < 0:
        raise ValidationError("Scores must be non-negative integers.")
    The_winner = None if t1_score== t2_score else match['Teid1'] if t1_score > t2_score else match['Teid2']
    with conn:
        conn.execute("INSERT INTO results (Mid, t1_score, t2_score, The_winner) VALUES (?, ?, ?, ?)", (Mid, t1_score, t2_score, The_winner),)
        conn.execute("UPDATE matches SET Status = 'Completed' WHERE Mid = ?", (Mid,))

def standings(conn: sqlite3.Connection, Toid: int):
    pass #come to it tmr lol

