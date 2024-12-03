# app.py
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ================ Configuration Settings ================
# Database configuration
DB_FILE = 'attendance.db'

# Admin credentials
ADMIN_CREDENTIALS = {
    'admin': 'admin123'  # Change for production
}

# Period timings
PERIOD_TIMINGS = {
    'P1': ('09:00', '10:00'),
    'P2': ('10:00', '11:00'),
    'P3': ('11:00', '12:00'),
    'P4': ('12:00', '13:00'),
    'P5': ('13:45', '14:45'),
    'P6': ('14:45', '16:00')
}

# Program structure
SECTIONS = {
    'B.Tech': {
        'years': ['I', 'II', 'III', 'IV'],
        'branches': {
            'CSE': ['A', 'B', 'C'],
            'ECE': ['A', 'B'],
            'AI': ['A', 'B']
        }
    },
    'MCA': {
        'years': ['I', 'II'],
        'branches': {
            'MCA': ['A']
        }
    },
    'Diploma': {
        'years': ['I', 'II', 'III'],
        'branches': {
            'CSE': ['A', 'B'],
            'ECE': ['A']
        }
    }
}

# Subjects configuration
SUBJECTS = {
    'B.Tech-I-CSE': ['Python', 'Mathematics-I', 'Physics'],
    'B.Tech-II-CSE': ['Data Structures', 'DBMS', 'Java'],
    'MCA-I': ['Programming Fundamentals', 'Computer Organization'],
}

# Sample faculty data
FACULTY = [
    ('p', 'p'),
    ('faculty2', 'pass2'),
    ('faculty3', 'pass3')
]

# ================ Utility Functions ================
def get_section_name(program, year, branch, section):
    """Generate full section name"""
    return f"{program}-{year}-{branch}-{section}"

def get_original_section_name(section_name):
    """Generate original section name"""
    return f"(O){section_name}"

def check_period_time(period):
    """Check if current time is within period time"""
    current_time = datetime.now().time()
    if period in PERIOD_TIMINGS:
        start_str, end_str = PERIOD_TIMINGS[period]
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        return start_time <= current_time <= end_time
    return False

def validate_date_range(from_date, to_date):
    """Validate date range"""
    try:
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        return from_date <= to_date
    except:
        return False

# ================ Database Functions ================
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables and sample data"""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Create tables
        cur.executescript('''
            CREATE TABLE faculty (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                credential TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE sections (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                is_original BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                year TEXT NOT NULL,
                branch TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE students (
                id INTEGER PRIMARY KEY,
                ht_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                manipulated_section_id INTEGER,
                original_section_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manipulated_section_id) REFERENCES sections(id),
                FOREIGN KEY (original_section_id) REFERENCES sections(id)
            );

            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                faculty_id INTEGER,
                subject_id INTEGER,
                section_id INTEGER,
                date DATE NOT NULL,
                time TIME NOT NULL,
                period TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('P', 'A')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (faculty_id) REFERENCES faculty(id),
                FOREIGN KEY (subject_id) REFERENCES subjects(id),
                FOREIGN KEY (section_id) REFERENCES sections(id),
                UNIQUE (student_id, date, period)
            );

            CREATE TABLE faculty_workload (
                id INTEGER PRIMARY KEY,
                faculty_id INTEGER,
                section_id INTEGER,
                subject_id INTEGER,
                date DATE NOT NULL,
                time TIME NOT NULL,
                period TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (faculty_id) REFERENCES faculty(id),
                FOREIGN KEY (section_id) REFERENCES sections(id),
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            );
        ''')
        
        # Insert initial data
        # Add faculty
        for faculty_name, credential in FACULTY:
            cur.execute('INSERT INTO faculty (name, credential) VALUES (?, ?)',
                       (faculty_name, credential))
        
        # Add sections and subjects
        for program, prog_data in SECTIONS.items():
            for year in prog_data['years']:
                for branch, sections in prog_data['branches'].items():
                    # Add subjects for this combination
                    key = f"{program}-{year}-{branch}"
                    if key in SUBJECTS:
                        for subject in SUBJECTS[key]:
                            cur.execute('''
                                INSERT INTO subjects (name, program, year, branch)
                                VALUES (?, ?, ?, ?)
                            ''', (subject, program, year, branch))
                    
                    # Add sections (both original and manipulated)
                    for section in sections:
                        section_name = get_section_name(program, year, branch, section)
                        # Add manipulated section
                        cur.execute('INSERT INTO sections (name, is_original) VALUES (?, 0)',
                                  (section_name,))
                        # Add original section
                        cur.execute('INSERT INTO sections (name, is_original) VALUES (?, 1)',
                                  (get_original_section_name(section_name),))
        
        conn.commit()
        conn.close()
        return True
    return True

def check_credentials(username, password, is_admin=False):
    """Verify login credentials"""
    if is_admin:
        return ADMIN_CREDENTIALS.get(username) == password
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT credential FROM faculty WHERE name = ?', (username,))
        result = cur.fetchone()
        return result and result['credential'] == password

def get_sections_for_faculty():
    """Get available sections for faculty"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT name FROM sections WHERE is_original = 0 ORDER BY name')
        return [row['name'] for row in cur.fetchall()]

def get_subjects_for_section(section_name):
    """Get subjects for a section"""
    program, year, branch, _ = section_name.split('-')
    key = f"{program}-{year}-{branch}"
    return SUBJECTS.get(key, [])

def get_students_in_section(section_name):
    """Get students in a section"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT s.ht_number, s.name, orig.name as original_section
            FROM students s
            JOIN sections manip ON s.manipulated_section_id = manip.id
            JOIN sections orig ON s.original_section_id = orig.id
            WHERE manip.name = ?
            ORDER BY s.ht_number
        ''', (section_name,))
        return [dict(row) for row in cur.fetchall()]

def check_duplicate_attendance(section_name, period, date):
    """Check for duplicate attendance entries"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT f.name, sub.name, a.time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN sections sec ON s.original_section_id = sec.id
            JOIN faculty f ON a.faculty_id = f.id
            JOIN subjects sub ON a.subject_id = sub.id
            WHERE sec.name = ? AND a.period = ? AND a.date = ?
            LIMIT 1
        ''', (section_name, period, date))
        result = cur.fetchone()
        
        if result:
            return True, f"Attendance already marked by {result['name']} for {result[1]} at {result[2]}"
        return False, ""

def mark_attendance(attendance_data, faculty_name):
    """Mark attendance for students"""
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
                cur.execute('''
                    SELECT s.id, s.original_section_id 
                    FROM students s 
                    WHERE s.ht_number = ?
                ''', (student['ht_number'],))
                student_data = cur.fetchone()
                if not student_data:
                    continue
                
                student_id = student_data['id']
                original_section_id = student_data['original_section_id']
                
                # Get subject ID
                cur.execute('SELECT id FROM subjects WHERE name = ?', (student['subject'],))
                subject_id = cur.fetchone()['id']
                
                # Insert attendance record
                cur.execute('''
                    INSERT INTO attendance 
                    (student_id, faculty_id, subject_id, section_id, date, time, period, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student_id, faculty_id, subject_id, original_section_id,
                    current_date, current_time,
                    student['period'],
                    'P' if student['present'] else 'A'
                ))
                
                # Record faculty workload
                cur.execute('''
                    INSERT INTO faculty_workload
                    (faculty_id, section_id, subject_id, date, time, period)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    faculty_id, original_section_id, subject_id,
                    current_date, current_time, student['period']
                ))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error marking attendance: {e}")
        return False

# ================ Streamlit Interface Functions ================
def display_login_page():
    """Display login page"""
    st.title("Attendance Management System")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        login_type = st.radio("Select Login Type", ["Faculty", "Admin"])
    
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            is_admin = login_type == "Admin"
            if check_credentials(username, password, is_admin):
                st.session_state.logged_in = True
                st.session_state.is_admin = is_admin
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

def display_faculty_page():
    """Display faculty dashboard"""
    st.title(f"Welcome, {st.session_state.username}")
    
    # Sidebar
    with st.sidebar:
        st.header("Control Panel")
        current_date = datetime.now().strftime('%d/%m/%Y')
        current_time = datetime.now().strftime('%I:%M %p')
        st.write(f"Date: {current_date}")
        st.write(f"Time: {current_time}")
        
        # Period selection
        st.session_state.period = st.selectbox(
            "Select Period",
            [''] + list(PERIOD_TIMINGS.keys())
        )
        
        # Section selection
        sections = get_sections_for_faculty()
        st.session_state.section = st.selectbox(
            "Select Section",
            [''] + sections
        )
        
        # Subject selection
        if st.session_state.section:
            subjects = get_subjects_for_section(st.session_state.section)
            st.session_state.subject = st.selectbox(
                "Select Subject",
                [''] + subjects
            )
        
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content
    st.info("\n".join([
        f"Period Timings:",
        *[f"{p}: {start}-{end}" for p, (start, end) in PERIOD_TIMINGS.items()]
    ]))
    
    if not all([st.session_state.get(key) for key in ['period', 'section', 'subject']]):
        st.warning("Please select Period, Section, and Subject to proceed.")
        return
    
    # Check period timing
    if not check_period_time(st.session_state.period):
        st.error("Selected period is not currently active.")
        return
    
    # Check duplicate attendance
    is_duplicate, message = check_duplicate_attendance(
        st.session_state.section,
        st.session_state.period,
        datetime.now().date().isoformat()
    )
    if is_duplicate:
        st.warning(message)
        return
    
    # Display attendance form
    st.subheader(f"Mark Attendance for {st.session_state.section} - {st.session_state.subject}")
    
    students = get_students_in_section(st.session_state.section)
    if not students:
        st.error("No students found in selected section")
        return
    
    # Create attendance form
    attendance_data = []
    
    cols = st.columns([2, 2, 2, 1])
    with cols[0]:
        st.markdown("**HT Number**")
    with cols[1]:
        st.markdown("**Student Name**")
    with cols[2]:
        st.markdown("**Original Section**")
    with cols[3]:
        st.markdown("**Present**")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    for student in students:
        cols = st.columns([2, 2, 2, 1])
        with cols[0]:
            st.write(student['ht_number'])
        with cols[1]:
            st.write(student['name'])
        with cols[2]:
            st.write(student['original_section'])
        with cols[3]:
            present = st.checkbox(
                "Present",
                key=f"{student['ht_number']}",
                value=True
            )
        
        attendance_data.append({
            'ht_number': student['ht_number'],
            'subject': st.session_state.subject,
            'period': st.session_state.period,
            'present': present
        })
    
    if st.button("Submit Attendance", type="primary"):
        if mark_attendance(attendance_data, st.session_state.username):
            st.success("Attendance marked successfully!")
            # Clear form
            st.session_state.period = ''
            st.session_state.section = ''
            st.session_state.subject = ''
            st.rerun()
        else:
            st.error("Failed to mark attendance")

def display_admin_page():
    """Display admin dashboard"""
    st.title("Admin Dashboard")
    
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Student Statistics", "Faculty Workload", "Manage Data"]
        )
        
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    if page == "Student Statistics":
        display_student_statistics()
    elif page == "Faculty Workload":
        display_faculty_workload()
    else:
        display_manage_data()

def display_student_statistics():
    """Display student attendance statistics"""
    st.header("Student Attendance Statistics")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date")
    with col2:
        to_date = st.date_input("To Date")
    
    if not validate_date_range(from_date.isoformat(), to_date.isoformat()):
        st.error("Invalid date range")
        return
    
    # Section selection
    sections = get_sections_for_faculty()
    selected_sections = st.multiselect("Select Sections", sections)
    
    if st.button("Generate Report"):
        with get_db() as conn:
            cur = conn.cursor()
            placeholders = ','.join(['?'] * len(selected_sections))
            
            query = f"""
                SELECT 
                    s.ht_number,
                    s.name as student_name,
                    sec.name as section,
                    sub.name as subject,
                    COUNT(*) as total_classes,
                    SUM(CASE WHEN a.status = 'P' THEN 1 ELSE 0 END) as present_classes,
                    ROUND(CAST(SUM(CASE WHEN a.status = 'P' THEN 1 ELSE 0 END) AS FLOAT) / 
                          COUNT(*) * 100, 2) as attendance_percentage
                FROM students s
                JOIN sections sec ON s.manipulated_section_id = sec.id
                JOIN attendance a ON s.id = a.student_id
                JOIN subjects sub ON a.subject_id = sub.id
                WHERE sec.name IN ({placeholders})
                AND date(a.date) BETWEEN ? AND ?
                GROUP BY s.ht_number, s.name, sec.name, sub.name
                ORDER BY sec.name, s.ht_number, sub.name
            """
            
            cur.execute(query, selected_sections + [from_date, to_date])
            results = [dict(row) for row in cur.fetchall()]
            
            if results:
                df = pd.DataFrame(results)
                
                # Summary statistics
                st.subheader("Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Students", len(df['ht_number'].unique()))
                with col2:
                    avg_attendance = df['attendance_percentage'].mean()
                    st.metric("Average Attendance", f"{avg_attendance:.2f}%")
                with col3:
                    below_75 = len(df[df['attendance_percentage'] < 75]['ht_number'].unique())
                    st.metric("Students Below 75%", below_75)
                
                # Detailed report
                st.subheader("Detailed Report")
                st.dataframe(df)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Report",
                    csv,
                    "attendance_report.csv",
                    "text/csv"
                )
            else:
                st.warning("No attendance records found for selected criteria")

def display_faculty_workload():
    """Display faculty workload analysis"""
    st.header("Faculty Workload Analysis")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date")
    with col2:
        to_date = st.date_input("To Date")
    
    if not validate_date_range(from_date.isoformat(), to_date.isoformat()):
        st.error("Invalid date range")
        return
    
    # Faculty selection
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM faculty ORDER BY name")
        faculty_list = [row['name'] for row in cur.fetchall()]
    
    selected_faculty = st.multiselect("Select Faculty", faculty_list)
    
    if st.button("Generate Report"):
        with get_db() as conn:
            cur = conn.cursor()
            placeholders = ','.join(['?'] * len(selected_faculty))
            
            query = f"""
                SELECT 
                    f.name as faculty_name,
                    COUNT(DISTINCT fw.date || fw.period) as total_classes,
                    COUNT(DISTINCT fw.date) as working_days,
                    COUNT(DISTINCT sub.id) as unique_subjects,
                    COUNT(DISTINCT sec.id) as unique_sections,
                    GROUP_CONCAT(DISTINCT sub.name) as subjects_handled,
                    GROUP_CONCAT(DISTINCT sec.name) as sections_handled
                FROM faculty f
                LEFT JOIN faculty_workload fw ON f.id = fw.faculty_id
                LEFT JOIN subjects sub ON fw.subject_id = sub.id
                LEFT JOIN sections sec ON fw.section_id = sec.id
                WHERE f.name IN ({placeholders})
                AND date(fw.date) BETWEEN ? AND ?
                GROUP BY f.name
            """
            
            cur.execute(query, selected_faculty + [from_date, to_date])
            results = [dict(row) for row in cur.fetchall()]
            
            if results:
                for faculty in results:
                    with st.expander(f"📊 {faculty['faculty_name']}", expanded=True):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Classes", faculty['total_classes'])
                        with col2:
                            st.metric("Working Days", faculty['working_days'])
                        with col3:
                            st.metric("Subjects", faculty['unique_subjects'])
                        with col4:
                            st.metric("Sections", faculty['unique_sections'])
                        
                        st.write("**Subjects Handled:**", faculty['subjects_handled'])
                        st.write("**Sections Handled:**", faculty['sections_handled'])
                
                # Create downloadable report
                df = pd.DataFrame(results)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Workload Report",
                    csv,
                    "faculty_workload.csv",
                    "text/csv"
                )
            else:
                st.warning("No workload data found for selected criteria")

def display_manage_data():
    """Display data management interface"""
    st.header("Manage System Data")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Students", "Faculty", "Sections & Subjects", "Upload Data"
    ])
    
    with tab1:
        st.subheader("Student Management")
        section = st.selectbox(
            "Select Section",
            get_sections_for_faculty()
        )
        if section:
            students = get_students_in_section(section)
            df = pd.DataFrame(students)
            st.dataframe(df)
            
            # Export option
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    "Export Student Data",
                    csv,
                    "students.csv",
                    "text/csv"
                )
    
    with tab2:
        st.subheader("Faculty Management")
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, created_at FROM faculty")
            faculty = [dict(row) for row in cur.fetchall()]
            df = pd.DataFrame(faculty)
            st.dataframe(df)
    
    with tab3:
        st.subheader("Sections and Subjects")
        for program, prog_data in SECTIONS.items():
            st.write(f"**{program}**")
            for year in prog_data['years']:
                for branch in prog_data['branches']:
                    key = f"{program}-{year}-{branch}"
                    if key in SUBJECTS:
                        st.write(f"{key}: {', '.join(SUBJECTS[key])}")
    
    with tab4:
        st.subheader("Upload Data")
        uploaded_file = st.file_uploader("Choose Excel file", type="xlsx")
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df)
                if st.button("Process Upload"):
                    st.info("Data processing functionality to be implemented")
            except Exception as e:
                st.error(f"Error processing file: {e}")

def main():
    """Main application entry point"""
    # Initialize database
    if not init_db():
        st.error("Failed to initialize database. Please check file permissions and try again.")
        return
    
    # Handle session state
    if 'logged_in' not in st.session_state:
        display_login_page()
    else:
        if st.session_state.is_admin:
            display_admin_page()
        else:
            display_faculty_page()

if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="Attendance Management System",
        page_icon="📋",
        layout="wide"
    )
    
    # Run application
    main()