# src/database.py

import sqlite3
import config

def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    """
    conn = None
    try:
        conn = sqlite3.connect(config.DATABASE_FILE)
        # Return rows as dictionaries (like objects) instead of tuples
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables():
    """
    Initializes the database by creating the 'journals' and 'patents'
    tables if they do not already exist.
    
    Returns:
        True if tables were created successfully, False otherwise.
    """
    conn = get_db_connection()
    if not conn:
        print("Error: Could not create database connection. Tables not created.")
        return False

    # Use 'IF NOT EXISTS' to make this function safe to run multiple times
    create_journals_table_sql = """
    CREATE TABLE IF NOT EXISTS journals (
        journal_id TEXT PRIMARY KEY,
        part1_pdf_path TEXT,
        part2_pdf_path TEXT,
        status TEXT NOT NULL DEFAULT 'downloaded',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # As discussed, application_no is UNIQUE to prevent duplicates
    create_patents_table_sql = """
    CREATE TABLE IF NOT EXISTS patents (
        application_no TEXT PRIMARY KEY,
        title TEXT,
        date_of_filing TEXT,
        publication_date TEXT,
        abstract TEXT,
        ipc_codes TEXT,
        patent_type TEXT,
        
        -- THIS IS THE LINE I FIXED (was 'NOT new_DEFAULT')
        status TEXT NOT NULL DEFAULT 'newly_extracted',
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        cursor = conn.cursor()
        print("Initializing database...")
        cursor.execute(create_journals_table_sql)
        print("  ✓ 'journals' table created (or already exists).")
        cursor.execute(create_patents_table_sql)
        print("  ✓ 'patents' table created (or already exists).")
        conn.commit()
        print("Database initialization complete.")
        return True  # <-- ADD THIS
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        return False  # <-- ADD THIS
    finally:
        if conn:
            conn.close()


def get_downloaded_journal_ids():
    """
    Fetches all existing journal_ids from the database.
    
    Returns:
        A set of strings (e.g., {'44_2025', '45_2025'}) for
        fast 'in' lookups.
    """
    conn = get_db_connection()
    if not conn:
        return set()
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT journal_id FROM journals")
        # Use a set comprehension for efficient lookup
        journal_ids = {row['journal_id'] for row in cursor.fetchall()}
        return journal_ids
    except sqlite3.Error as e:
        print(f"Error fetching journal history: {e}")
        return set()
    finally:
        if conn:
            conn.close()

def log_journal(journal_id, part1_path, part2_path):
    """
    Logs a newly downloaded journal to the database.
    Uses 'INSERT OR IGNORE' to be idempotent, so if the
    journal_id already exists, it does nothing.
    
    Args:
        journal_id (str): The journal serial (e.g., "45_2025").
        part1_path (str): The relative path to Part I PDF.
        part2_path (str): The relative path to Part II PDF.
    """
    conn = get_db_connection()
    if not conn:
        print(f"Error: Could not log journal {journal_id}. No DB connection.")
        return

    sql = """
    INSERT OR IGNORE INTO journals (journal_id, part1_pdf_path, part2_pdf_path)
    VALUES (?, ?, ?)
    """
    
    # Convert Path objects to strings if they are paths
    p1_str = str(part1_path) if part1_path else None
    p2_str = str(part2_path) if part2_path else None
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (journal_id, p1_str, p2_str))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error logging journal {journal_id} to database: {e}")
    finally:
        if conn:
            conn.close()


def add_publication_type_column():
    """
    Adds the 'publication_type' column to the 'patents' table.
    Uses 'IF NOT EXISTS' to be safe to run multiple times.
    """
    conn = get_db_connection()
    if not conn:
        print("Error: Could not connect to DB for migration.")
        return

    try:
        cursor = conn.cursor()
        # Add the new column.
        # We can't use 'IF NOT EXISTS' for ADD COLUMN in SQLite
        # So we will check the table info first.
        
        cursor.execute("PRAGMA table_info(patents)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'publication_type' not in columns:
            print("Adding 'publication_type' column to 'patents' table...")
            cursor.execute("ALTER TABLE patents ADD COLUMN publication_type TEXT")
            conn.commit()
            print("  ✓ Column added.")
        else:
            print("'publication_type' column already exists.")
            
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()