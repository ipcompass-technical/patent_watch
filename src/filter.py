import json
import re

# Import configuration and utilities
import config
from . import utils
from . import database # Import the database module

def run_filter():
    """
    Loads all 'newly_extracted' patents from the database,
    classifies them based on IPC codes, and updates them in place.
    """
    print("--- Running Filter ---")
    
    # Define software IPC codes
    SOFTWARE_PREFIXES = ['G06', 'H04L', 'G16H', 'G05B']
    
    # 1. Load patents from DATABASE, not JSON
    patents_to_classify = database.get_patents_to_classify()
    
    if not patents_to_classify:
        print("No new patents to classify. Exiting.")
        return

    print(f"Loaded {len(patents_to_classify)} unclassified patents from database.")
    
    classified_counts = {
        "Software": 0,
        "Hybrid": 0,
        "Non-Software": 0,
        "Unknown": 0
    }
    
    # 2. Loop and classify
    for patent in patents_to_classify:
        # Get data from the database row
        ipc_string = patent["ipc_codes"] or ""
        
        # -----------------------------------------------------------------
        # --- THIS IS THE BUG FIX ---
        # -----------------------------------------------------------------
        # We must split ONLY on commas, not on spaces.
        # old: ipc_codes = [code.strip() for code in re.split(r'[,\s]+', ipc_string) if code]
        ipc_codes_raw = ipc_string.split(',')
        ipc_codes = [code.strip() for code in ipc_codes_raw if code.strip()]
        # -----------------------------------------------------------------
        
        if not ipc_codes:
            patent_type = 'Unknown'
        else:
            software_count = 0
            other_count = 0
            
            for code in ipc_codes:
                if any(code.startswith(prefix) for prefix in SOFTWARE_PREFIXES):
                    software_count += 1
                else:
                    other_count += 1
            
            # 3. Assign type
            if software_count > 0 and other_count > 0:
                patent_type = 'Hybrid'
            elif software_count > 0 and other_count == 0:
                patent_type = 'Software'
            else:
                patent_type = 'Non-Software'
        
        # 4. Update the database
        app_no = patent["application_no"]
        database.update_patent_classification(app_no, patent_type, ipc_codes)
        
        # Update our local counter
        classified_counts[patent_type] += 1

    # 5. Print summary
    print("\n--- Filtering complete ---")
    print(f"  ✓ Classified {classified_counts['Software']} as 'Software'")
    print(f"  ✓ Classified {classified_counts['Hybrid']} as 'Hybrid'")
    print(f"  ✓ Classified {classified_counts['Non-Software']} as 'Non-Software'")
    print(f"  ✓ Classified {classified_counts['Unknown']} as 'Unknown'")
    print(f"Total patents updated in database: {len(patents_to_classify)}")

if __name__ == '__main__':
    # This check is still useful for direct testing
    run_filter()