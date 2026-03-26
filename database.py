import sqlite3
import os

DB_PATH = 'vietlott.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_type TEXT NOT NULL,
            draw_date TEXT NOT NULL,
            n1 INTEGER NOT NULL,
            n2 INTEGER NOT NULL,
            n3 INTEGER NOT NULL,
            n4 INTEGER NOT NULL,
            n5 INTEGER NOT NULL,
            n6 INTEGER NOT NULL,
            n7 INTEGER, -- Optional extra ball for Power 6/55
            jackpot TEXT,
            UNIQUE(game_type, draw_date)
        )
    ''')
    # Migration: check if n7 exists, if not add it
    try:
        c.execute("ALTER TABLE draws ADD COLUMN n7 INTEGER")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
