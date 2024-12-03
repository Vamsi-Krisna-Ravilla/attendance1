# config.py
import os
from datetime import datetime

# Database configuration
DB_FILE = 'attendance.db'

# Admin credentials
ADMIN_CREDENTIALS = {
    'admin': 'admin123'  # Change for production
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

# Subjects for each program-branch combination
SUBJECTS = {
    'B.Tech-I-CSE': ['Python', 'Mathematics-I', 'Physics'],
    'B.Tech-II-CSE': ['Data Structures', 'DBMS', 'Java'],
    'MCA-I': ['Programming Fundamentals', 'Computer Organization'],
    # Add more subjects as needed
}

# Faculty data
FACULTY = [
    ('faculty1', 'pass1'),
    ('faculty2', 'pass2'),
    ('faculty3', 'pass3')
]

# Time periods with timings
PERIODS = {
    'P1': '09:00-10:00',
    'P2': '10:00-11:00',
    'P3': '11:00-12:00',
    'P4': '12:00-13:00',
    'P5': '13:45-14:45',
    'P6': '14:45-16:00'
}

# Helper functions
def get_section_name(program, year, branch, section):
    return f"{program}-{year}-{branch}-{section}"

def get_original_section_name(section_name):
    return f"(O){section_name}"

def get_available_sections():
    sections = []
    for program, prog_data in SECTIONS.items():
        for year in prog_data['years']:
            for branch, branch_sections in prog_data['branches'].items():
                for section in branch_sections:
                    section_name = get_section_name(program, year, branch, section)
                    sections.append(section_name)
    return sections

def get_subjects_for_section(program, year, branch):
    key = f"{program}-{year}-{branch}"
    return SUBJECTS.get(key, [])