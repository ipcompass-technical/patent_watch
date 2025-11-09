import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# Constants
BASE_URL = 'https://search.ipindia.gov.in/IPOJournal/Journal/Patent'
DOWNLOAD_DIR = 'raw_pdfs'
HISTORY_FILE = 'download_history.json'

# --- YOUR BASELINE ---
# We will not download anything *before* this date.
# Set to '44/2025' which corresponds to 31/10/2025
BASELINE_SERIAL = '44/2025'

# --- NO SELENIUM NEEDED ---

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load download history (with safety check)
if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            download_history = json.load(f)
            # Ensure it's a list, not some other JSON type
            if not isinstance(download_history, list):
                print(f"Warning: History file '{HISTORY_FILE}' did not contain a list. Resetting.")
                download_history = []
    except json.JSONDecodeError:
        # This happens if the file is empty or corrupted
        print(f"Warning: History file '{HISTORY_FILE}' was empty or corrupted. Resetting.")
        download_history = []
else:
    download_history = []

print(f"Loaded {len(download_history)} journals from history")

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

# --- THIS IS THE NEW, FAST WAY ---
print(f"Fetching {BASE_URL} with 'requests'...")
# Add a User-Agent header to disguise our script as a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    # Get the raw HTML
    response = requests.get(BASE_URL, headers=headers)
    response.raise_for_status()
    
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the table containing the journals
    table = soup.find('table')
    if not table:
        print("Error: Could not find table on the webpage")
        exit(1)
    
    # Iterate through table rows
    rows = table.find_all('tr')
    print(f"Found {len(rows)} rows in table")
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) < 2:
            continue
        
        # Try to find the serial number
        journal_serial = None
        # Column 1 (index 1) is "Journal No."
        if len(cols) > 1:
            text = cols[1].text.strip()
            if parse_serial(text):
                journal_serial = text

        if not journal_serial:
            # print("Warning: Could not find a valid serial in row. Skipping.")
            continue # Could not find a valid serial, skip row
        
        print(f"Processing journal: {journal_serial}")
        
        # CRITICAL OPTIMIZATION: If journal serial is before BASELINE_SERIAL, BREAK
        comparison = compare_serials(journal_serial, BASELINE_SERIAL)
        if comparison is not None and comparison < 0:
            print(f"Reached baseline serial ({BASELINE_SERIAL}). Journal {journal_serial} is older. Stopping.")
            break
        
        journal_no = journal_serial
        
        # If Journal No. is already in download_history, CONTINUE (skip)
        if journal_no in download_history:
            print(f"Journal No. {journal_no} already downloaded. Skipping.")
            continue
        
        # Find download forms
        download_col = cols[-1]  # Last column should be "Download"
        download_forms = download_col.find_all('form')
        
        print(f"  Found {len(download_forms)} total form(s)")
        
        part_i_filename = None
        part_ii_filename = None
        
        # --- STRICT MATCHING LOOP ---
        for form in download_forms:
            button = form.find('button')
            if not button:
                continue
            
            # Clean the text: join multiple spaces, strip whitespace, convert to lower case
            text = button.get_text(" ", strip=True).lower()
            
            filename_input = form.find('input', {'type': 'hidden', 'name': 'FileName'})
            if not filename_input:
                continue
            filename_value = filename_input.get('value', '')
            
            # STRICT Exact matching
            if text == 'part i' or text == 'part 1':
                part_i_filename = filename_value
                print(f"  ✓ EXACT MATCH: Part I found.")
            elif text == 'part ii' or text == 'part 2':
                part_ii_filename = filename_value
                print(f"  ✓ EXACT MATCH: Part II found.")
        
        # --- Download Logic (remains the same) ---
        downloaded_parts = []
        POST_URL = 'https://search.ipindia.gov.in/IPOJournal/Journal/ViewJournal'
        
        if part_i_filename:
            try:
                print(f"Downloading Part I for Journal No. {journal_no}...")
                pdf_response = requests.post(
                    POST_URL, 
                    data={'FileName': part_i_filename}, 
                    timeout=300, # 5-minute timeout for large files
                    stream=True,
                    headers=headers # Pass headers for the POST request too
                )
                pdf_response.raise_for_status()
                
                # Sanitize filename (replace '/' with '_')
                safe_journal_no = journal_no.replace('/', '_')
                pdf_filename = f"{safe_journal_no}_Part_I.pdf"
                pdf_path = os.path.join(DOWNLOAD_DIR, pdf_filename)
                
                with open(pdf_path, 'wb') as pdf_file:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        if chunk:
                            pdf_file.write(chunk)
                
                downloaded_parts.append("Part I")
                print(f"  ✓ Downloaded {pdf_filename}")
            except Exception as e:
                print(f"  ✗ Error downloading Part I: {e}")
        
        if part_ii_filename:
            try:
                print(f"Downloading Part II for Journal No. {journal_no}...")
                pdf_response = requests.post(
                    POST_URL, 
                    data={'FileName': part_ii_filename}, 
                    timeout=300, # 5-minute timeout for large files
                    stream=True,
                    headers=headers # Pass headers for the POST request too
                )
                pdf_response.raise_for_status()
                
                # Sanitize filename (replace '/' with '_')
                safe_journal_no = journal_no.replace('/', '_')
                pdf_filename = f"{safe_journal_no}_Part_II.pdf"
                pdf_path = os.path.join(DOWNLOAD_DIR, pdf_filename)
                
                with open(pdf_path, 'wb') as pdf_file:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        if chunk:
                            pdf_file.write(chunk)
                
                downloaded_parts.append("Part II")
                print(f"  ✓ Downloaded {pdf_filename}")
            except Exception as e:
                print(f"  ✗ Error downloading Part II: {e}")
        
        # Update history
        if downloaded_parts:
            print(f"✓ Successfully downloaded {', '.join(downloaded_parts)} for Journal No. {journal_no}")
            download_history.append(journal_no)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(download_history, f, indent=2, ensure_ascii=False)
        else:
            print(f"✗ No PDFs downloaded for Journal No. {journal_no}")

except requests.exceptions.RequestException as e:
    print(f"FATAL ERROR: Could not fetch webpage. {e}")
    print("Please check your internet connection or if the website is down.")

print(f"\nDownload process complete. Total journals in history: {len(download_history)}")