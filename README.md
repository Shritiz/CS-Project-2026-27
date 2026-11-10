# Tournament Manager — Team Handoff Guide

> **Audience:** project teammates who need to understand, run, debug, or extend the application without having worked on the original implementation.
>
> This document describes the current codebase as it exists, including the database schema, command-line flow, function responsibilities, data lifecycle, validation rules, known design inconsistencies, and the current seeded data.

---

## 1. What the project does

This is a Python command-line tournament management system backed by SQLite. It supports:

- Creating and listing tournaments
- Registering teams under tournaments
- Registering players under teams
- Generating round-robin fixtures
- Listing matches and their results
- Recording match scores
- Calculating standings
- Searching for teams and players
- Showing tournament statistics

The application is intentionally small: there is no web server, GUI, authentication, or separate API layer. The user interacts with a menu printed by `Program.py`, and all persistent data is stored in `tournament.db`.

---

## 2. Repository layout

```text
CS-Project-2026-27/
├── Program.py                 # Main application, schema, menu loop, fixture generation
├── Modules/
│   └── functions.py           # SQLite helpers, validation, queries, calculations, CLI helpers
├── tournament.db              # Persistent SQLite database
├── README.md                  # This handoff document
├── .gitignore
└── __pycache__/               # Generated Python bytecode; not source
```

### Important files

#### `Program.py`

Contains:

- The database schema string named `Schema`
- `generate_fixtures()`
- `run_cli()`
- `main()`

It imports the helper functions with:

```python
from Modules.functions import *
```

#### `Modules/functions.py`

Contains almost all business logic:

- Database initialization
- Validation errors
- CRUD-style database functions
- Queries for tournaments, teams, players, and matches
- Result recording
- Standings and statistics calculations
- Search
- Output formatting
- Interactive input helpers

#### `tournament.db`

This is the live data file. Running the program against it changes the database permanently whenever a create/register/result operation succeeds.

---

## 3. How to run the program

From the project directory:

```bash
python3 Program.py
```

The menu is:

```text
1. List tournaments        2. Create tournament
3. Register team           4. Register player
5. List teams/players      6. Generate round-robin fixtures
7. List matches             8. Enter match result
9. View standings          10. Search
11. Statistics             0. Exit
```

The program uses `tournament.db` relative to the current working directory. Run it from the project directory so it opens the intended database.

To make a backup before experimenting:

```bash
cp tournament.db tournament.db.backup
```

To inspect the database directly:

```bash
sqlite3 tournament.db
```

Useful SQLite commands:

```sql
.tables
.schema tournaments
.schema teams
.schema players
.schema matches
.schema results
.quit
```

---

## 4. Database schema and relationships

The schema is defined in `Program.py` in the `Schema` multi-line string. `init_database()` runs it with `CREATE TABLE IF NOT EXISTS`, so starting the program creates missing tables without deleting existing data.

The relationships are:

```text
tournaments 1 ──── many teams
teams       1 ──── many players
teams       1 ──── many matches as Teid1
teams       1 ──── many matches as Teid2
matches     1 ──── 0 or 1 result
```

Foreign keys use `ON DELETE CASCADE` for teams, players, matches, and results where defined. However, the current connection does not explicitly enable `PRAGMA foreign_keys = ON`, so SQLite's foreign-key enforcement depends on the connection configuration. This should be enabled in `init_database()` if strict referential integrity is required.

### 4.1 `tournaments`

| Column | Meaning |
|---|---|
| `Toid` | Auto-incrementing tournament ID; primary key |
| `name` | Tournament name; required and case-insensitively unique |
| `sport` | Sport name; required |
| `format` | Tournament format, usually `Round Robin` |
| `status` | `Scheduled`, `Ongoing`, or `Completed` |
| `Sdate` | Optional start date stored as text |
| `Edate` | Optional end date stored as text |

The application does not validate that dates are real `YYYY-MM-DD` dates. It stores whatever non-empty text the user enters.

### 4.2 `teams`

| Column | Meaning |
|---|---|
| `Teid` | Auto-incrementing team ID; primary key |
| `name` | Team name |
| `Toid` | Parent tournament ID |

`UNIQUE (Toid, name)` prevents the same team name from appearing twice in one tournament. The same team name may appear in different tournaments.

### 4.3 `players`

| Column | Meaning |
|---|---|
| `Pid` | Auto-incrementing player ID; primary key |
| `name` | Player name |
| `Teid` | Parent team ID |

There is no database-level uniqueness constraint on player names. Two players may have the same name, even on the same team. The helper function's error message says duplicate player names are checked, but the schema does not actually enforce that.

### 4.4 `matches`

| Column | Meaning |
|---|---|
| `Mid` | Auto-incrementing match ID; primary key |
| `Toid` | Tournament containing the match |
| `Teid1` | First team ID |
| `Teid2` | Second team ID |
| `Mdate` | Match date; required text |
| `Mtime` | Match time; required text |
| `Venue` | Optional venue |
| `Status` | `Scheduled`, `Completed`, or `Cancelled` |

The schema checks that `Teid1 <> Teid2`, but does not check that both teams belong to the same tournament. The application normally creates valid same-tournament fixtures, but direct SQL can create invalid cross-tournament matches unless additional validation is added.

### 4.5 `results`

| Column | Meaning |
|---|---|
| `Rid` | Auto-incrementing result ID; primary key |
| `Mid` | Match ID; unique, so a match can have at most one result |
| `Teid1_score` | Non-negative score for `Teid1` |
| `Teid2_score` | Non-negative score for `Teid2` |

A result does not store a winner column. The winner is derived from the two scores when standings are calculated.

---

## 5. Application startup and connection lifecycle

### `main()` — `Program.py`

`main()` performs the top-level lifecycle:

1. Sets `conn = None` so the `finally` block can safely inspect it.
2. Calls `init_database(Schema, "tournament.db")`.
3. Passes the returned connection to `run_cli(conn)`.
4. Converts `EOFError` and `KeyboardInterrupt` into a friendly `Goodbye!` message.
5. Closes the connection in `finally`.

The connection is now configured with `sqlite3.Row`, which is important because the rest of the project uses named access such as:

```python
row["Toid"]
row["name"]
```

Without the row factory, SQLite returns tuples and those accesses fail.

### `init_database(schema, database_path)`

Location: `Modules/functions.py`

Responsibilities:

1. Opens the SQLite file.
2. Sets `conn.row_factory = sqlite3.Row`.
3. Executes the schema script.
4. Commits schema creation.
5. Returns the connection to the caller.

The return statement is essential. If it is omitted, `main()` receives `None`, and every database operation fails with an error like:

```text
AttributeError: 'NoneType' object has no attribute 'execute'
```

### `close_database(conn)`

Closes a connection if one was supplied. The main program currently closes the connection directly in `main()` instead of calling this helper.

### `get_connection(database_path)`

Returns a basic SQLite connection. It does not set the row factory, so callers using this function would receive tuple rows. It is currently not part of the main execution path.

---

## 6. Validation and error handling

### `ValidationError`

A project-specific exception used for user-correctable input and business-rule problems. The CLI catches it and prints:

```text
Error: <message>
```

Examples:

- Empty tournament name
- Invalid tournament ID
- Missing team
- Negative score
- Duplicate team
- Attempting to record a second result

### `isRequired(conn, value, label)`

Converts a value to text, strips whitespace, and rejects an empty value. It returns the stripped value.

Despite receiving `conn`, it does not use the connection. The parameter remains for compatibility with the current function signatures.

### `prompt_int(label, default=None)`

Used by the interactive CLI when an integer is needed. It repeatedly prompts until the user enters a value accepted by Python's `int()`.

Important distinction:

- `prompt_int()` handles invalid integer input before the business function receives it.
- `rec_r()` still performs its own score conversion because the function can also be called directly.

### Error handling in `run_cli()`

The menu loop catches:

1. `ValidationError` — printed as a normal user-facing error.
2. `sqlite3.IntegrityError` — printed as a database error.
3. Other `sqlite3.Error` exceptions — also printed as database errors.

Unexpected Python errors are not caught. That is useful during development because real programming bugs produce a traceback instead of being silently hidden.

---

## 7. Function-by-function guide

## `Program.py`

### `generate_fixtures(conn, tournament_id)`

Generates one round-robin fixture for every pair of teams in a tournament.

Flow:

1. Calls `get_To()` to validate and load the tournament.
2. Calls `lst_Te()` to load its teams.
3. Rejects tournaments with fewer than two teams.
4. Rejects generation if any match already exists for the tournament.
5. Adds a `None` placeholder when the number of teams is odd, creating a bye.
6. Rotates the participants after each round.
7. Inserts scheduled matches using the current date and time from SQLite.
8. Commits the transaction.
9. Returns the created match IDs.

For `n` teams, a single round-robin should create:

```text
n * (n - 1) / 2
```

matches. For four teams, that is six matches. For three teams, it is three matches, with one bye in each round.

The function does not store a round number, despite internally using `round_number` in the loop. It also leaves venue as `NULL`.

### `run_cli(conn)`

The main interactive controller. It repeatedly:

1. Prints the menu.
2. Reads the selected option.
3. Calls the appropriate helper.
4. Prints results or errors.
5. Continues until option `0` is selected or input ends.

The option-to-function mapping is:

| Option | Main calls |
|---:|---|
| 0 | Return from the loop |
| 1 | `lst_To()`, `print_rows()` |
| 2 | `create_tournament_cli()` |
| 3 | `choose_tournament()`, `add_Te()` |
| 4 | `prompt_int()`, `add_P()` |
| 5 | `choose_tournament()`, `lst_Te()`, `lst_P()`, `print_rows()` |
| 6 | `choose_tournament()`, `generate_fixtures()` |
| 7 | `choose_tournament()`, `lst_M()`, `print_rows()` |
| 8 | `prompt_int()`, `rec_r()` |
| 9 | `choose_tournament()`, `standings()`, `print_rows()` |
| 10 | `search()`, `print_rows()` |
| 11 | `choose_tournament()`, `statistics()` |

### `main()`

Described in the startup section above. It owns database startup, CLI execution, shutdown, and connection cleanup.

---

## `Modules/functions.py`

### `Create_To(conn, name, sport, format, status, Sdate, Edate)`

Creates a tournament.

Steps:

1. Validates `name`, `sport`, and `format` with `isRequired()`.
2. Validates status against `Scheduled`, `Ongoing`, and `Completed`.
3. Converts empty dates to `NULL`.
4. Inserts the row.
5. Commits on success.
6. Rolls back and raises `ValidationError` on an integrity failure.
7. Returns the new tournament ID.

The function does not validate date format or ensure that the end date comes after the start date.

### `get_To(conn, Toid)`

Loads one tournament by ID.

Steps:

1. Requires a non-empty value.
2. Converts it to an integer.
3. Requires a positive ID.
4. Queries `tournaments`.
5. Raises `ValidationError` if no matching tournament exists.
6. Returns a `sqlite3.Row`.

This is the standard gateway used by other functions before they operate on a tournament.

### `add_Te(conn, name, Toid)`

Registers a team under a tournament.

Steps:

1. Loads and validates the tournament with `get_To()`.
2. Requires a non-empty team name.
3. Inserts the supplied team name and the validated tournament ID.
4. Commits.
5. Converts duplicate-team database errors into `ValidationError`.
6. Returns the new team ID.

`Program.py` still contains an old workaround that updates the team name after calling `add_Te()`. Since `add_Te()` now inserts the correct name itself, that update is redundant and can be removed later.

### `add_P(conn, name, Teid)`

Registers a player under a team.

Steps:

1. Requires and converts the team ID to an integer.
2. Requires a positive team ID.
3. Checks that the team exists.
4. Requires a non-empty player name.
5. Inserts the player.
6. Commits.
7. Returns the new player ID.

There is no age, jersey number, captain, or position field in the current schema.

### `lst_To(conn)`

Returns all tournaments ordered by `Toid`.

### `lst_Te(conn, Toid)`

Validates the tournament and returns its teams ordered alphabetically by team name.

### `lst_P(conn, Teid, Toid)`

Returns players with their team name.

Filtering behavior:

- If `Teid` is not `None`, it filters by one team.
- Otherwise, if `Toid` is not `None`, it filters by all teams in one tournament.
- Results are ordered alphabetically by player name.

The CLI uses the tournament form when option 5 is selected.

### `lst_M(conn, Toid, status)`

Returns matches for one tournament, joining team names and optional result scores.

Important details:

- Uses `LEFT JOIN results`, so scheduled matches with no result are displayed.
- Returns `NULL` scores for matches that have not been completed.
- Aliases team names as `team1_name` and `team2_name`, matching the columns expected by `Program.py`.
- Accepts optional match status filtering.
- Orders by date and time.

### `gen_round_robin(conn, Toid)`

This is a second fixture-generation implementation in `Modules/functions.py`. It is currently not called by `Program.py`; the active path is `Program.generate_fixtures()`.

It creates every pair using nested loops and does not implement the rotation/bye algorithm. It should be removed or consolidated to avoid two competing implementations.

### `rec_r(conn, Mid, t1_score, t2_score)`

Records one match result.

Steps:

1. Validates and converts the match ID.
2. Loads the match.
3. Rejects a missing match.
4. Rejects a match already marked `Completed`.
5. Requires both scores.
6. Converts both scores to integers.
7. Rejects negative scores.
8. Inserts a result using `Teid1_score` and `Teid2_score`.
9. Marks the match `Completed`.
10. Commits both operations as one transaction via `with conn:`.

The winner is not stored. Standings determine winner/draw/loss from the scores.

### `standings(conn, Toid)`

Calculates the table for a tournament from completed results.

Initialization:

Each registered team starts with:

```text
played = 0
wins = 0
draws = 0
losses = 0
for = 0
against = 0
points = 0
```

Processing each result:

- Both teams gain one `played` count.
- Each team's `for` is increased by its score.
- Each team's `against` is increased by the opponent's score.
- A draw gives both teams one point.
- A win gives the winner three points and the loser zero.

Then:

```text
difference = for - against
```

Sorting order is:

1. More points first
2. Better goal/score difference first
3. More scores for first
4. Alphabetical team name as the final tie-breaker

The points system is hard-coded as 3 for a win and 1 for a draw. It is not configurable per tournament.

### `search(conn, term, Toid=None)`

Searches team and player data using SQL `LIKE` patterns.

For teams, it searches team names.

For players, it searches:

- Player names
- Team names

When a tournament ID is supplied, both queries are restricted to that tournament. The CLI currently calls it without a tournament filter, so option 10 searches the entire database.

The search pattern is:

```python
pattern = f"%{term}%"
```

SQLite's default `LIKE` behavior is generally case-insensitive for ASCII text.

### `statistics(conn, Toid)`

Returns a dictionary containing:

```python
{
    "teams": number of teams,
    "players": number of players,
    "matches": total matches,
    "completed": matches with Status = 'Completed',
    "upcoming": matches with Status = 'Scheduled',
    "total_score": sum of both teams' scores in completed matches,
}
```

The function performs these calculations in one SQL query using scalar subqueries. It returns `dict(row)` so the CLI prints a normal Python dictionary.

Cancelled matches are counted in `matches` but not in `completed` or `upcoming`.

### `print_rows(rows, columns)`

Generic table formatter.

`columns` is a list of `(database_key, heading)` pairs. For each row it:

1. Materializes the iterable into a list.
2. Prints `No records found.` if empty.
3. Prints headings.
4. Prints a separator.
5. Prints each selected value.
6. Displays `-` for `NULL` values.

This function expects rows to support named keys, which is why `sqlite3.Row` is configured during initialization.

### `choose_tournament(conn)`

Reusable interactive selector.

1. Lists all tournaments.
2. Returns `None` if no tournaments exist.
3. Prompts for a tournament ID.
4. Uses `get_To()` to validate the selection.
5. Prints a validation error and returns `None` for an invalid selection.

### `prompt_int(label, default=None)`

Repeatedly prompts until a whole number is entered. It is used for IDs and scores in the CLI.

The current implementation accepts values such as `-1` because they are valid integers. Business functions are responsible for rejecting negative IDs or scores where appropriate.

### `create_tournament_cli(conn)`

Collects tournament fields interactively and delegates insertion to `Create_To()`.

Empty format defaults to `Round Robin`.

Empty status defaults to `Scheduled`.

Empty start/end dates are stored as `NULL`.

---

## 8. Complete data flow examples

## 8.1 Creating a tournament

```text
User selects 2
    ↓
run_cli()
    ↓
create_tournament_cli()
    ↓
collect name, sport, format, status, dates
    ↓
Create_To()
    ↓
validate fields
    ↓
INSERT INTO tournaments
    ↓
commit
    ↓
print new tournament ID
```

## 8.2 Registering a team

```text
User selects 3
    ↓
choose_tournament()
    ↓
get_To()
    ↓
read team name
    ↓
add_Te()
    ↓
validate tournament and name
    ↓
INSERT INTO teams
    ↓
commit
    ↓
print team ID
```

## 8.3 Registering a player

```text
User selects 4
    ↓
read team ID
    ↓
read player name
    ↓
add_P()
    ↓
validate team ID and existence
    ↓
INSERT INTO players
    ↓
commit
    ↓
print player ID
```

## 8.4 Generating fixtures

```text
User selects 6
    ↓
choose_tournament()
    ↓
generate_fixtures()
    ↓
load tournament teams
    ↓
reject fewer than two teams
    ↓
reject if matches already exist
    ↓
create every pair of teams
    ↓
INSERT scheduled matches
    ↓
commit
    ↓
print number created
```

## 8.5 Recording a result

```text
User selects 8
    ↓
read match ID and two scores
    ↓
rec_r()
    ↓
validate match
    ↓
reject already completed match
    ↓
convert and validate scores
    ↓
INSERT results row
    ↓
UPDATE match Status = 'Completed'
    ↓
commit
    ↓
print Result saved.
```

## 8.6 Calculating standings

```text
User selects 9
    ↓
choose_tournament()
    ↓
standings()
    ↓
load all teams with zeroed counters
    ↓
load all results for tournament
    ↓
apply win/draw/loss scoring
    ↓
calculate score difference
    ↓
sort table
    ↓
print rows
```

---

## 9. Current seeded database

The database currently contains the original test records plus a realistic seeded competition.

### Overall counts

At the time this document was written:

- Tournaments: 5
- Teams: 10
- Players: 20
- Matches: 8
- Results: 5

### Seeded tournament

**National University Football Cup 2026**

- Tournament ID: 5
- Sport: Football
- Format: Round Robin
- Status: Ongoing
- Start date: 2026-11-01
- End date: 2026-11-30

Teams:

- North Stars — 4 players
- Riverside FC — 4 players
- City United — 4 players
- Eastside Athletic — 4 players

Completed matches:

```text
North Stars       2 - 1 Riverside FC
City United       0 - 0 Eastside Athletic
North Stars       1 - 3 City United
Riverside FC      2 - 2 Eastside Athletic
```

Scheduled matches:

```text
North Stars       vs Eastside Athletic
Riverside FC      vs City United
```

Current statistics for tournament ID 5:

```text
teams:       4
players:     16
matches:     6
completed:   4
upcoming:    2
total_score: 11
```

Current standings:

| Team | Played | Wins | Draws | Losses | For | Against | Difference | Points |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| City United | 2 | 1 | 1 | 0 | 3 | 1 | 2 | 4 |
| North Stars | 2 | 1 | 0 | 1 | 3 | 4 | -1 | 3 |
| Eastside Athletic | 2 | 0 | 2 | 0 | 2 | 2 | 0 | 2 |
| Riverside FC | 2 | 0 | 1 | 1 | 3 | 4 | -1 | 1 |

---

## 10. Important current limitations and technical debt

These are not theoretical concerns; they are areas a teammate should understand before extending the project.

### 10.1 Schema and logic are embedded in the wrong layer

The schema is defined in `Program.py`, while `Modules/functions.py` imports `Schema` from `Program.py`. This creates a fragile circular-import relationship.

A cleaner design would move the schema to a dedicated module, for example:

```text
Modules/schema.py
```

Then both files could import it without importing the executable entrypoint.

### 10.2 Duplicate fixture-generation functions

There are two implementations:

- `Program.generate_fixtures()` — active implementation
- `Modules.functions.gen_round_robin()` — legacy/unused implementation

Keep one implementation to prevent future behavior from diverging.

### 10.3 No explicit foreign-key enforcement

Add this during initialization if database-level relationship enforcement is wanted:

```python
conn.execute("PRAGMA foreign_keys = ON")
```

### 10.4 Dates and times are plain text

The program stores date and time strings but does not validate them. A future improvement should validate ISO dates and times before insertion.

### 10.5 No round number in the match table

The fixture algorithm has rounds, but the schema does not store a round field. This makes it impossible to display or query round numbers later.

### 10.6 No team-membership validation for manually inserted matches

The database ensures that team IDs exist, but not that both teams belong to the selected tournament. The application-generated fixtures are correct, but direct SQL can violate the business rule.

### 10.7 Tournament status is not automatically updated

Recording results does not change the tournament status. A tournament remains whatever status was manually entered during creation.

### 10.8 Points are hard-coded

Standings always use:

- Win: 3 points
- Draw: 1 point
- Loss: 0 points

If different sports or competitions need different scoring, the schema and calculation function need to be extended.

### 10.9 Player model is minimal

Players only have a name and team ID. There is no age, jersey number, position, captain flag, or transfer history.

### 10.10 CLI and business logic are mixed

Several functions both collect input and perform database operations. This is convenient for a small assignment but makes automated testing harder. A future refactor should keep input/output in the CLI layer and make business functions accept already-validated values.

### 10.11 The team-name update in `Program.py` is obsolete

Option 3 currently calls `add_Te()` and then updates the same row's name. Since `add_Te()` now stores the correct name, the update block is redundant:

```python
conn.execute("UPDATE teams SET name = ? WHERE Teid = ?", (team_name, team_id))
```

It is safe to remove after confirming no old database compatibility requirement depends on it.

### 10.12 No automated tests

The project currently relies on interactive testing. At minimum, add tests for:

- Empty and duplicate tournament names
- Team and player registration
- Fixture counts for 2, 3, and 4 teams
- Duplicate fixture generation
- Result validation
- Standings for wins, draws, and losses
- Search behavior
- Statistics counts

Use a temporary SQLite database for automated tests so the seeded `tournament.db` is not changed.

---

## 11. Suggested development workflow

Before changing code:

```bash
cp tournament.db tournament.db.backup
```

After changing code, run a basic smoke test:

```bash
printf '1\n0\n' | python3 Program.py
```

For a complete manual flow:

1. List tournaments.
2. Create a new tournament.
3. Add at least two teams.
4. Add players to each team.
5. Generate fixtures.
6. List matches.
7. Record a win, draw, or loss.
8. View standings.
9. Search for a team and player.
10. View statistics.
11. Try invalid IDs and negative scores.
12. Confirm the database counts with SQLite.

Useful direct checks:

```sql
SELECT * FROM tournaments;
SELECT * FROM teams;
SELECT * FROM players;
SELECT * FROM matches;
SELECT * FROM results;
```

When debugging a failed query, inspect the actual schema first:

```sql
.schema matches
.schema results
```

The column names are case-insensitive in SQLite, but spelling and table relationships still matter. For example, the result score columns are `Teid1_score` and `Teid2_score`, not `t1_score` and `t2_score`.

---

## 12. Recommended next improvements

If the team continues development, prioritize these changes:

1. Move `Schema` out of `Program.py` to remove the circular import.
2. Consolidate the two fixture-generation functions.
3. Remove the obsolete team-name update in `Program.py`.
4. Enable foreign keys explicitly.
5. Add a `round_number` column to matches.
6. Validate dates and times.
7. Add tournament-specific point rules.
8. Separate CLI input from business/database logic.
9. Add automated tests using temporary databases.
10. Add a migration strategy before changing the existing schema.

---

## 13. Quick reference: expected database flow

```text
Tournament
   │
   ├── Teams
   │      │
   │      └── Players
   │
   └── Matches
          │
          └── Results

Create tournament
    → register teams
    → register players
    → generate fixtures
    → record results
    → calculate standings/statistics
    → search and display reports
```

The central rule is that tournaments own teams, teams own players, and matches belong to tournaments while referencing two teams. Results belong to matches and are the source used to calculate standings and score totals.
