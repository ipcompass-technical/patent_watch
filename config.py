# -----------------------------------------------------------------
# CONFIGURATION FILE
# All "magic numbers," URLs, and file paths are stored here.
# -----------------------------------------------------------------
from pathlib import Path

# --- Project Root ---
# This finds the root folder of your project, so all paths work
# from anywhere.
BASE_DIR = Path(__file__).resolve().parent

# --- Data Folders ---
DATA_DIR = BASE_DIR / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
OUTPUT_DIR = DATA_DIR / "output"

# --- File Paths ---
# 'data/output/download_history.json'
HISTORY_FILE = OUTPUT_DIR / "download_history.json"
# 'data/output/all_patents.json'
ALL_PATENTS_JSON = OUTPUT_DIR / "all_patents.json"
# 'data/output/classified_patents.json'
CLASSIFIED_PATENTS_JSON = OUTPUT_DIR / "classified_patents.json"
# 'data/output/captcha.jpg'
CAPTCHA_IMAGE_FILE = OUTPUT_DIR / "captcha.jpg"
# 'data/output/results.html'
RESULTS_HTML = OUTPUT_DIR / "results.html"
# 'data/output/error.html'
ERROR_HTML = OUTPUT_DIR / "error.html"
# 'data/output/application_details.html'
DETAILS_HTML = OUTPUT_DIR / "application_details.html"
# 'data/output/application_status.html'
STATUS_HTML = OUTPUT_DIR / "application_status.html"
# 'data/output/view_documents.html'
DOCUMENTS_HTML = OUTPUT_DIR / "view_documents.html"
# 'data/output/real_status_page.html'
REAL_STATUS_HTML = OUTPUT_DIR / "real_status_page.html"


# --- Downloader Settings ---
DOWNLOADER_BASE_URL = 'https.ipindia.gov.in/IPOJournal/Journal/Patent'
# Don't download journals older than '44/2025'
DOWNLOADER_BASELINE_SERIAL = '44/2025'

# --- Searcher Settings ---
SEARCH_BASE_URL = "https.ipindia.gov.in/PublicSearch/"
SEARCH_POST_URL = "https.ipindia.gov.in/PublicSearch/PublicationSearch/Search"

# User-Agent to mimic a real browser
REQUESTS_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': SEARCH_BASE_URL
}