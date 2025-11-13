# Project Directory Structure

This document explains the layout of the `patent_watch` project and the role of each file and folder.

```
patent_watch/
│
├── .git/               # (Hidden) All Git version control history.
├── .gitignore          # Tells Git which files/folders to ignore (data, cache, etc.)
│
├── data/               # Contains all data that is NOT code.
│   ├── raw_pdfs/       # Downloaded PDF patent journals live here.
│   └── output/         # All generated files: JSONs, HTML reports, and the captcha.
│
├── docs/               # All project documentation.
│   ├── README.md       # "How to Install and Run" guide.
│   ├── PIPELINE.md     # "Why" - Explains the logic and traps of the scripts.
│   └── STRUCTURE.md    # "What" - This file.
│
├── src/                # "Source" - All Python code lives here.
│   ├── __init__.py     # (Empty) Magic file that tells Python 'src' is a package.
│   ├── downloader.py   # Module for downloading new journals.
│   ├── extractor.py    # Module for parsing PDFs into JSON.
│   ├── filter.py       # Module for filtering patents for software.
│   ├── searcher.py     # Module for running the human-in-the-loop search.
│   └── utils.py        # Helper functions (like date formatting) used by other modules.
│
├── .venv/              # (Hidden) Your local Python virtual environment.
│
├── config.py           # Central settings file. All URLs, file paths, and secrets.
├── main.py             # The main "control panel" for the whole pipeline.
└── requirements.txt    # List of all Python libraries needed for the project.

```
