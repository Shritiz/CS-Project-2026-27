import sqlite3
from pathlib  import Path 
from typing import Any, Iterable
from Modules.functions import *

#Schema for initial setup of the database
Schema = """ 
CREATE TABLE IF NOT EXISTS tournaments (
    Toid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sport TEXT NOT NULL,
    format TEXT NOT NULL,
    status TEXT CHECK(status IN ('Scheduled', 'Ongoing', 'Completed')) NOT NULL DEFAULT 'Scheduled',
    Sdate DATE,
    Edate DATE
);


CREATE TABLE IF NOT EXISTS teams (
    Teid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    Toid INTEGER,
    FOREIGN KEY (Toid) REFERENCES tournaments (Toid)
);

CREATE TABLE IF NOT EXISTS players (
    Pid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    Teid INTEGER,
    FOREIGN KEY (Teid) REFERENCES teams (Teid)
);

CREATE TABLE IF NOT EXISTS matches (
    Mid INTEGER PRIMARY KEY AUTOINCREMENT,
    Toid INTEGER NOT NULL,
    Teid1 INTEGER NOT NULL,
    Teid2 INTEGER NOT NULL,
    Mdate DATE NOT NULL,
    Mtime TIME NOT NULL,
    Venue TEXT,
    Status TEXT CHECK(Status IN ('Scheduled', 'Completed', 'Cancelled')) NOT NULL DEFAULT 'Scheduled',
    FOREIGN KEY (Toid) REFERENCES tournaments (Toid),
    FOREIGN KEY (Teid1) REFERENCES teams (Teid),
    FOREIGN KEY (Teid2) REFERENCES teams (Teid)
);


CREATE TABLE IF NOT EXISTS results (
    Rid INTEGER PRIMARY KEY AUTOINCREMENT,
    Mid INTEGER NOT NULL,
    Teid1_score INTEGER NOT NULL,
    Teid2_score INTEGER NOT NULL,
    FOREIGN KEY (Mid) REFERENCES matches (Mid)
);

CREATE INDEX IF NOT EXISTS idx_To_id ON tournaments (Toid);
CREATE INDEX IF NOT EXISTS idx_Te_id ON teams (Teid);
CREATE INDEX IF NOT EXISTS idx_P_id ON players (Pid);
CREATE INDEX IF NOT EXISTS idx_TO_id ON matches (Toid, status);
"""

def main():
    pass
    #manager = DatabaseManager("tournament.db")

if __name__ == "__main__":
    main()