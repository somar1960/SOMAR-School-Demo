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

        VALUES (%s,%s,%s,'pending')

        ON CONFLICT (telegram_id)
        DO UPDATE SET
        full_name=EXCLUDED.full_name,
        photo=EXCLUDED.photo,
        status='pending'
    """,
    (
        telegram_id,
        full_name,
        photo
    ))

    conn.commit()
    cur.close()
    conn.close()



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

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data



def approve_student(student_id, student_number):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE students
        SET status='approved',
            student_number=%s
        WHERE id=%s
    """,
    (
        student_number,
        student_id
    ))

    conn.commit()
    cur.close()
    conn.close()



def reject_student(student_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE students
        SET status='rejected'
        WHERE id=%s
    """,
    (student_id,))

    conn.commit()
    cur.close()
    conn.close()



def get_student(student_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,
               telegram_id,
               full_name,
               photo,
               student_number
        FROM students
        WHERE id=%s
    """,
    (student_id,))

    student = cur.fetchone()

    cur.close()
    conn.close()

    return student
