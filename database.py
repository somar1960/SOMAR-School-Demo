import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def connect():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def create_table():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    photo_file_id TEXT NOT NULL,
                    student_number TEXT UNIQUE,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

def add_student(telegram_id, full_name, username, photo_file_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO students (telegram_id, full_name, username, photo_file_id, status)
                VALUES (%s, %s, %s, %s, 'pending')
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    username = EXCLUDED.username,
                    photo_file_id = EXCLUDED.photo_file_id,
                    status = 'pending',
                    student_number = NULL
                RETURNING id
            """, (telegram_id, full_name, username, photo_file_id))
            result = cur.fetchone()
            return result['id'] if result else None

def get_pending_students():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE status='pending' ORDER BY id")
            return cur.fetchall()

def get_student(student_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
            return cur.fetchone()

def get_student_by_telegram(telegram_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE telegram_id = %s", (telegram_id,))
            return cur.fetchone()

def generate_student_number(student_id: int) -> str:
    return f"SMS-{student_id:06d}"

def approve_student(student_id):
    number = generate_student_number(student_id)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE students
                SET status = 'approved', student_number = %s
                WHERE id = %s
                RETURNING *
            """, (number, student_id))
            return cur.fetchone()

def reject_student(student_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE students
                SET status = 'rejected'
                WHERE id = %s
                RETURNING *
            """, (student_id,))
            return cur.fetchone()
