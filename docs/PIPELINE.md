
# Project Pipeline Logic & Architecture

This document explains the _why_ behind the scripts. The project has been refactored from a simple file-based prototype into a robust, database-driven pipeline.

## The Core Concept: A Database State Machine

The entire pipeline is controlled by a central SQLite database: `data/output/patent_watch.db`.

This database acts as a "to-do list" (or work queue) between scripts. The state of any piece of data is tracked by a `status` column. A script's job is to:

1.  **Query** the database for items with a specific status (e.g., `status = 'downloaded'`).
    
2.  **Process** those items.
    
3.  **Update** their status to the next step (e.g., `status = 'extracted'`).
    

This makes the pipeline **resumable, robust, and scalable.**

### Database Schema

1.  **`journals` table:**
    
    -   `journal_id` (e.g., "45_2025")
        
    -   `part1_pdf_path`, `part2_pdf_path`
        
    -   `status`: (e.g., `downloaded`, `extracting`, `extracted`, `error_extracting`)
        
2.  **`patents` table:**
    
    -   `application_no` (e.g., "202511087359")
        
    -   `title`, `abstract`, `date_of_filing`, `publication_date`
        
    -   `ipc_codes` (The raw string from the PDF)
        
    -   `patent_type` (e.g., `Software`, `Hybrid`, `Non-Software`)
        
    -   `publication_type` (e.g., `PART_I_EARLY`, `PART_II_NORMAL`)
        
    -   `status`: (e.g., `newly_extracted`, `classified`, `retrieval_in_progress`, `documents_retrieved`)
        

## Part 1: `downloader.py` (Ingestion)

-   **Objective:** Download new weekly patent journals (Parts I & II).
    
-   **Old Logic:** Saved history to `download_history.json`.
    
-   **New Logic:**
    
    1.  Queries the `journals` table to get a set of all `journal_id`s it has ever downloaded.
        
    2.  Scrapes the website.
        
    3.  If it finds a journal not in its database history, it downloads the PDF(s).
        
    4.  After a successful download, it **INSERTS** a new row into the `journals` table with the paths to the PDFs and a `status = 'downloaded'`.
        

## Part 2: `extractor.py` (Extraction)

-   **Objective:** Extract structured data from all newly downloaded PDFs.
    
-   **Old Logic:** Read from `raw_pdfs` folder, saved all data to `all_patents.json`. This was brittle and not resumable.
    
-   **New Logic:**
    
    1.  Queries the `journals` table for all rows where `status = 'downloaded'`.
        
    2.  It loops through these results. For each journal:
        
    3.  It **UPDATE**s the journal's status to `extracting`. This "locks" the file, preventing a re-run if the script crashes.
        
    4.  It opens the PDF(s) (e.g., `44_2025_Part_I.pdf`) and processes them **page-by-page**.
        
    5.  The new, robust regex finds a patent on a page, it **INSERT**s that patent's data into the `patents` table with `status = 'newly_extracted'`.
        
    6.  If a page is not a patent (e.g., an index or cover), the regex fails to match, and the script simply skips it.
        
    7.  After both PDFs are done, it **UPDATE**s the journal's status to `extracted`.
        

## Part 3: `filter.py` (Classification)

-   **Objective:** Classify all new patents as "Software," "Hybrid," or "Non-Software."
    
-   **Old Logic:** Read `all_patents.json`, wrote to `classified_patents.json`.
    
-   **New Logic:**
    
    1.  Queries the `patents` table for all rows where `status = 'newly_extracted'`. (This found 5,204 patents in our first run).
        
    2.  It loops through these results. For each patent:
        
    3.  It reads the `ipc_codes` string, splits it by comma (`,`), and runs the classification logic.
        
    4.  It **UPDATE**s the patent's row, setting the `patent_type` and changing the `status = 'classified'`.
        
    5.  It also stores the cleaned list of IPC codes as a JSON string back into the `ipc_codes` column for future use.
        

## Part 4: `searcher.py` (Retrieval)

-   **Objective:** Run the 5-stage `requests` search for every "Software" and "Hybrid" patent to download all associated legal documents.
    
-   **Old Logic:** Was a single-use script for one patent.
    
-   **New Logic (Task 4 Plan):**
    
    1.  This script will be converted into a worker.
        
    2.  It will query the `patents` table for all rows where `status = 'classified'` AND `patent_type IN ('Software', 'Hybrid')`.
        
    3.  It will loop through these results, updating the status (e.g., `retrieval_in_progress`, `documents_retrieved`, `error_captcha`) as it goes.
        
    4.  This will make the most time-consuming part of the pipeline fully automated and resumable.
