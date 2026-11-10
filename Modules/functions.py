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

def lst_M(conn: sqlite3.Connection, Toid: int,status: str): #list matches
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


def gen_round_robin(conn: sqlite3.Connection, Toid: int): #default fixture
    teams = lst_Te(conn, Toid)

    if len(teams) < 2:
        raise ValidationError("At least two teams are required.")

    # Check if fixtures already exist
    existing = conn.execute(
        "SELECT 1 FROM matches WHERE Toid = ?", (Toid,)
    ).fetchone()

    if existing:
        raise ValidationError("Fixtures already exist.")

    # Generate matches
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            conn.execute("""
                INSERT INTO matches (Toid, Teid1, Teid2, Mdate, Mtime, Status)
                VALUES (?, ?, ?, DATE('now'), TIME('now'), 'Scheduled')
            """, (Toid, teams[i]["Teid"], teams[j]["Teid"]))

    conn.commit()

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
    Tour = get_To(conn, Toid)
    tems = lst_Te(conn, Tour["Toid"])
    table = {
        team["Teid"]: {
            "Teid": team["Teid"],
            "team": team["name"],
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "for": 0,
            "against": 0,
            "points": 0,
        }
        for team in tems
    }

    matches = conn.execute(
        """SELECT m.Teid1, m.Teid2, r.Teid1_score, r.Teid2_score
           FROM matches m JOIN results r ON r.Mid = m.Mid
           WHERE m.Toid = ?""",
        (Tour["Toid"],),
    ).fetchall()

    for match in matches:
        first = table[match["Teid1"]]
        second = table[match["Teid2"]]
        score1 = match["Teid1_score"]
        score2 = match["Teid2_score"]
        first["played"] += 1
        second["played"] += 1
        first["for"] += score1
        first["against"] += score2
        second["for"] += score2
        second["against"] += score1

        if score1 == score2:
            first["draws"] += 1
            second["draws"] += 1
            first["points"] += 1
            second["points"] += 1
        elif score1 > score2:
            first["wins"] += 1
            second["losses"] += 1
            first["points"] += 3
        else:
            second["wins"] += 1
            first["losses"] += 1
            second["points"] += 3

    for row in table.values():
        row["difference"] = row["for"] - row["against"]

    def sort_key(r):
        return (-r["points"], -r["difference"], -r["for"], r["team"].lower())

    return sorted(table.values(), key=sort_key)


def search(conn: sqlite3.Connection, term: str, Toid=None): #search diff values in the database
    term = isRequired(conn, term, "Search term")
    pattern = f"%{term}%"
    team_parameters = [pattern]
    player_parameters = [pattern, pattern]
    To_clause = ""

    if Toid is not None: #if is given or no, then add the appropriate filter
        Tour = get_To(conn, Toid)
        To_clause = " AND t.Toid = ?"
        team_parameters.append(Tour["Toid"])
        player_parameters.append(Tour["Toid"])

    teams = conn.execute(
        """SELECT t.name, t.Toid, u.name AS tournament_name
           FROM teams t JOIN tournaments u ON u.Toid = t.Toid
           WHERE t.name LIKE ?""" + To_clause,
        team_parameters,
    ).fetchall()
    players = conn.execute(
        """SELECT p.name, t.name AS team_name, t.Toid,
                  u.name AS tournament_name
           FROM players p JOIN teams t ON t.Teid = p.Teid
           JOIN tournaments u ON u.Toid = t.Toid
           WHERE (p.name LIKE ? OR t.name LIKE ?)""" + To_clause,
        player_parameters,
    ).fetchall()
    return {"teams": teams, "players": players} #return dictornary of players and tms


def statistics(conn: sqlite3.Connection, Toid: int): #return the dictonary of player data
    Tour = get_To(conn, Toid)
    tournament_id = Tour["Toid"]
    row = conn.execute(
        """SELECT
           (SELECT COUNT(*) FROM teams WHERE Toid = ?) AS teams,
           (SELECT COUNT(*) FROM players p JOIN teams t ON t.Teid = p.Teid
             WHERE t.Toid = ?) AS players,
           (SELECT COUNT(*) FROM matches WHERE Toid = ?) AS matches,
           (SELECT COUNT(*) FROM matches WHERE Toid = ? AND Status = 'Completed') AS completed,
           (SELECT COUNT(*) FROM matches WHERE Toid = ? AND Status = 'Scheduled') AS upcoming,
           COALESCE((SELECT SUM(r.Teid1_score + r.Teid2_score)
             FROM results r JOIN matches m ON m.Mid = r.Mid
             WHERE m.Toid = ?), 0) AS total_score""",
        [tournament_id] * 6,
    ).fetchone()
    return dict(row)


def print_rows(rows, columns):
    """Print database rows using a list of (column name, heading) pairs."""
    rows = list(rows)
    if not rows:
        print("No records found.")
        return
    headings = " | ".join(title for _, title in columns)
    print("\\n" + headings)
    print("-" * (len(headings) + 2))
    for row in rows:
        print(" | ".join(
            str(row[key]) if row[key] is not None else "-"
            for key, _ in columns
        ))


def choose_tournament(conn): #display selected tournmant row
    tournaments = lst_To(conn)
    print_rows(
        tournaments,
        [("Toid", "ID"), ("name", "Name"), ("sport", "Sport"), ("status", "Status")],
    )
    if not tournaments:
        return None
    try:
        return get_To(conn, input("Tournament ID: "))
    except ValidationError as exc:
        print(f"Error: {exc}")
        return None


def prompt_int(label: str, default=None): #Idiot proof the code lol
    while True:
        value = input(f"{label}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not value and default is not None:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a whole number.")


def create_tournament_cli(conn): #adding TO esily, helpful function
    try:
        tournament_id = Create_To(
            conn,
            input("Tournament name: "),
            input("Sport: "),
            input("Format [Round Robin]: ").strip() or "Round Robin",
            input("Status [Scheduled]: ").strip() or "Scheduled",
            input("Start date (YYYY-MM-DD, optional): ").strip() or None,
            input("End date (YYYY-MM-DD, optional): ").strip() or None,
        )
        print(f"Tournament created with ID {tournament_id}.")
    except ValidationError as exc:
        print(f"Error: {exc}")

