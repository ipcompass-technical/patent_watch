import fitz  # PyMuPDF
import re
import json

# Import configuration and our new database functions
import config
from . import utils
from . import database

def _process_pdf(pdf_path, pub_type, patent_regex):
    """
    Helper function to process a single PDF file page by page.
    """
    patents_found = 0
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  ✗ ERROR: Could not open {pdf_path}. Skipping. Error: {e}")
        return 0
        
    print(f"  Processing {doc.page_count} pages from {pdf_path.name}...")
    
    for page_num, page in enumerate(doc, start=1):
        try:
            page_text = page.get_text() + "\n"
            
            # Run the regex on this single page's text
            match = patent_regex.search(page_text)
            
            if match:
                data = match.groupdict()
                
                # Clean up the extracted data
                # We .strip() EVERY field to remove unwanted whitespace
                cleaned_data = {
                    "application_no": data['app_no'].strip(),
                    "date_of_filing": data['date_filing'].strip(),
                    "publication_date": data['date_pub'].strip(),
                    "title": data['title'].strip().replace('\n', ' '),
                    # Use .get() for optional 'ipc' group, default to empty string
                    "international_classification": data.get('ipc', '').strip().replace('\n', ' '),
                    "applicant": data['applicant'].strip().replace('\n', ' '),
                    "inventor": data['inventor'].strip().replace('\n', ' '),
                    "abstract": data['abstract'].strip().replace('\n', ' '),
                    "publication_type": pub_type
                }
                
                database.insert_patent(cleaned_data)
                patents_found += 1
            else:
                # Fluff page, skip
                pass 
                
        except Exception as e:
            print(f"    - Error processing page {page_num}: {e}")
            
    doc.close()
    print(f"  ✓ Found {patents_found} patents in {pdf_path.name}.")
    return patents_found

def run_extractor():
    """
    Extracts structured data from all PDFs in the 'journals' table
    that have a status of 'downloaded'.
    """
    print("--- Running Extractor ---")
    
    # -----------------------------------------------------------------
    # --- THIS IS THE FINAL, ROBUST REGEX ---
    # -----------------------------------------------------------------
    # It uses complex "lookaheads" (?=...) to stop capturing
    # at the *next nearest* field code, even if it's optional.
    # -----------------------------------------------------------------
    patent_regex = re.compile(
        r"\(12\)\s*PATENT APPLICATION PUBLICATION"
        
        # (21) Application No. - Stop at (19) or (22)
        r".*?\(21\)\s*Application No\.:?\s*(?P<app_no>.*?)(?=\s*\((?:19|22)\))"
        
        # (22) Date of filing - Stop at (43)
        r".*?\(22\)\s*Date of filing of Application\s*:?\s*(?P<date_filing>.*?)(?=\s*\((?:43)\))"
        
        # (43) Publication Date - Stop at (54)
        r".*?\(43\)\s*Publication Date\s*:?\s*(?P<date_pub>.*?)(?=\s*\((?:54)\))"
        
        # (54) Title - Stop at (51) or (71) (in case 51 is missing)
        r".*?\(54\)\s*Title of the invention\s*:?\s*(?P<title>.*?)(?=\s*\((?:51|71)\))"
        
        # (51) IPC - This is an optional group.
        # It captures everything until the *next* field code, which could be
        # (31), (32), (33), (86), (87), (61), (62), or (71).
        # We make the whole (51) block optional with (?:...)?
        r"(?:"
            r".*?\(51\)\s*International classification\s*:?\s*(?P<ipc>.*?)"
            r"(?=\s*\((?:31|32|33|86|87|61|62|71)\))"
        r")?"
        
        # (71) Applicant - Stop at (72)
        r".*?\(71\)\s*Name of Applicant\s*:?\s*(?P<applicant>.*?)(?=\s*\((?:72)\))"
        
        # (72) Inventor - Stop at (57)
        r".*?\(72\)\s*Name of Inventor\s*:?\s*(?P<inventor>.*?)(?=\s*\((?:57)\))"
        
        # (57) Abstract - Stop at "No. of Pages" or "Description"
        r".*?\(57\)\s*Abstract\s*:?\s*(?P<abstract>.*?)"
        r"(?=No\. of Pages|Description:)",
        
        re.DOTALL | re.IGNORECASE
    )
    # -----------------------------------------------------------------
    # --- END OF UPDATED REGEX ---
    # -----------------------------------------------------------------

    # Get the "to-do list" from the database
    journals_to_process = database.get_journals_to_process()
    if not journals_to_process:
        print("No new journals to extract. Exiting.")
        return

    print(f"Found {len(journals_to_process)} journals to process...")
    total_patents_found = 0

    # Loop through each journal
    for journal in journals_to_process:
        journal_id = journal['journal_id']
        print(f"\nProcessing journal: {journal_id}")
        
        database.update_journal_status(journal_id, "extracting")
        
        journal_patents = 0
        
        try:
            # Process Part I
            if journal['part1_pdf_path']:
                pdf_path = config.BASE_DIR / journal['part1_pdf_path']
                journal_patents += _process_pdf(pdf_path, "PART_I_EARLY", patent_regex)
            
            # Process Part II
            if journal['part2_pdf_path']:
                pdf_path = config.BASE_DIR / journal['part2_pdf_path']
                journal_patents += _process_pdf(pdf_path, "PART_II_NORMAL", patent_regex)
            
            database.update_journal_status(journal_id, "extracted")
            print(f"✓ Finished journal {journal_id}. Found {journal_patents} patents.")
            total_patents_found += journal_patents
            
        except Exception as e:
            print(f"  ✗✗✗ CRITICAL ERROR processing {journal_id}: {e}")
            database.update_journal_status(journal_id, "error_extracting")
            
    print(f"\n--- Extraction complete. ---")
    print(f"Total new patents saved to database: {total_patents_found}")

if __name__ == '__main__':
    run_extractor()