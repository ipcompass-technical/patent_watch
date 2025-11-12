- # Patent Watch - Data Pipeline
  
This project is a set of Python scripts that form a data pipeline to download, filter, and retrieve specific documents for Indian patent applications.  
- ## Prerequisites
- Python 3.x
- pip (Python package installer)
- ## Installation
- Clone or download this project.
- Install the required Python libraries using the `requirements.txt` file:
  
  ```
  pip install -r requirements.txt
  ```
- ## How to Run
  
  The pipeline is a series of scripts that must be run in order.  
- ### Step 1: Download New Journals
  
  This script finds all new patent journals from the official website (that are not in your history) and downloads them as PDFs.  
  
  ```
  python downloader.py
  ```
- **Output:** New PDF files are saved in the `raw_pdfs/` directory.
- **Note:** This script is "stateful." It remembers what it downloaded in `download_history.json`. To re-download, delete that file.
- ### Step 2: Extract PDF Data
  
  This script reads all PDFs from `raw_pdfs/`, extracts all patent data, and saves it to a single JSON file.  
  
  ```
  python extract.py
  ```
- **Output:** Creates `all_patents.json` containing raw data for *all* patents.
- ### Step 3: Filter for Software Patents
  
  This script reads `all_patents.json` and creates a new, clean list containing only patents that are classified as "Software" or "Hybrid" (based on their IPC codes).  
  
  ```
  python filter.py
  ```
- **Output:** Creates `classified_patents.json`.
- ### Step 4: Retrieve Specific Patent Documents
  
  This is a "human-in-the-loop" script that takes a single patent, bypasses the CAPTCHA with your help, and navigates the complex search website to download all associated documents.  
  
  ```
  python search_requests.py
  ```
- **Input:** It will ask you to open `captcha.jpg` and enter the text.
- **Output:**
	- `application_details.html` (The patent's main detail page)
	- `application_status.html` (The *real* status page, after bypassing a redirect)
	- `view_documents.html` (The final page listing all downloadable documents)
