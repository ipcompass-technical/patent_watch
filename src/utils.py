# -----------------------------------------------------------------
# UTILITY FUNCTIONS
# Helper functions used by multiple scripts.
# -----------------------------------------------------------------
import json
from datetime import datetime

def load_json_history(filepath):
    """
    Safely loads a JSON history file. If it's missing, empty, or
    corrupt, returns an empty list.
    """
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Warning: History file {filepath} is corrupt. Resetting.")
                return []
            return data
    except json.JSONDecodeError:
        print(f"Warning: History file {filepath} is empty or corrupt. Resetting.")
        return []

def save_json_history(filepath, data):
    """Saves a list to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def reformat_search_date(date_str_ddmmyyyy):
    """
    Converts a "DD/MM/YYYY" date string to the "MM/DD/YYYY"
    format required by the search form.
    """
    try:
        date_obj = datetime.strptime(date_str_ddmmyyyy, "%d/%m/%Y")
        return date_obj.strftime("%m/%d/%Y")
    except ValueError:
        print(f"Error: Invalid date format '{date_str_ddmmyyyy}'. Expected DD/MM/YYYY.")
        return None

def parse_serial(serial_str):
    """Parse serial number in format 'week/year' and return (week, year) tuple."""
    try:
        parts = serial_str.split('/')
        if len(parts) == 2:
            week = int(parts[0])
            year = int(parts[1])
            return (week, year)
    except (ValueError, IndexError):
        pass
    return None

def compare_serials(serial1, serial2):
    """
    Compare two serial numbers in format 'week/year'.
    Returns: -1 if serial1 < serial2, 0 if equal, 1 if serial1 > serial2
    """
    parsed1 = parse_serial(serial1)
    parsed2 = parse_serial(serial2)
    
    if not parsed1 or not parsed2:
        return None
    
    week1, year1 = parsed1
    week2, year2 = parsed2
    
    if year1 < year2:
        return -1
    elif year1 > year2:
        return 1
    else:  # Same year, compare weeks
        if week1 < week2:
            return -1
        elif week1 > week2:
            return 1
        else:
            return 0