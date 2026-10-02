from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path
from typing import Any, Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    sport TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'Round Robin',
    start_date TEXT,
    end_date TEXT,
    status TEXT NOT NULL DEFAULT 'Upcoming'
        CHECK (status IN ('Upcoming', 'Active', 'Completed', 'Cancelled')),
    win_points INTEGER NOT NULL DEFAULT 3 CHECK (win_points >= 0),
    draw_points INTEGER NOT NULL DEFAULT 1 CHECK (draw_points >= 0),
    loss_points INTEGER NOT NULL DEFAULT 0 CHECK (loss_points >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(tournament_id) ON DELETE CASCADE,
    name TEXT NOT NULL COLLATE NOCASE,
    captain TEXT NOT NULL,
    UNIQUE (tournament_id, name)
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 5 AND 100),
    jersey_number INTEGER NOT NULL CHECK (jersey_number > 0),
    UNIQUE (team_id, jersey_number)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(tournament_id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL CHECK (round_number > 0),
    team1_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    team2_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    match_date TEXT,
    match_time TEXT,
    venue TEXT,
    status TEXT NOT NULL DEFAULT 'Scheduled'
        CHECK (status IN ('Scheduled', 'Completed')),
    CHECK (team1_id <> team2_id),
    UNIQUE (tournament_id, round_number, team1_id, team2_id)
);

CREATE TABLE IF NOT EXISTS results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL UNIQUE REFERENCES matches(match_id) ON DELETE CASCADE,
    team1_score INTEGER NOT NULL CHECK (team1_score >= 0),
    team2_score INTEGER NOT NULL CHECK (team2_score >= 0),
    winner_id INTEGER REFERENCES teams(team_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_teams_tournament ON teams(tournament_id);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id, status);
"""


class ValidationError(ValueError):
    """Raised when an operation cannot be completed with the supplied values."""


class TournamentManager: #logic
    def __init__(self, database: str | Path = "tournament.db") -> None:
        self.connection = sqlite3.connect(str(database), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def _one(self, query: str, parameters: Iterable[Any] = ()) -> sqlite3.Row | None:
        return self.connection.execute(query, tuple(parameters)).fetchone()

    def _required(self, value: str, label: str) -> str:
        value = str(value).strip()
        if not value:
            raise ValidationError(f"{label} cannot be empty.")
        return value

    def _positive_int(self, value: Any, label: str) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{label} must be a whole number.") from exc
        if number <= 0:
            raise ValidationError(f"{label} must be greater than zero.")
        return number

    def _non_negative_int(self, value: Any, label: str) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{label} must be a whole number.") from exc
        if number < 0:
            raise ValidationError(f"{label} cannot be negative.")
        return number

    def create_tournament(
        self,
        name: str,
        sport: str,
        format_name: str = "Round Robin",
        start_date: str | None = None,
        end_date: str | None = None,
        status: str = "Upcoming",
        win_points: int = 3,
        draw_points: int = 1,
        loss_points: int = 0,
    ) -> int:
        name = self._required(name, "Tournament name")
        sport = self._required(sport, "Sport")
        format_name = self._required(format_name, "Format")
        if status not in {"Upcoming", "Active", "Completed", "Cancelled"}:
            raise ValidationError("Status must be Upcoming, Active, Completed, or Cancelled.")
        points = [self._non_negative_int(value, label) for value, label in (
            (win_points, "Win points"), (draw_points, "Draw points"), (loss_points, "Loss points")
        )]
        try:
            cursor = self.connection.execute(
                """INSERT INTO tournaments
                   (name, sport, format, start_date, end_date, status, win_points, draw_points, loss_points)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, sport, format_name, start_date or None, end_date or None, status, *points),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            self.connection.rollback()
            raise ValidationError("A tournament with that name already exists.") from exc
        return int(cursor.lastrowid)

    def list_tournaments(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM tournaments ORDER BY tournament_id"
        ).fetchall()

    def get_tournament(self, tournament_id: Any) -> sqlite3.Row:
        tournament_id = self._positive_int(tournament_id, "Tournament ID")
        row = self._one("SELECT * FROM tournaments WHERE tournament_id = ?", (tournament_id,))
        if row is None:
            raise ValidationError("Tournament not found.")
        return row

    def add_team(self, tournament_id: Any, name: str, captain: str) -> int:
        tournament = self.get_tournament(tournament_id)
        name = self._required(name, "Team name")
        captain = self._required(captain, "Captain")
        try:
            cursor = self.connection.execute(
                "INSERT INTO teams (tournament_id, name, captain) VALUES (?, ?, ?)",
                (tournament["tournament_id"], name, captain),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            self.connection.rollback()
            raise ValidationError("That team already exists in this tournament.") from exc
        return int(cursor.lastrowid)

    def list_teams(self, tournament_id: Any) -> list[sqlite3.Row]:
        tournament = self.get_tournament(tournament_id)
        return self.connection.execute(
            "SELECT * FROM teams WHERE tournament_id = ? ORDER BY name",
            (tournament["tournament_id"],),
        ).fetchall()

    def add_player(self, team_id: Any, name: str, age: Any, jersey_number: Any) -> int:
        team_id = self._positive_int(team_id, "Team ID")
        if self._one("SELECT team_id FROM teams WHERE team_id = ?", (team_id,)) is None:
            raise ValidationError("Team not found.")
        name = self._required(name, "Player name")
        age = self._positive_int(age, "Age")
        if not 5 <= age <= 100:
            raise ValidationError("Age must be between 5 and 100.")
        jersey_number = self._positive_int(jersey_number, "Jersey number")
        try:
            cursor = self.connection.execute(
                "INSERT INTO players (team_id, name, age, jersey_number) VALUES (?, ?, ?, ?)",
                (team_id, name, age, jersey_number),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            self.connection.rollback()
            raise ValidationError("That jersey number is already used by this team.") from exc
        return int(cursor.lastrowid)

    def list_players(self, team_id: Any | None = None, tournament_id: Any | None = None) -> list[sqlite3.Row]:
        query = """SELECT p.*, t.name AS team_name, t.tournament_id
                   FROM players p JOIN teams t ON t.team_id = p.team_id"""
        parameters: list[Any] = []
        if team_id is not None:
            query += " WHERE p.team_id = ?"
            parameters.append(self._positive_int(team_id, "Team ID"))
        elif tournament_id is not None:
            tournament = self.get_tournament(tournament_id)
            query += " WHERE t.tournament_id = ?"
            parameters.append(tournament["tournament_id"])
        query += " ORDER BY t.name, p.jersey_number"
        return self.connection.execute(query, parameters).fetchall()

    def generate_round_robin(self, tournament_id: Any) -> list[int]:
        tournament = self.get_tournament(tournament_id)
        teams = self.list_teams(tournament["tournament_id"])
        if len(teams) < 2:
            raise ValidationError("Register at least two teams before generating fixtures.")
        existing = self._one(
            "SELECT match_id FROM matches WHERE tournament_id = ? LIMIT 1",
            (tournament["tournament_id"],),
        )
        if existing:
            raise ValidationError("Fixtures already exist for this tournament.")

        participants = list(teams)
        if len(participants) % 2:
            participants.append(None)
        rounds = len(participants) - 1
        created: list[int] = []
        for round_number in range(1, rounds + 1):
            for index in range(len(participants) // 2):
                first, second = participants[index], participants[-index - 1]
                if first is not None and second is not None:
                    cursor = self.connection.execute(
                        """INSERT INTO matches
                           (tournament_id, round_number, team1_id, team2_id)
                           VALUES (?, ?, ?, ?)""",
                        (tournament["tournament_id"], round_number, first["team_id"], second["team_id"]),
                    )
                    created.append(int(cursor.lastrowid))
            participants = [participants[0]] + [participants[-1]] + participants[1:-1]
        self.connection.commit()
        return created

    def list_matches(self, tournament_id: Any, status: str | None = None) -> list[sqlite3.Row]:
        tournament = self.get_tournament(tournament_id)
        query = """SELECT m.*, a.name AS team1_name, b.name AS team2_name,
                          r.team1_score, r.team2_score
                   FROM matches m
                   JOIN teams a ON a.team_id = m.team1_id
                   JOIN teams b ON b.team_id = m.team2_id
                   LEFT JOIN results r ON r.match_id = m.match_id
                   WHERE m.tournament_id = ?"""
        parameters: list[Any] = [tournament["tournament_id"]]
        if status:
            if status not in {"Scheduled", "Completed"}:
                raise ValidationError("Match status must be Scheduled or Completed.")
            query += " AND m.status = ?"
            parameters.append(status)
        query += " ORDER BY m.round_number, m.match_id"
        return self.connection.execute(query, parameters).fetchall()

    def record_result(self, match_id: Any, team1_score: Any, team2_score: Any) -> None:
        match_id = self._positive_int(match_id, "Match ID")
        match = self._one("SELECT * FROM matches WHERE match_id = ?", (match_id,))
        if match is None:
            raise ValidationError("Match not found.")
        if match["status"] == "Completed":
            raise ValidationError("This match already has a result.")
        team1_score = self._non_negative_int(team1_score, "Team 1 score")
        team2_score = self._non_negative_int(team2_score, "Team 2 score")
        winner_id = None if team1_score == team2_score else (
            match["team1_id"] if team1_score > team2_score else match["team2_id"]
        )
        with self.connection:
            self.connection.execute(
                "INSERT INTO results (match_id, team1_score, team2_score, winner_id) VALUES (?, ?, ?, ?)",
                (match_id, team1_score, team2_score, winner_id),
            )
            self.connection.execute(
                "UPDATE matches SET status = 'Completed' WHERE match_id = ?", (match_id,)
            )

    def standings(self, tournament_id: Any) -> list[dict[str, Any]]:
        tournament = self.get_tournament(tournament_id)
        teams = self.list_teams(tournament["tournament_id"])
        table = {
            team["team_id"]: {
                "team_id": team["team_id"], "team": team["name"], "played": 0,
                "wins": 0, "draws": 0, "losses": 0, "for": 0, "against": 0, "points": 0,
            }
            for team in teams
        }
        matches = self.connection.execute(
            """SELECT m.team1_id, m.team2_id, r.team1_score, r.team2_score
               FROM matches m JOIN results r ON r.match_id = m.match_id
               WHERE m.tournament_id = ?""",
            (tournament["tournament_id"],),
        ).fetchall()
        for match in matches:
            first, second = table[match["team1_id"]], table[match["team2_id"]]
            score1, score2 = match["team1_score"], match["team2_score"]
            first["played"] += 1; second["played"] += 1
            first["for"] += score1; first["against"] += score2
            second["for"] += score2; second["against"] += score1
            if score1 == score2:
                first["draws"] += 1; second["draws"] += 1
                first["points"] += tournament["draw_points"]; second["points"] += tournament["draw_points"]
            elif score1 > score2:
                first["wins"] += 1; second["losses"] += 1; first["points"] += tournament["win_points"]; second["points"] += tournament["loss_points"]
            else:
                second["wins"] += 1; first["losses"] += 1; second["points"] += tournament["win_points"]; first["points"] += tournament["loss_points"]
        rows = list(table.values())
        for row in rows:
            row["difference"] = row["for"] - row["against"]
        return sorted(rows, key=lambda row: (-row["points"], -row["difference"], -row["for"], row["team"].lower()))

    def search(self, term: str, tournament_id: Any | None = None) -> dict[str, list[sqlite3.Row]]:
        term = self._required(term, "Search term")
        pattern = f"%{term}%"
        parameters: list[Any] = [pattern, pattern]
        tournament_clause = ""
        if tournament_id is not None:
            tournament = self.get_tournament(tournament_id)
            tournament_clause = " AND t.tournament_id = ?"
            parameters.append(tournament["tournament_id"])
        teams = self.connection.execute(
            """SELECT t.name, t.captain, u.name AS tournament_name FROM teams t
               JOIN tournaments u ON u.tournament_id = t.tournament_id
               WHERE (t.name LIKE ? OR t.captain LIKE ?)""" + tournament_clause,
            parameters,
        ).fetchall()
        player_parameters: list[Any] = [pattern, pattern]
        if tournament_id is not None:
            player_parameters.append(tournament["tournament_id"])
        players = self.connection.execute(
            """SELECT p.name, p.age, p.jersey_number, t.name AS team_name,
                      u.name AS tournament_name
               FROM players p JOIN teams t ON t.team_id = p.team_id
               JOIN tournaments u ON u.tournament_id = t.tournament_id
               WHERE (p.name LIKE ? OR t.name LIKE ?)""" + tournament_clause,
            player_parameters,
        ).fetchall()
        return {"teams": teams, "players": players}

    def statistics(self, tournament_id: Any) -> dict[str, int]:
        tournament = self.get_tournament(tournament_id)
        counts = self._one(
            """SELECT
               (SELECT COUNT(*) FROM teams WHERE tournament_id = ?) AS teams,
               (SELECT COUNT(*) FROM players p JOIN teams t ON t.team_id = p.team_id WHERE t.tournament_id = ?) AS players,
               (SELECT COUNT(*) FROM matches WHERE tournament_id = ?) AS matches,
               (SELECT COUNT(*) FROM matches WHERE tournament_id = ? AND status = 'Completed') AS completed,
               (SELECT COUNT(*) FROM matches WHERE tournament_id = ? AND status = 'Scheduled') AS upcoming,
               COALESCE((SELECT SUM(r.team1_score + r.team2_score) FROM results r JOIN matches m ON m.match_id = r.match_id WHERE m.tournament_id = ?), 0) AS total_score""",
            [tournament["tournament_id"]] * 6,
        )
        return dict(counts)


def print_rows(rows: Iterable[sqlite3.Row], columns: list[tuple[str, str]]) -> None:
    rows = list(rows)
    if not rows:
        print("No records found.")
        return
    print("\n" + " | ".join(title for _, title in columns))
    print("-" * (len(" | ".join(title for _, title in columns)) + 2))
    for row in rows:
        print(" | ".join(str(row[key]) if row[key] is not None else "-" for key, _ in columns))


def choose_tournament(manager: TournamentManager) -> sqlite3.Row | None:
    tournaments = manager.list_tournaments()
    print_rows(tournaments, [("tournament_id", "ID"), ("name", "Name"), ("sport", "Sport"), ("status", "Status")])
    if not tournaments:
        return None
    try:
        return manager.get_tournament(input("Tournament ID: "))
    except ValidationError as exc:
        print(f"Error: {exc}")
        return None


def prompt_int(label: str, default: int | None = None) -> int:
    while True:
        value = input(f"{label}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not value and default is not None:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a whole number.")


def create_tournament_cli(manager: TournamentManager) -> None:
    try:
        tournament_id = manager.create_tournament(
            input("Tournament name: "), input("Sport: "), input("Format [Round Robin]: ").strip() or "Round Robin",
            input("Start date (YYYY-MM-DD, optional): ").strip() or None,
            input("End date (YYYY-MM-DD, optional): ").strip() or None,
            input("Status [Upcoming]: ").strip() or "Upcoming",
        )
        print(f"Tournament created with ID {tournament_id}.")
    except ValidationError as exc:
        print(f"Error: {exc}")


def run_cli(manager: TournamentManager) -> None:
    print("\n=== TOURNAMENT MANAGER ===\n")
    while True:
        print("""\n1. List tournaments        2. Create tournament
3. Register team           4. Register player
5. List teams/players      6. Generate round-robin fixtures
7. List matches             8. Enter match result
9. View standings          10. Search
11. Statistics             0. Exit""")
        choice = input("\nChoose an option: ").strip()
        try:
            if choice == "0":
                print("Goodbye!")
                return
            if choice == "1":
                print_rows(manager.list_tournaments(), [("tournament_id", "ID"), ("name", "Name"), ("sport", "Sport"), ("format", "Format"), ("status", "Status")])
            elif choice == "2":
                create_tournament_cli(manager)
            elif choice == "3":
                tournament = choose_tournament(manager)
                if tournament:
                    print(f"Team ID: {manager.add_team(tournament['tournament_id'], input('Team name: '), input('Captain: '))}")
            elif choice == "4":
                print("Register the player under a team.")
                team_id = prompt_int("Team ID")
                print(f"Player ID: {manager.add_player(team_id, input('Player name: '), prompt_int('Age'), prompt_int('Jersey number'))}")
            elif choice == "5":
                tournament = choose_tournament(manager)
                if tournament:
                    print_rows(manager.list_teams(tournament["tournament_id"]), [("team_id", "ID"), ("name", "Team"), ("captain", "Captain")])
                    print_rows(manager.list_players(tournament_id=tournament["tournament_id"]), [("player_id", "ID"), ("name", "Player"), ("team_name", "Team"), ("age", "Age"), ("jersey_number", "Jersey")])
            elif choice == "6":
                tournament = choose_tournament(manager)
                if tournament:
                    print(f"Created {len(manager.generate_round_robin(tournament['tournament_id']))} fixtures.")
            elif choice == "7":
                tournament = choose_tournament(manager)
                if tournament:
                    print_rows(manager.list_matches(tournament["tournament_id"]), [("match_id", "ID"), ("round_number", "Round"), ("team1_name", "Team 1"), ("team2_name", "Team 2"), ("status", "Status"), ("team1_score", "Score 1"), ("team2_score", "Score 2")])
            elif choice == "8":
                match_id = prompt_int("Match ID")
                manager.record_result(match_id, prompt_int("Team 1 score"), prompt_int("Team 2 score"))
                print("Result saved.")
            elif choice == "9":
                tournament = choose_tournament(manager)
                if tournament:
                    rows = manager.standings(tournament["tournament_id"])
                    print_rows(rows, [("team", "Team"), ("played", "P"), ("wins", "W"), ("draws", "D"), ("losses", "L"), ("for", "For"), ("against", "Against"), ("difference", "Diff"), ("points", "Pts")])
            elif choice == "10":
                results = manager.search(input("Search term: "))
                print("Teams:"); print_rows(results["teams"], [("name", "Team"), ("captain", "Captain"), ("tournament_name", "Tournament")])
                print("Players:"); print_rows(results["players"], [("name", "Player"), ("team_name", "Team"), ("age", "Age"), ("jersey_number", "Jersey"), ("tournament_name", "Tournament")])
            elif choice == "11":
                tournament = choose_tournament(manager)
                if tournament:
                    print(manager.statistics(tournament["tournament_id"]))
            else:
                print("Please choose a valid menu option.")
        except ValidationError as exc:
            print(f"Error: {exc}")
        except sqlite3.Error as exc:
            print(f"Database error: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage tournaments, teams, fixtures, and results.")
    parser.add_argument("--db", default="tournament.db", help="SQLite database path (default: tournament.db)")
    args = parser.parse_args()
    manager = TournamentManager(args.db)
    try:
        run_cli(manager)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
    finally:
        manager.close()


if __name__ == "__main__":
    main()
