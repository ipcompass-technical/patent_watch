# Project Directory Structure

This document explains the layout of the `patent_watch` project and the role of each file and folder.

```
patent_watch/
│
├── .git/               # (Hidden) All Git version control history.
├── .gitignore          # Tells Git which files/folders to ignore (data, .venv, __pycache__)
│
├── data/               # Contains all data that is NOT code.
│   ├── raw_pdfs/       # Downloaded PDF patent journals live here.
│   └── output/         # All generated files: debug HTML, and the central database.
│       └── patent_watch.db  # <-- CRITICAL: The main SQLite database.
│
├── docs/               # All project documentation.
│   ├── README.md       # "How to Install and Run" guide.
│   ├── PIPELINE.md     # "Why" - Explains the logic of the database state machine.
│   └── STRUCTURE.md    # "What" - This file.
│
├── src/                # "Source" - All Python code lives here.
│   ├── __init__.py     # (Empty) Magic file that tells Python 'src' is a package.
│   ├── database.py     # <-- CRITICAL: Central module for all database interactions.
│   ├── downloader.py   # Module for downloading new journals (sends to DB).
│   ├── extractor.py    # Module for parsing PDFs (reads/writes from DB).
│   ├── filter.py       # Module for classifying patents (reads/writes from DB).
│   ├── searcher.py     # Module for running the human-in-the-loop search.
│   └── utils.py        # Helper functions (like date formatting) used by other modules.
│
├── .venv/              # (Hidden) Your local Python virtual environment.
│
├── config.py           # Central settings file. All URLs, file paths, and settings.
├── main.py             # The main "control panel" for the whole pipeline.
└── requirements.txt    # List of all required Python libraries (pip).

```
