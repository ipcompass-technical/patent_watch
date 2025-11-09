import fitz  # PyMuPDF
import re
import json

# Open the PDF file
pdf_document = fitz.open("sample.pdf")

# Extract text from all pages
all_text = ""
for page_num in range(len(pdf_document)):
    page = pdf_document[page_num]
    all_text += page.get_text()

# Close the document
pdf_document.close()

# Split the text by patent delimiter
patent_pattern = r'\(12\) PATENT APPLICATION PUBLICATION'
patents = re.split(patent_pattern, all_text)

# Remove the first empty element (text before first patent)
patents = patents[1:]

all_patents = []

for patent_text in patents:
    patent = {}
    
    # Extract Application No (21)
    app_no_match = re.search(r'\(21\)\s+Application No\.([^\n]+)', patent_text)
    if app_no_match:
        patent['application_no'] = app_no_match.group(1).strip()
    
    # Extract Title (54)
    title_match = re.search(r'\(54\)\s+Title of the invention\s*:(.+?)(?=\(51\))', patent_text, re.DOTALL)
    if title_match:
        patent['title'] = re.sub(r'\s+', ' ', title_match.group(1)).strip()
    
    # Extract International classification (51) - can span multiple lines
    class_match = re.search(r'\(51\)\s+International classification\s*\n\s*:(.+?)(?=\(31\))', patent_text, re.DOTALL)
    if class_match:
        patent['international_classification'] = re.sub(r'\s+', ' ', class_match.group(1)).strip()
    
    # Extract Name of Applicant (71)
    applicant_match = re.search(r'\(71\)Name of Applicant\s*:\s*(.+?)(?=\(72\))', patent_text, re.DOTALL)
    if applicant_match:
        patent['applicant'] = re.sub(r'\s+', ' ', applicant_match.group(1)).strip()
    
    # Extract Name of Inventor (72)
    inventor_match = re.search(r'\(72\)Name of Inventor\s*:\s*(.+?)(?=\(57\))', patent_text, re.DOTALL)
    if inventor_match:
        patent['inventor'] = re.sub(r'\s+', ' ', inventor_match.group(1)).strip()
    
    # Extract Abstract (57)
    abstract_match = re.search(r'\(57\)\s+Abstract\s*:\s*(.+?)(?=\n\n|$)', patent_text, re.DOTALL)
    if abstract_match:
        patent['abstract'] = re.sub(r'\s+', ' ', abstract_match.group(1)).strip()
    
    all_patents.append(patent)

# Save to JSON file
with open('all_patents.json', 'w', encoding='utf-8') as f:
    json.dump(all_patents, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(all_patents)} patents and saved to all_patents.json")
