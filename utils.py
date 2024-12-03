# utils.py
from datetime import datetime, time
from config import PERIOD_TIMINGS

def check_period_time(period):
    """Check if current time is within period time"""
    current_time = datetime.now().time()
    if period in PERIOD_TIMINGS:
        start_str, end_str = PERIOD_TIMINGS[period]
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        return start_time <= current_time <= end_time
    return False

def format_time(time_str):
    """Format time string for display"""
    return datetime.strptime(time_str, '%H:%M').strftime('%I:%M %p')

def validate_date_range(from_date, to_date):
    """Validate date range"""
    try:
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        return from_date <= to_date
    except:
        return False