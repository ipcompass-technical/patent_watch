import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Import configuration and utilities from our own package
from . import utils
import config

def run_downloader():
    """
    Finds and downloads new patent journals (Parts I & II) that are
    not listed in the download history.
    """
    print("--- Running Downloader ---")
    
    # 1. Setup
    # Ensure directories exist
    config.RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load download history from data/output/download_history.json
    download_history = utils.load_json_history(config.HISTORY_FILE)
    print(f"Loaded {len(download_history)} journals from history.")
    
    # 2. Fetch the webpage
    print(f"Fetching webpage: {config.DOWNLOADER_BASE_URL}")
    try:
        response = requests.get(
            config.DOWNLOADER_BASE_URL, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response.raise_for_status()
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
            
        # 4. Check against Baseline and History
        
        # Check 1: If journal is older than our baseline, stop.
        comparison = utils.compare_serials(journal_serial, config.DOWNLOADER_BASELINE_SERIAL)
        if comparison is not None and comparison < 0:
            print(f"Reached baseline serial ({config.DOWNLOADER_BASELINE_SERIAL}). Stopping.")
            break
        
        # Check 2: If we already downloaded this, skip.
        if journal_serial in download_history:
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
        
        # Download Part I
        if part_i_filename:
            _download_pdf(journal_serial, "Part_I", part_i_filename)
        
        # Download Part II
        if part_ii_filename:
            _download_pdf(journal_serial, "Part_II", part_ii_filename)
            
        # 6. Save to history
        download_history.append(journal_serial)
        utils.save_json_history(config.HISTORY_FILE, download_history)
        print(f"  Saved {journal_serial} to history.")

    print(f"\nDownloader finished. Found {new_journals_found} new journals.")

def _download_pdf(journal_serial, part_name, form_filename):
    """Helper function to download a single PDF via POST request."""
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
        safe_serial = journal_serial.replace('/', '_')
        pdf_filename = f"{safe_serial}_{part_name}.pdf"
        pdf_path = config.RAW_PDF_DIR / pdf_filename
        
        with open(pdf_path, 'wb') as pdf_file:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_file.write(chunk)
        print(f"  ✓ Downloaded {pdf_filename}")
        
    except requests.RequestException as e:
        print(f"  ✗ Error downloading {part_name}: {e}")

if __name__ == '__main__':
    # This allows the script to be run directly for testing
    run_downloader()