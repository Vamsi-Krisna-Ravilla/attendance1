-- schema.sql
CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    credential TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,  -- e.g., 'B.Tech-I-CSE-A'
    is_original BOOLEAN DEFAULT 0,  -- 0 for manipulated, 1 for original
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    program TEXT NOT NULL,  -- e.g., 'B.Tech', 'MCA', 'Diploma'
    year INTEGER NOT NULL,  -- 1, 2, 3, 4
    branch TEXT NOT NULL,   -- 'CSE', 'ECE', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    ht_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    manipulated_section_id INTEGER,
    original_section_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manipulated_section_id) REFERENCES sections(id),
    FOREIGN KEY (original_section_id) REFERENCES sections(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    faculty_id INTEGER,
    subject_id INTEGER,
    section_id INTEGER,  -- Original section ID
    date DATE NOT NULL,
    time TIME NOT NULL,
    period TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('P', 'A')),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (section_id) REFERENCES sections(id),
    UNIQUE (student_id, date, period)
);

CREATE TABLE IF NOT EXISTS faculty_workload (
    id INTEGER PRIMARY KEY,
    faculty_id INTEGER,
    subject_id INTEGER,
    section_id INTEGER,
    date DATE NOT NULL,
    time TIME NOT NULL,
    period TEXT NOT NULL,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (section_id) REFERENCES sections(id)
);