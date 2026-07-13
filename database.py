import sqlite3

DB_NAME = "students.db"


def connect():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            photo TEXT,
            student_number TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    conn.close()


def add_student(telegram_id, full_name, photo):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO students
        (telegram_id, full_name, photo, status)

        VALUES (?, ?, ?, ?)
    """, (
        telegram_id,
        full_name,
        photo,
        "pending"
    ))

    conn.commit()
    conn.close()


def get_pending_students():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM students
        WHERE status='pending'
    """)

    students = cur.fetchall()

    conn.close()

    return students


def approve_student(student_id, student_number):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE students
        SET status='approved',
            student_number=?
        WHERE id=?
    """, (
        student_number,
        student_id
    ))

    conn.commit()
    conn.close()


def reject_student(student_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM students
        WHERE id=?
    """, (
        student_id,
    ))

    conn.commit()
    conn.close()


def get_student(student_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM students
        WHERE id=?
    """, (
        student_id,
    ))

    student = cur.fetchone()

    conn.close()

    return student
