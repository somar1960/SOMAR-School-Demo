import sqlite3

DB = "students.db"


def connect():
    return sqlite3.connect(DB)


def create_table():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        name TEXT,
        photo TEXT
    )
    """)

    conn.commit()
    conn.close()
