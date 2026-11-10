import sqlite3
from typing import Any
from Modules.functions import *

# ``Modules.functions`` imports Schema, so define the schema before importing it.
Schema = """
CREATE TABLE IF NOT EXISTS tournaments (
    Toid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    sport TEXT NOT NULL,
    format TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Scheduled'
        CHECK(status IN ('Scheduled', 'Ongoing', 'Completed')),
    Sdate TEXT,
    Edate TEXT
);

CREATE TABLE IF NOT EXISTS teams (
    Teid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    Toid INTEGER NOT NULL,
    UNIQUE (Toid, name),
    FOREIGN KEY (Toid) REFERENCES tournaments (Toid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS players (
    Pid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    Teid INTEGER NOT NULL,
    FOREIGN KEY (Teid) REFERENCES teams (Teid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
    Mid INTEGER PRIMARY KEY AUTOINCREMENT,
    Toid INTEGER NOT NULL,
    Teid1 INTEGER NOT NULL,
    Teid2 INTEGER NOT NULL,
    Mdate TEXT NOT NULL,
    Mtime TEXT NOT NULL,
    Venue TEXT,
    Status TEXT NOT NULL DEFAULT 'Scheduled'
        CHECK(Status IN ('Scheduled', 'Completed', 'Cancelled')),
    CHECK(Teid1 <> Teid2),
    FOREIGN KEY (Toid) REFERENCES tournaments (Toid) ON DELETE CASCADE,
    FOREIGN KEY (Teid1) REFERENCES teams (Teid) ON DELETE CASCADE,
    FOREIGN KEY (Teid2) REFERENCES teams (Teid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS results (
    Rid INTEGER PRIMARY KEY AUTOINCREMENT,
    Mid INTEGER NOT NULL UNIQUE,
    Teid1_score INTEGER NOT NULL CHECK(Teid1_score >= 0),
    Teid2_score INTEGER NOT NULL CHECK(Teid2_score >= 0),
    FOREIGN KEY (Mid) REFERENCES matches (Mid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_To_id ON tournaments (Toid);
CREATE INDEX IF NOT EXISTS idx_Te_id ON teams (Teid);
CREATE INDEX IF NOT EXISTS idx_P_id ON players (Pid);
CREATE INDEX IF NOT EXISTS idx_TO_id ON matches (Toid, Status);
"""
def generate_fixtures(conn: sqlite3.Connection, tournament_id: Any) -> list[int]:
    """Generate one round-robin fixture for every pair of teams."""
    tournament = get_To(conn, tournament_id)
    teams = lst_Te(conn, tournament["Toid"])
    if len(teams) < 2:
        raise ValidationError("At least two teams are required to generate fixtures.")
    if conn.execute(
        "SELECT 1 FROM matches WHERE Toid = ? LIMIT 1", (tournament["Toid"],)
    ).fetchone():
        raise ValidationError("Fixtures already exist for this tournament.")

    participants = list(teams)
    if len(participants) % 2:
        participants.append(None)

    created: list[int] = []
    for round_number in range(1, len(participants)):
        for index in range(len(participants) // 2):
            first = participants[index]
            second = participants[-index - 1]
            if first is None or second is None:
                continue
            cursor = conn.execute(
                """INSERT INTO matches
                   (Toid, Teid1, Teid2, Mdate, Mtime, Venue, Status)
                   VALUES (?, ?, ?, DATE('now'), TIME('now'), NULL, 'Scheduled')""",
                (tournament["Toid"], first["Teid"], second["Teid"]),
            )
            created.append(int(cursor.lastrowid))
        participants = [participants[0]] + [participants[-1]] + participants[1:-1]
    conn.commit()
    return created


def run_cli(conn: sqlite3.Connection) -> None:
    print("\n=== TOURNAMENT MANAGER ===")
    while True:
        print(
            """\n1. List tournaments        2. Create tournament
3. Register team           4. Register player
5. List teams/players      6. Generate round-robin fixtures
7. List matches             8. Enter match result
9. View standings          10. Search
11. Statistics             0. Exit"""
        )
        choice = input("\nChoose an option: ").strip()
        try:
            if choice == "0":
                print("Goodbye!")
                return
            if choice == "1":
                print_rows(
                    lst_To(conn),
                    [("Toid", "ID"), ("name", "Name"), ("sport", "Sport"), ("status", "Status")],
                )
            elif choice == "2":
                create_tournament_cli(conn)
            elif choice == "3":
                tournament = choose_tournament(conn)
                if tournament:
                    team_name = input("Team name: ").strip()
                    team_id = add_Te(conn, team_name, tournament["Toid"])
                    # add_Te in the supplied helper currently stores Toid as the name.
                    conn.execute("UPDATE teams SET name = ? WHERE Teid = ?", (team_name, team_id))
                    conn.commit()
                    print(f"Team ID: {team_id}")
            elif choice == "4":
                team_id = prompt_int("Team ID")
                player_name = input("Player name: ")
                print(f"Player ID: {add_P(conn, player_name, team_id)}")
            elif choice == "5":
                tournament = choose_tournament(conn)
                if tournament:
                    print_rows(
                        lst_Te(conn, tournament["Toid"]),
                        [("Teid", "ID"), ("name", "Team")],
                    )
                    print_rows(
                        lst_P(conn, None, tournament["Toid"]),
                        [("Pid", "ID"), ("name", "Player"), ("Tname", "Team")],
                    )
            elif choice == "6":
                tournament = choose_tournament(conn)
                if tournament:
                    print(f"Created {len(generate_fixtures(conn, tournament['Toid']))} fixtures.")
            elif choice == "7":
                tournament = choose_tournament(conn)
                if tournament:
                    print_rows(
                        lst_M(conn, tournament["Toid"], None),
                        [
                            ("Mid", "ID"),
                            ("Mdate", "Date"),
                            ("Mtime", "Time"),
                            ("team1_name", "Team 1"),
                            ("team2_name", "Team 2"),
                            ("Status", "Status"),
                            ("Teid1_score", "Score 1"),
                            ("Teid2_score", "Score 2"),
                        ],
                    )
            elif choice == "8":
                rec_r(conn, prompt_int("Match ID"), prompt_int("Team 1 score"), prompt_int("Team 2 score"))
                print("Result saved.")
            elif choice == "9":
                tournament = choose_tournament(conn)
                if tournament:
                    print_rows(
                        standings(conn, tournament["Toid"]),
                        [
                            ("team", "Team"),
                            ("played", "P"),
                            ("wins", "W"),
                            ("draws", "D"),
                            ("losses", "L"),
                            ("for", "For"),
                            ("against", "Against"),
                            ("difference", "Diff"),
                            ("points", "Pts"),
                        ],
                    )
            elif choice == "10":
                results = search(conn, input("Search term: "))
                print("Teams:")
                print_rows(results["teams"], [("name", "Team"), ("tournament_name", "Tournament")])
                print("Players:")
                print_rows(results["players"], [("name", "Player"), ("team_name", "Team"), ("tournament_name", "Tournament")])
            elif choice == "11":
                tournament = choose_tournament(conn)
                if tournament:
                    print(statistics(conn, tournament["Toid"]))
            else:
                print("Please choose a valid menu option.")
        except ValidationError as exc:
            print(f"Error: {exc}")
        except sqlite3.IntegrityError as exc:
            print(f"Database error: {exc}")
        except sqlite3.Error as exc:
            print(f"Database error: {exc}")


def main() -> None:
    conn = None
    try:
        conn = init_database(Schema, "tournament.db")
        run_cli(conn)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
