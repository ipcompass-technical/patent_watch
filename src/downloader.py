# src/downloader.py

import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Import configuration and utilities from our own package
from . import utils
import config

# --- MODIFICATION: Import database ---
from . import database

def run_downloader():
    """
    Finds and downloads new patent journals (Parts I & II) that are
    not listed in the 'journals' database table.
    """
    print("--- Running Downloader ---")
    
    # 1. Setup
    # Ensure directories exist
    config.RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    # --- MODIFICATION: Load history from database instead of JSON ---
    # This is now a SET for faster lookups (e.g., {'44_2025', '45_2025'})
    download_history = database.get_downloaded_journal_ids()
    print(f"Loaded {len(download_history)} journals from database history.")
    
    # 2. Fetch the webpage
    print(f"Fetching webpage: {config.DOWNLOADER_BASE_URL}")
    try:
        response = requests.get(
            config.DOWNLOADER_BASE_URL, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response.raise_for_status()

        debug_path = config.OUTPUT_DIR / "debug_page.html"
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"DEBUG: Saved raw HTML to {debug_path}")
        
    except requests.RequestException as e:
        print(f"Error: Could not fetch webpage. {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    if not table:
        print("Error: Could not find table on the webpage.")
        return

    # 3. Iterate through table rows
    rows = table.find_all('tr')
    print(f"Found {len(rows)} rows in table. Checking for new journals...")
    
    new_journals_found = 0
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) < 2:
            continue
        
        journal_serial = cols[1].text.strip() # "Journal No." is in the second column
        
        if not utils.parse_serial(journal_serial):
            continue
            
        # --- MODIFICATION: Use database-safe ID ---
        # Convert '45/2025' to '45_2025' for filenames and DB key
        journal_db_id = journal_serial.replace('/', '_')
            
        # 4. Check against Baseline and History
        
        # Check 1: If journal is older than our baseline, stop.
        comparison = utils.compare_serials(journal_serial, config.DOWNLOADER_BASELINE_SERIAL)
        if comparison is not None and comparison < 0:
            print(f"Reached baseline serial ({config.DOWNLOADER_BASELINE_SERIAL}). Stopping.")
            break
        
        # Check 2: If we already downloaded this, skip.
        # This now checks against the set from the database.
        if journal_db_id in download_history:
            continue
            
        print(f"Found new journal: {journal_serial}. Processing...")
        new_journals_found += 1
        
        # 5. Find and Download PDFs
        download_col = cols[-1]
        download_forms = download_col.find_all('form')
        
        part_i_filename = None
        part_ii_filename = None
        
        for form in download_forms:
            button = form.find('button')
            if not button:
                continue
            
            text = button.get_text(" ", strip=True).lower()
            filename_input = form.find('input', {'type': 'hidden', 'name': 'FileName'})
            
            if not filename_input:
                continue
                
            filename_value = filename_input.get('value', '')
            
            # Strict Exact matching
            if text == 'part i' or text == 'part 1':
                part_i_filename = filename_value
            elif text == 'part ii' or text == 'part 2':
                part_ii_filename = filename_value
        
        # --- MODIFICATION: Store the returned file paths ---
        part_i_path = None
        part_ii_path = None
        
        # Download Part I
        if part_i_filename:
            part_i_path = _download_pdf(journal_db_id, "Part_I", part_i_filename)
        
        # Download Part II
        if part_ii_filename:
            part_ii_path = _download_pdf(journal_db_id, "Part_II", part_ii_filename)
            
        # 6. Save to history
        # --- MODIFICATION: Log to database instead of JSON ---
        database.log_journal(journal_db_id, part_i_path, part_ii_path)
        
        # Add to our local set to avoid re-downloading in this same session
        download_history.add(journal_db_id) 
        print(f"  Saved {journal_serial} (ID: {journal_db_id}) to database.")

    print(f"\nDownloader finished. Found {new_journals_found} new journals.")


def _download_pdf(journal_db_id, part_name, form_filename):
    """
    Helper function to download a single PDF via POST request.
    
    --- MODIFICATION: Returns the Path object on success, None on failure. ---
    """
    try:
        POST_URL = 'https://search.ipindia.gov.in/IPOJournal/Journal/ViewJournal'
        pdf_response = requests.post(
            POST_URL,
            data={'FileName': form_filename},
            timeout=60,
            stream=True
        )
        pdf_response.raise_for_status()
        
        # Save to 'data/raw_pdfs/44_2025_Part_I.pdf'
        pdf_filename = f"{journal_db_id}_{part_name}.pdf"
        pdf_path = config.RAW_PDF_DIR / pdf_filename
        
        with open(pdf_path, 'wb') as pdf_file:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_file.write(chunk)
        print(f"  ✓ Downloaded {pdf_filename}")
        
        # Return the path to be logged in the database
        return pdf_path 
        
    except requests.RequestException as e:
        print(f"  ✗ Error downloading {part_name}: {e}")
        return None # Return None on failure

if __name__ == '__main__':
    # This allows the script to be run directly for testing
    run_downloader()