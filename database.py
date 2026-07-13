import os
import psycopg2


DATABASE_URL = os.getenv("DATABASE_URL")


def connect():
    return psycopg2.connect(DATABASE_URL)


def create_table():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            full_name TEXT,
            photo TEXT,
            student_number TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    cur.close()
    conn.close()



def add_student(telegram_id, full_name, photo):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO students
        (telegram_id, full_name, photo, status)

        VALUES (%s,%s,%s,%s)

        ON CONFLICT (telegram_id)
        DO UPDATE SET
        full_name=EXCLUDED.full_name,
        photo=EXCLUDED.photo
    """,
    (
        telegram_id,
        full_name,
        photo,
        "pending"
    ))

    conn.commit()

    cur.close()
    conn.close()



def get_pending_students():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM students
        WHERE status='pending'
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data
    
def get_pending_students():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,
               telegram_id,
               full_name,
               photo,
               student_number,
               status
        FROM students
        WHERE status='pending'
        ORDER BY id
    """)

    students = cur.fetchall()

    cur.close()
    conn.close()

    return students
