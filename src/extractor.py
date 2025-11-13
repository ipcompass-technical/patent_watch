import fitz  # PyMuPDF
import re
import json

# Import configuration
import config

def run_extractor():
    """
    Extracts structured data from all PDFs in the raw_pdfs folder
    and saves it to all_patents.json.
    """
    print("--- Running Extractor ---")
    
    # 1. Define the master Regex
    # This regex uses 'named groups' (?P<name>...) to extract data
    # re.DOTALL means '.' will match newlines, which is crucial for
    # multi-line fields like 'abstract'.
    patent_regex = re.compile(
        r"\(12\)\s*PATENT APPLICATION PUBLICATION"
        r".*?\(21\)\s*Application No\.:\s*(?P<app_no>.*?)\n"
        r".*?\(22\)\s*Date of filing of Application\s*:\s*(?P<date_filing>.*?)\n"
        r".*?\(43\)\s*Publication Date\s*:\s*(?P<date_pub>.*?)\n"
        r".*?\(54\)\s*Title of the invention\s*:\s*(?P<title>.*?)\n"
        r".*?\(51\)\s*International classification\s*:\s*(?P<ipc>.*?)\n"
        r".*?\(71\)Name of Applicant\s*:\s*(?P<applicant>.*?)\n"
        r".*?\(72\)Name of Inventor\s*:\s*(?P<inventor>.*?)\n"
        r".*?\(57\)\s*Abstract\s*:\s*(?P<abstract>.*?)\n"
        r"(?=No\. of Pages|Description:)",  # Positive lookahead (ends match here)
        re.DOTALL
    )

    all_patents = []
    pdf_files = list(config.RAW_PDF_DIR.glob('*.pdf'))
    print(f"Found {len(pdf_files)} PDF files to process...")

    # 2. Loop through all PDF files
    for pdf_path in pdf_files:
        print(f"Processing {pdf_path.name}...")
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            
            # 3. Find all matches in the full text
            for match in patent_regex.finditer(full_text):
                data = match.groupdict()
                
                # Clean up the extracted data
                cleaned_data = {
                    "application_no": data['app_no'].strip(),
                    "date_of_filing": data['date_filing'].strip(),
                    "publication_date": data['date_pub'].strip(),
                    "title": data['title'].strip().replace('\n', ' '),
                    "international_classification": data['ipc'].strip().replace('\n', ' '),
                    "applicant": data['applicant'].strip().replace('\n', ' '),
                    "inventor": data['inventor'].strip().replace('\n', ' '),
                    "abstract": data['abstract'].strip().replace('\n', ' '),
                }
                all_patents.append(cleaned_data)
                
            print(f"  Found {len(list(patent_regex.finditer(full_text)))} patents.")
                
        except Exception as e:
            print(f"  Error processing {pdf_path.name}: {e}")
            
    # 4. Save results
    print(f"\nExtraction complete. Total patents found: {len(all_patents)}")
    utils.save_json_history(config.ALL_PATENTS_JSON, all_patents)
    print(f"All patents saved to {config.ALL_PATENTS_JSON}")

if __name__ == '__main__':
    run_extractor()