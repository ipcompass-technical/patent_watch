
# Patent Watch - Data Pipeline

This project is a database-driven pipeline to download, parse, classify, and retrieve documents for Indian patent applications.

The entire pipeline is managed by a central SQLite database (`patent_watch.db`) which acts as a "to-do list" or work queue between the different scripts. All scripts are run using the central `main.py` control script.

## Prerequisites

-   Python 3.10 or- later
    
-   pip (Python package installer)
    
-   A virtual environment (`.venv`)
    

## Installation

1.  **Clone the project:**
    
    ```
    git clone [your-repo-url]
    cd patent_watch
    
    ```
    
2.  **Create and activate a virtual environment:**
    
    ```
    python3 -m venv .venv
    source .venv/bin/activate
    
    ```
    
3.  **Install requirements:**
    
    ```
    pip install -r requirements.txt
    
    ```
    
4.  Initialize the Database:
    
    This is a one-time setup. This command creates the patent_watch.db file and all the necessary tables.
    
    ```
    python main.py init
    
    ```
    
5.  Run Database Migrations:
    
    If you have an existing database and need to add new columns (like publication_type), run this.
    
    ```
    python main.py migrate
    
    ```
    

## How to Run the Pipeline

All commands must be run from the root `patent_watch/` directory with your virtual environment **active** (`source .venv/bin/activate`).

### Main Pipeline Commands

These are the main steps of the pipeline, run in order.

1.  **Download new journals:**
    
    ```
    python main.py download
    
    ```
    
    _Finds new journals on the website and logs them as 'downloaded' in the `journals` table._
    
2.  **Extract data from PDFs:**
    
    ```
    python main.py extract
    
    ```
    
    _Finds 'downloaded' journals, parses them, and saves all patent data to the `patents` table as 'newly_extracted'._
    
3.  **Filter for software patents:**
    
    ```
    python main.py filter
    
    ```
    
    _Finds 'newly_extracted' patents, classifies them, and updates them as 'classified'._
    
4.  Run the 'all' command:
    
    This runs download, extract, and filter in sequence.
    
    ```
    python main.py all
    
    ```
    
5.  Retrieve Specific Documents:
    
    (Work in Progress) This will run the searcher.py worker script.
    
    ```
    python main.py search
    
    ```
    

### Database Management Commands

These commands are used for debugging and managing the pipeline's state.

-   python main.py init
    
    (One-time setup) Creates the database and tables.
    
-   python main.py migrate
    
    (Run when schema changes) Adds new columns to the database.
    
-   python main.py reset [journal_id]
    
    Resets a journal's status back to downloaded in the journals table.
    
    Example: python main.py reset 44_2025
    
-   python main.py reset-patents
    
    Resets all classified patents back to newly_extracted in the patents table, so the filter can be re-run.
    
-   python main.py clear
    
    DANGER: Deletes ALL patent data from the patents table. Asks for confirmation. Used for a full reset of the extraction step.
