import sqlite3
from pathlib  import Path 
from typing import Any, Iterable
from Modules.functions import *

#Schema for initial setup of the database
Schema = """ 
CREATE TABLE IF NOT EXISTS tournaments (
    Toid INTEGER PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL,
    sport TEXT NOT NULL,
    format TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Scheduled'
        CHECK(status IN ('Scheduled', 'Ongoing', 'Completed')),
    Sdate DATE,
    Edate DATE
);


CREATE TABLE IF NOT EXISTS teams (
    Teid INTEGER PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL,
    Toid INTEGER,
    FOREIGN KEY (Toid) REFERENCES tournaments (Toid)
);

CREATE TABLE IF NOT EXISTS players (
    Pid INTEGER PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL,
    Teid INTEGER,
    FOREIGN KEY (Teid) REFERENCES teams (Teid)
);

CREATE TABLE IF NOT EXISTS matches (
    Mid INTEGER PRIMARY KEY AUTO_INCREMENT,
    Toid INTEGER NOT NULL,
    Teid1 INTEGER NOT NULL,
    Teid2 INTEGER NOT NULL,
    Mdate DATE NOT NULL,
    Mtime TIME NOT NULL,
    Venue TEXT,
    Status VARCHAR(20) CHECK(Status IN ('Scheduled', 'Completed', 'Cancelled')) NOT NULL DEFAULT 'Scheduled',
    FOREIGN KEY (Toid) REFERENCES tournaments (Toid),
    FOREIGN KEY (Teid1) REFERENCES teams (Teid),
    FOREIGN KEY (Teid2) REFERENCES teams (Teid)
);


CREATE TABLE IF NOT EXISTS results (
    Rid INTEGER PRIMARY KEY AUTO_INCREMENT,
    Mid INTEGER NOT NULL,
    Teid1_score INTEGER NOT NULL,
    Teid2_score INTEGER NOT NULL,
    FOREIGN KEY (Mid) REFERENCES matches (Mid)
);

CREATE INDEX idx_To_id ON tournaments (Toid);
CREATE INDEX idx_Te_id ON teams (Teid);
CREATE INDEX idx_P_id ON players (Pid);
CREATE INDEX idx_TO_id ON matches (Toid, status);
"""

def main():
    try:
        manager = DatabaseManager("tournament.db")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except (EOFError, KeyboardInterrupt):
        print("Application interrupted.")
    finally:
        manager.close()  # close the database for a safer self
    

if __name__ == "__main__":
    main()