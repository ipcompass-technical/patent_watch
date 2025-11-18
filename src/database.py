# src/database.py

import sqlite3
import config
import json

# -----------------------------------------------------------------
# SHARED FUNCTIONS
# -----------------------------------------------------------------

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

# -----------------------------------------------------------------
# 'init' COMMAND (main.py)
# -----------------------------------------------------------------

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
        status TEXT NOT NULL DEFAULT 'newly_extracted',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        publication_type TEXT
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
        return True
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        if conn:
            conn.close()

# -----------------------------------------------------------------
# 'migrate' COMMAND (main.py)
# -----------------------------------------------------------------

def add_publication_type_column():
    """
    Adds the 'publication_type' column to the 'patents' table.
    """
    conn = get_db_connection()
    if not conn:
        print("Error: Could not connect to DB for migration.")
        return

    try:
        cursor = conn.cursor()
        
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

# -----------------------------------------------------------------
# 'downloader' SCRIPT (downloader.py)
# -----------------------------------------------------------------

def get_downloaded_journal_ids():
    """
    Fetches all existing journal_ids from the database.
    """
    conn = get_db_connection()
    if not conn:
        return set()
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT journal_id FROM journals")
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
    """
    conn = get_db_connection()
    if not conn:
        print(f"Error: Could not log journal {journal_id}. No DB connection.")
        return

    sql = """
    INSERT OR IGNORE INTO journals (journal_id, part1_pdf_path, part2_pdf_path)
    VALUES (?, ?, ?)
    """
    
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

# -----------------------------------------------------------------
# 'extractor' SCRIPT (extractor.py)
# -----------------------------------------------------------------

def get_journals_to_process():
    """
    Finds all journals that have been downloaded but not extracted.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM journals WHERE status = 'downloaded'")
        journals = cursor.fetchall()
        return journals
    except sqlite3.Error as e:
        print(f"Error fetching journals to process: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_journal_status(journal_id, status):
    """
    Updates the status of a specific journal.
    """
    conn = get_db_connection()
    if not conn:
        print(f"Error: Could not update status for {journal_id}. No DB connection.")
        return

    sql = """
    UPDATE journals
    SET status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE journal_id = ?
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (status, journal_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating status for {journal_id}: {e}")
    finally:
        if conn:
            conn.close()

def insert_patent(patent_data):
    """
    Inserts or replaces a single patent into the 'patents' table.
    """
    conn = get_db_connection()
    if not conn:
        print("Error: No DB connection. Could not save patent.")
        return

    # Set defaults for fields the extractor finds
    patent_data.setdefault('international_classification', None)
    patent_data.setdefault('patent_type', None)
    patent_data.setdefault('status', 'newly_extracted')
    
    data_tuple = (
        patent_data.get('application_no'),
        patent_data.get('title'),
        patent_data.get('date_of_filing'),
        patent_data.get('publication_date'),
        patent_data.get('abstract'),
        patent_data.get('international_classification'),
        patent_data.get('patent_type'),
        patent_data.get('status'),
        patent_data.get('publication_type')
    )
    
    sql = """
    INSERT OR REPLACE INTO patents (
        application_no, title, date_of_filing, publication_date,
        abstract, ipc_codes, patent_type, status, publication_type
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, data_tuple)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting patent {patent_data.get('application_no')}: {e}")
    finally:
        if conn:
            conn.close()

# -----------------------------------------------------------------
# 'filter' COMMAND (filter.py)
# -----------------------------------------------------------------

def get_patents_to_classify():
    """
    Fetches all patents that are newly_extracted and need classification.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patents WHERE status = 'newly_extracted'")
        patents = cursor.fetchall()
        return patents
    except sqlite3.Error as e:
        print(f"Error fetching patents to classify: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_patent_classification(app_no, patent_type, ipc_codes_list):
    """
    Updates a patent's classification, status, and IPC codes list.
    """
    conn = get_db_connection()
    if not conn:
        print(f"Error: No DB connection. Could not update {app_no}")
        return

    # Store the list of IPC codes as a JSON string
    ipc_codes_json = json.dumps(ipc_codes_list)
    
    sql = """
    UPDATE patents
    SET patent_type = ?, 
        ipc_codes = ?, 
        status = 'classified', 
        updated_at = CURRENT_TIMESTAMP
    WHERE application_no = ?
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (patent_type, ipc_codes_json, app_no))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating patent classification for {app_no}: {e}")
    finally:
        if conn:
            conn.close()

# -----------------------------------------------------------------
# 'reset' and 'clear' COMMANDS (main.py)
# -----------------------------------------------------------------

def reset_journal_status(journal_id):
    """
    Resets a journal's status back to 'downloaded' for reprocessing.
    """
    print(f"Attempting to reset status for journal: {journal_id}")
    # We can just reuse the function we already built
    update_journal_status(journal_id, "downloaded")
    print(f"✓ Journal {journal_id} status reset to 'downloaded'.")


def clear_patents_table():
    """
    Deletes ALL data from the 'patents' table.
    Used for resetting the pipeline during debugging.
    """
    conn = get_db_connection()
    if not conn:
        print("Error: No DB connection. Could not clear patents.")
        return False

    print("WARNING: This will delete all patent records from the 'patents' table.")
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != 'DELETE':
        print("Operation cancelled.")
        return False
        
    sql = "DELETE FROM patents"
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print(f"✓ 'patents' table has been cleared.")
        return True
    except sqlite3.Error as e:
        print(f"Error clearing 'patents' table: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- NEW FUNCTION ---
def reset_patents_to_newly_extracted():
    """
    Resets all 'classified' patents back to 'newly_extracted'
    so the filter can be run again.
    """
    conn = get_db_connection()
    if not conn:
        print("Error: No DB connection.")
        return
        
    sql = """
    UPDATE patents
    SET status = 'newly_extracted', 
        patent_type = NULL,
        ipc_codes = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE status = 'classified'
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        count = cursor.rowcount
        conn.commit()
        print(f"✓ Reset {count} patents from 'classified' back to 'newly_extracted'.")
    except sqlite3.Error as e:
        print(f"Error resetting patent status: {e}")
    finally:
        if conn:
            conn.close()