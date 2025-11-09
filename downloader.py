import os
import json
import shutil
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# Constants
BASE_URL = 'https://search.ipindia.gov.in/IPOJournal/Journal/Patent'
DOWNLOAD_DIR = 'raw_pdfs'
HISTORY_FILE = 'download_history.json'
BASELINE_SERIAL = '44/2025'  # Format: week_number/year

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load download history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        download_history = json.load(f)
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

# Set up Selenium with headless Chromium
print("Setting up Chromium browser...")

# Set TMPDIR environment variable for Snap environments
os.environ['TMPDIR'] = os.getcwd()
print(f"Set TMPDIR to: {os.environ['TMPDIR']}")

# Try to find Chromium binary in common locations
chromium_paths = [
    shutil.which('chromium'),
    shutil.which('chromium-browser'),
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/snap/bin/chromium',
]

chromium_binary = None
for path in chromium_paths:
    if path and os.path.exists(path):
        chromium_binary = path
        print(f"Found Chromium at: {chromium_binary}")
        break

chrome_options = Options()
if chromium_binary:
    chrome_options.binary_location = chromium_binary
else:
    print("Warning: Chromium binary not found in common locations.")
    print("Attempting to use default Chromium installation...")

# Essential arguments for headless mode and Snap/Linux compatibility
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--remote-debugging-port=9222')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument('--window-size=1920,1080')

# Create a user data directory to avoid permission issues with Snap
user_data_dir = os.path.join(os.getcwd(), 'chromium_user_data')
os.makedirs(user_data_dir, exist_ok=True)
chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

# Use ChromeDriverManager to automatically set up the driver for Chromium
print("Setting up ChromeDriver for Chromium...")
service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Navigate to the webpage
    print(f"Navigating to: {BASE_URL}")
    driver.get(BASE_URL)
    
    # Wait explicitly for the actual content (Part I link) to be loaded and visible
    print("Waiting for page content to load (looking for 'Part I' link)...")
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT, 'Part I')))
        print("Content loaded successfully! Found visible 'Part I' link.")
    except Exception as e:
        print(f"Could not find visible 'Part I' link, trying alternative wait conditions...")
        try:
            wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT, 'Part-I')))
            print("Found visible 'Part-I' link.")
        except:
             # Final fallback to table wait
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                print("Table found, but links may not be loaded yet.")
            except:
                 print("Could not find table either.")

    
    # Add a small delay to ensure all JavaScript has finished executing
    time.sleep(2)
    print("Additional 2 second delay to ensure all content is fully rendered...")
    
    # Get the page source after JavaScript has rendered the content
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
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
        
        # Try to find the serial number (format: week/year) in any column
        journal_serial = None
        for col in cols:
            text = col.text.strip()
            if parse_serial(text):
                journal_serial = text
                break
        
        # If not found, try column 1 (Date of Publication) as fallback
        if not journal_serial and len(cols) > 1:
            journal_serial = cols[1].text.strip()
        
        # Parse the serial number
        if not parse_serial(journal_serial):
            # print(f"Warning: Could not parse serial number from row. Skipping.")
            continue
        
        print(f"Processing journal: {journal_serial}")
        
        # CRITICAL OPTIMIZATION: If journal serial is before BASELINE_SERIAL, BREAK
        comparison = compare_serials(journal_serial, BASELINE_SERIAL)
        if comparison is not None and comparison < 0:
            print(f"Reached baseline serial ({BASELINE_SERIAL}). Journal {journal_serial} is older. Stopping.")
            break
        
        # Use the serial number as the journal identifier
        journal_no = journal_serial
        
        # If Journal No. is already in download_history, CONTINUE (skip)
        if journal_no in download_history:
            print(f"Journal No. {journal_no} already downloaded. Skipping.")
            continue
        
        # Find download forms for Part I and Part II
        download_col = cols[-1]
        download_forms = download_col.find_all('form')
        
        if not download_forms:
             for i, col in enumerate(cols):
                forms = col.find_all('form')
                if forms:
                    download_forms.extend(forms)
        
        print(f"  Found {len(download_forms)} total form(s)")
        
        part_i_filename = None
        part_ii_filename = None
        
        # --- NEW STRICT MATCHING LOOP START ---
        for form in download_forms:
            button = form.find('button')
            if not button:
                continue
            
            # Clean the text: join multiple spaces, strip whitespace, convert to lower case
            # This turns "Part   IV " into "part iv"
            text = button.get_text(" ", strip=True).lower()
            
            filename_input = form.find('input', {'type': 'hidden', 'name': 'FileName'})
            if not filename_input:
                continue
            filename_value = filename_input.get('value', '')
            
            print(f"  Checking form button: '{text}'")

            # STRICT Exact matching to avoid "part iv" matching "part i"
            if text == 'part i' or text == 'part 1':
                part_i_filename = filename_value
                print(f"  ✓ EXACT MATCH: Part I found.")
            elif text == 'part ii' or text == 'part 2':
                part_ii_filename = filename_value
                print(f"  ✓ EXACT MATCH: Part II found.")
        # --- NEW STRICT MATCHING LOOP END ---
        
        if not part_i_filename and not part_ii_filename:
            print(f"  ✗ Warning: Could not find Part I or Part II forms.")
        
        # Download Part I and Part II PDFs using POST requests
        downloaded_parts = []
        POST_URL = 'https://search.ipindia.gov.in/IPOJournal/Journal/ViewJournal'
        
        if part_i_filename:
            try:
                print(f"Downloading Part I for Journal No. {journal_no}...")
                pdf_response = requests.post(
                    POST_URL, data={'FileName': part_i_filename}, timeout=300, stream=True
                )
                pdf_response.raise_for_status()
                
                # Fix filename by replacing slash with underscore
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
                    POST_URL, data={'FileName': part_ii_filename}, timeout=300, stream=True
                )
                pdf_response.raise_for_status()
                
                # Fix filename by replacing slash with underscore
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
        
        # Update history if successful
        if downloaded_parts:
            print(f"✓ Successfully downloaded {', '.join(downloaded_parts)} for Journal No. {journal_no}")
            download_history.append(journal_no)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(download_history, f, indent=2, ensure_ascii=False)
        else:
             print(f"✗ No PDFs downloaded for Journal No. {journal_no}")

finally:
    print("\nClosing browser...")
    driver.quit()

print(f"\nDownload process complete. Total journals in history: {len(download_history)}")