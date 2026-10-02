# CS-Project-2026-27
Project Using pyton, SQL,  python connections and other ot make a project 


# 🏆 Tournament Manager

A Python + SQLite based tournament management system designed to organize, manage, and track competitive tournaments from a single application.

The system allows an administrator to create tournaments, register players and teams, schedule matches, record results, automatically calculate standings, and generate tournament statistics.

The project is designed as a **Class 12 Computer Science final project** using Python for the application logic and SQLite for persistent database storage.

---

## 📌 Project Overview

Managing a tournament manually can become difficult as the number of teams, players, and matches increases.

Tournament Manager solves this problem by providing a centralized system where tournament-related information can be stored and managed efficiently.

Instead of maintaining separate lists for players, teams, fixtures, and results, the application stores all information in a relational SQLite database.

The system can be used for tournaments such as:

- ⚽ Football
- 🏏 Cricket
- 🏀 Basketball
- 🎮 Esports
- 🎾 Tennis
- ♟️ Chess
- 🏸 Badminton
- Or any other competitive tournament

The application is designed to be flexible enough that the same system can manage different types of tournaments.

---

# 🎯 Objectives

The main objectives of Tournament Manager are:

1. Store tournament information digitally.
2. Register and manage players and teams.
3. Generate and manage tournament fixtures.
4. Record match results.
5. Automatically calculate team/player standings.
6. Track wins, losses, draws, and points.
7. Search and filter tournament information.
8. Provide useful tournament statistics.
9. Reduce manual calculation and record keeping.
10. Demonstrate practical use of Python with SQL databases.

---

# 🛠️ Technologies Used

## Programming Language

**Python 3**

Python is used for:

- Application logic
- User input
- Menu system
- Database operations
- Calculations
- Validation
- Tournament logic
- Reports and statistics

## Database

**SQLite**

The project uses Python's built-in `sqlite3` module.

Database connection:

```python
import sqlite3

con = sqlite3.connect("tournament.db")
cur = con.cursor()
```

SQLite is used because it provides persistent data storage without requiring a separate database server.

---

# 🗄️ Database Structure

The project uses multiple related tables rather than storing everything in a single table.

A possible database structure is:

```text
TOURNAMENT
    │
    ├── TEAMS
    │     │
    │     └── PLAYERS
    │
    └── MATCHES
          │
          └── RESULTS
```

---

# 📊 Main Database Tables

## 1. Tournament Table

Stores information about each tournament.

Example fields:

```text
tournament_id
name
sport
format
start_date
end_date
status
```

Example:

```text
1 | Inter School Football Cup | Football | Knockout | 2026-10-10 | 2026-10-15 | Active
```

---

## 2. Team Table

Stores participating teams.

```text
team_id
tournament_id
team_name
captain
```

Example:

```text
1 | 1 | Thunder FC | Rahul
2 | 1 | United XI  | Arjun
3 | 1 | Warriors   | Aman
```

---

## 3. Player Table

Stores players belonging to teams.

```text
player_id
team_id
player_name
age
jersey_number
```

This allows one team to contain multiple players.

---

## 4. Match Table

Stores scheduled matches.

```text
match_id
tournament_id
round
team1_id
team2_id
match_date
match_time
venue
status
```

Example:

```text
101 | 1 | Semi Final | 1 | 3 | 2026-10-14 | 16:00 | Main Ground | Scheduled
```

---

## 5. Result Table

Stores the result of completed matches.

```text
result_id
match_id
team1_score
team2_score
winner_id
```

For example:

```text
101 | 7 | 3 | 1
```

This means Team 1 defeated Team 3 with a score of 7–3.

---

# ⚙️ Core Features

## 🏆 1. Tournament Creation

The administrator can create a new tournament.

Information such as:

- Tournament name
- Sport
- Tournament format
- Start date
- End date

can be entered.

Supported formats can include:

- League
- Knockout
- Round Robin
- Group Stage

---

# 👥 2. Team Registration

Teams can be registered for a tournament.

The system checks for duplicate team names and prevents invalid registrations.

Example:

```text
Team Name: Thunder FC
Captain: Rahul
Tournament: Inter School Cup

Team registered successfully!
```

---

# 👤 3. Player Registration

Players can be assigned to teams.

Information stored can include:

- Player name
- Age
- Jersey number
- Team

The system can also prevent duplicate jersey numbers within the same team.

---

# 📅 4. Fixture Generation

One of the major features of the project is automatic fixture generation.

Instead of manually entering every match, the program can generate fixtures based on the tournament format.

For example:

### Round Robin

For four teams:

```text
Round 1
Team A vs Team B
Team C vs Team D

Round 2
Team A vs Team C
Team B vs Team D

Round 3
Team A vs Team D
Team B vs Team C
```

The generated fixtures are then stored in the SQLite database.

---

# 🥇 5. Knockout Tournament

The system can also support knockout tournaments.

Example:

```text
Quarter Final

Team A ─────┐
            ├── Team A
Team B ─────┘

Team C ─────┐
            ├── Team D
Team D ─────┘
```

The winner of each match progresses to the next round.

The system can automatically create the next round after results are entered.

---

# 📝 6. Match Result Entry

After a match has been completed, the administrator can enter the result.

Example:

```text
Match: Thunder FC vs United XI

Thunder FC Score: 3
United XI Score: 1

Winner: Thunder FC
```

The result is stored in the database.

---

# 📈 7. Automatic Points Table

For league or round-robin tournaments, the system can automatically calculate standings.

Example:

```text
------------------------------------------------
Team           P     W     D     L     Pts
------------------------------------------------
Thunder FC     5     4     1     0      13
United XI      5     3     1     1      10
Warriors       5     2     0     3       6
Titans         5     0     0     5       0
------------------------------------------------
```

The points system can be configured according to the tournament.

For example:

```text
Win  = 3 points
Draw = 1 point
Loss = 0 points
```

The program calculates these values automatically from stored match results.

---

# 📊 8. Tournament Statistics

The system can generate statistics from the stored database.

Examples include:

### Team Statistics

```text
Matches Played
Wins
Losses
Draws
Points
Goals/Runs/Score For
Goals/Runs/Score Against
```

### Tournament Statistics

```text
Total Teams
Total Players
Total Matches
Completed Matches
Upcoming Matches
Total Scores
```

---

# 🔍 9. Search System

The administrator can search for information without manually going through the database.

Possible searches:

```text
Search Team
Search Player
Search Tournament
Search Match
Search Completed Matches
Search Upcoming Matches
```

Example:

```text
Enter player name: Rahul

Player Found

Name: Rahul Sharma
Team: Thunder FC
Jersey Number: 10
```

---

# 📅 10. Upcoming Matches

The system can display matches that have not yet been completed.

Example:

```text
UPCOMING MATCHES

Match 12
Thunder FC vs Warriors
Date: 14 October 2026
Time: 4:00 PM
Venue: Main Ground

Match 13
United XI vs Titans
Date: 15 October 2026
Time: 4:00 PM
Venue: Main Ground
```

---

# 🏁 11. Tournament Status

Each tournament can have a status such as:

```text
Upcoming
Active
Completed
Cancelled
```

The status can be updated as the tournament progresses.

---

# 🏅 12. Tournament Winner

Once the tournament is completed, the system can determine and display the winner.

Example:

```text
================================
        TOURNAMENT COMPLETE
================================

Tournament:
Inter School Football Cup

Winner:
🏆 Thunder FC

Final Score:
Thunder FC 3 - 1 United XI

Congratulations!
================================
```

---

# 📋 13. Tournament Dashboard

The main menu can provide a simple dashboard.

Example:

```text
========================================
          TOURNAMENT MANAGER
========================================

Active Tournament:
Inter School Football Cup

Teams: 8
Players: 96
Matches: 28

Completed Matches: 19
Upcoming Matches: 9

========================================

1. Manage Tournaments
2. Manage Teams
3. Manage Players
4. Manage Matches
5. Enter Match Result
6. View Points Table
7. Search
8. Statistics
9. Exit

========================================
```

---

# 🧠 Special Features

The project will contain several features that make it more than a basic CRUD database application.

## ⭐ Automatic Fixture Generation

The program can automatically create matches instead of requiring every match to be entered manually.

---

## ⭐ Automatic Standings

The points table is calculated from actual match results stored in the database.

There is no need to manually enter points.

---

## ⭐ Automatic Winner Detection

The system can determine the tournament winner based on the tournament format and recorded results.

---

## ⭐ Relational Database

Instead of one large table, information is divided into related tables.

For example:

```text
Tournament
     ↓
Teams
     ↓
Players
```

and:

```text
Tournament
     ↓
Matches
     ↓
Results
```

This demonstrates the practical use of relational databases.

---

## ⭐ Data Validation

The program will validate user input.

Examples:

- Prevent duplicate team names.
- Prevent invalid team IDs.
- Prevent duplicate player registrations.
- Prevent invalid scores.
- Prevent entering a result twice.
- Prevent teams from playing themselves.
- Prevent scheduling invalid matches.
- Prevent registering players to non-existent teams.

---

## ⭐ Search & Filtering

Information can be searched using different criteria.

For example:

```text
Show all teams in a tournament
Show all matches for a team
Show all players in a team
Show completed matches
Show upcoming matches
Show teams with more than 10 points
```

---

## ⭐ Database Reports

The system can generate reports using SQL queries.

Examples:

```sql
SELECT * FROM teams;

SELECT * FROM matches
WHERE status = 'Scheduled';

SELECT team_id, COUNT(*)
FROM players
GROUP BY team_id;
```

More advanced queries can use:

```text
WHERE
ORDER BY
GROUP BY
COUNT()
SUM()
AVG()
JOIN
```

---

# 🔗 SQL Concepts Demonstrated

The project will demonstrate important SQL concepts expected at the Class 12 level.

### CREATE

Creating database tables.

```sql
CREATE TABLE teams (...);
```

### INSERT

Adding records.

```sql
INSERT INTO teams VALUES (...);
```

### SELECT

Retrieving records.

```sql
SELECT * FROM teams;
```

### UPDATE

Updating information.

```sql
UPDATE matches
SET status = 'Completed'
WHERE match_id = 101;
```

### DELETE

Removing records.

```sql
DELETE FROM players
WHERE player_id = 10;
```

### WHERE

Filtering records.

### ORDER BY

Sorting records.

### GROUP BY

Generating statistics.

### JOIN

Combining information from related tables.

---

# 🐍 Python Concepts Demonstrated

The project will also demonstrate Python programming concepts including:

- Variables
- Data types
- Input/output
- Conditional statements
- Loops
- Functions
- Lists
- Tuples
- Dictionaries where required
- Exception handling
- Input validation
- Modular programming
- SQL integration
- Database connectivity

---

# 🔌 Python–SQLite Integration

The database will be connected using Python's `sqlite3` module.

Basic structure:

```python
import sqlite3

con = sqlite3.connect("tournament.db")
cur = con.cursor()
```

Queries will be executed through Python:

```python
cur.execute(
    "SELECT * FROM teams"
)

records = cur.fetchall()

for record in records:
    print(record)
```

Changes will be saved using:

```python
con.commit()
```

And the connection will be closed using:

```python
con.close()
```

---

# 🛡️ Error Handling

The system will handle common errors without crashing.

For example:

```text
Invalid team ID.
Please enter a valid team ID.

OR

This team already exists.

OR

This match has already been completed.
```

Database errors can also be handled using Python exception handling.

```python
try:
    # database operation
except sqlite3.Error as e:
    print("Database error:", e)
```

---

# 📁 Proposed Project Structure

```text
TournamentManager/
│
├── main.py
├── database.py
├── tournament.py
├── team.py
├── player.py
├── match.py
├── statistics.py
│
├── tournament.db
│
├── README.md
└── requirements.txt
```

For a simpler Class 12 implementation, the project can also be kept in fewer files:

```text
TournamentManager/
│
├── main.py
├── tournament.db
└── README.md
```

The exact structure can be chosen based on project complexity.

---

# 🔄 Example Workflow

A typical tournament could be managed like this:

```text
1. Create Tournament
        ↓
2. Register Teams
        ↓
3. Register Players
        ↓
4. Generate Fixtures
        ↓
5. Play Matches
        ↓
6. Enter Results
        ↓
7. Update Standings
        ↓
8. Generate Next Round
        ↓
9. Complete Tournament
        ↓
10. Declare Winner
```

---

# 💡 Example Tournament

Suppose we create:

```text
Tournament:
CBSE Inter-School Football Cup

Teams:
1. Thunder FC
2. United XI
3. Warriors
4. Titans
```

The system generates:

```text
MATCH 1
Thunder FC vs United XI

MATCH 2
Warriors vs Titans

MATCH 3
Thunder FC vs Warriors

MATCH 4
United XI vs Titans
```

After entering results, the system automatically updates the standings.

The user does **not** need to manually calculate the points.

---

# 🎓 Educational Value

This project demonstrates how a real-world problem can be converted into a computerized information-management system.

It combines:

```text
Python
   +
Database
   +
SQL
   +
Problem Solving
   +
Data Management
```

The project provides practical experience with database design, SQL queries, Python programming, validation, and application development.

---

# 🚀 Future Improvements

Although the current project focuses on Python and SQLite, the system could later be expanded with:

- Graphical User Interface
- Web interface
- Login system
- Admin/user roles
- Online tournament registration
- Live score updates
- Player statistics
- Automated bracket visualization
- Exporting reports to PDF
- Cloud database
- Online multiplayer tournament management

These features are outside the scope of the current Class 12 project but demonstrate how the application could be developed further.

---

# 📌 Project Scope

The primary goal of this project is to create a reliable, database-driven tournament management system using concepts covered in the Class 12 Computer Science curriculum.

The project intentionally focuses on:

```text
Python
SQLite
SQL Queries
Functions
Database Management
Data Validation
Reports
```

rather than relying on external frameworks or complicated technologies.

---

# 👨‍💻 Project Type

**Class 12 Computer Science Final Project**

**Language:** Python 3  
**Database:** SQLite  
**Database Module:** `sqlite3`  
**Interface:** Command Line Interface (CLI)

---

# 🏆 Conclusion

Tournament Manager provides a complete solution for organizing and managing tournaments.

It replaces manual tournament records with a structured digital system capable of managing tournaments, teams, players, matches, results, standings, and statistics.

The project demonstrates how Python can be integrated with an SQL database to create a practical real-world application while applying the programming and database concepts learned in Class 12 Computer Science.