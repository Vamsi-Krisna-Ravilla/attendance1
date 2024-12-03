# database.py
import sqlite3
import os
from datetime import datetime
from config import DB_FILE, SECTIONS, SUBJECTS, FACULTY

# database.py
import sqlite3
import os
from datetime import datetime
from config import (
    DB_FILE, 
    SECTIONS, 
    SUBJECTS, 
    FACULTY, 
    get_section_name,
    get_original_section_name,
    get_available_sections
)


# database.py
def init_db():
    """Initialize database with tables and sample data"""
    try:
        # Check if file exists and if it's a valid SQLite database
        if os.path.exists(DB_FILE):
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.close()
            except sqlite3.DatabaseError:
                # If file exists but is corrupted, delete it
                os.remove(DB_FILE)
        
        # Create new database
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Read and execute schema
        with open('schema.sql', 'r') as schema_file:
            cur.executescript(schema_file.read())
        
        # Check if faculty table is empty before inserting sample data
        cur.execute("SELECT COUNT(*) FROM faculty")
        if cur.fetchone()[0] == 0:
            # Insert sample data
            # Add faculty
            for faculty_name, credential in FACULTY:
                cur.execute('INSERT INTO faculty (name, credential) VALUES (?, ?)',
                           (faculty_name, credential))
            
            # Add sections
            for section in SECTIONS:
                cur.execute('INSERT INTO sections (name) VALUES (?)', (section,))
            
            # Add subjects and map to sections
            for section in SECTIONS:
                section_subjects = SUBJECTS[section]
                for subject in section_subjects:
                    cur.execute('INSERT INTO subjects (name) VALUES (?)', (subject,))
                    cur.execute('''
                        INSERT INTO section_subjects (section_id, subject_id)
                        SELECT s.id, sub.id
                        FROM sections s, subjects sub
                        WHERE s.name = ? AND sub.name = ?
                    ''', (section, subject))
            
            # Add sample students
            for section in SECTIONS:
                for i in range(1, 6):  # 5 students per section
                    ht_number = f'{section}-{i:02d}'
                    name = f'Student {section}-{i}'
                    cur.execute('''
                        INSERT INTO students (ht_number, name, section_id)
                        SELECT ?, ?, id FROM sections WHERE name = ?
                    ''', (ht_number, name, section))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        return False


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Authentication functions
def check_credentials(username, password, is_admin=False):
    if is_admin:
        from config import ADMIN_CREDENTIALS
        return ADMIN_CREDENTIALS.get(username) == password
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT credential FROM faculty WHERE name = ?', (username,))
        result = cur.fetchone()
        return result and result['credential'] == password

# Data retrieval functions
def get_sections():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT name FROM sections ORDER BY name')
        return [row['name'] for row in cur.fetchall()]

def get_section_subjects(section):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT DISTINCT sub.name
            FROM subjects sub
            JOIN section_subjects ss ON sub.id = ss.subject_id
            JOIN sections sec ON ss.section_id = sec.id
            WHERE sec.name = ?
            ORDER BY sub.name
        ''', (section,))
        return [row['name'] for row in cur.fetchall()]

def get_students(section):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT s.id, s.ht_number, s.name
            FROM students s
            JOIN sections sec ON s.section_id = sec.id
            WHERE sec.name = ?
            ORDER BY s.ht_number
        ''', (section,))
        return [dict(row) for row in cur.fetchall()]

def check_duplicate_attendance(section, period, date):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT f.name, sub.name, a.time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN sections sec ON s.section_id = sec.id
            JOIN faculty f ON a.faculty_id = f.id
            JOIN subjects sub ON a.subject_id = sub.id
            WHERE sec.name = ? AND a.period = ? AND a.date = ?
            LIMIT 1
        ''', (section, period, date))
        result = cur.fetchone()
        
        if result:
            return True, f"Attendance already marked by {result['name']} for {result[1]} at {result[2]}"
        return False, ""

def mark_attendance(attendance_data, faculty_name):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Get faculty ID
            cur.execute('SELECT id FROM faculty WHERE name = ?', (faculty_name,))
            faculty_id = cur.fetchone()['id']
            
            current_date = datetime.now().date().isoformat()
            current_time = datetime.now().time().isoformat()
            
            for student in attendance_data:
                # Get student and subject IDs
                cur.execute('SELECT id FROM students WHERE ht_number = ?', (student['ht_number'],))
                student_id = cur.fetchone()['id']
                
                cur.execute('SELECT id FROM subjects WHERE name = ?', (student['subject'],))
                subject_id = cur.fetchone()['id']
                
                # Insert attendance record
                cur.execute('''
                    INSERT INTO attendance 
                    (student_id, faculty_id, subject_id, date, time, period, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student_id, faculty_id, subject_id,
                    current_date, current_time,
                    student['period'],
                    'P' if student['present'] else 'A'
                ))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error marking attendance: {e}")
        return False

# Report generation functions
def generate_attendance_report(from_date, to_date, sections):
    with get_db() as conn:
        cur = conn.cursor()
        
        report_data = []
        for section in sections:
            cur.execute('''
                SELECT 
                    s.ht_number,
                    s.name as student_name,
                    sub.name as subject,
                    COUNT(*) as total_classes,
                    SUM(CASE WHEN a.status = 'P' THEN 1 ELSE 0 END) as present_classes
                FROM students s
                JOIN sections sec ON s.section_id = sec.id
                JOIN attendance a ON s.id = a.student_id
                JOIN subjects sub ON a.subject_id = sub.id
                WHERE sec.name = ?
                AND a.date BETWEEN ? AND ?
                GROUP BY s.id, sub.id
            ''', (section, from_date, to_date))
            
            results = cur.fetchall()
            for row in results:
                attendance_percent = (row['present_classes'] / row['total_classes'] * 100) if row['total_classes'] > 0 else 0
                report_data.append({
                    'HT Number': row['ht_number'],
                    'Student Name': row['student_name'],
                    'Section': section,
                    'Subject': row['subject'],
                    'Total Classes': row['total_classes'],
                    'Present': row['present_classes'],
                    'Attendance %': round(attendance_percent, 2)
                })
        
        return report_data