import json

# Import configuration and utilities
import config
from . import utils

def run_filter():
    """
    Loads all_patents.json and filters it to find software-related
    patents, saving the result to classified_patents.json.
    """
    print("--- Running Filter ---")
    
    # Define software IPC codes
    SOFTWARE_PREFIXES = ['G06', 'H04L', 'G16H', 'G05B']
    
    # 1. Load the master patent list
    all_patents = utils.load_json_history(config.ALL_PATENTS_JSON)
    if not all_patents:
        print("Error: `all_patents.json` is empty. Run the extractor first.")
        return

    print(f"Loaded {len(all_patents)} patents from master list.")
    classified_patents = []
    
    # 2. Loop and classify
    for patent in all_patents:
        ipc_string = patent.get("international_classification", "")
        # Clean up the IPC string, split by comma or space
        ipc_codes = [code.strip() for code in re.split(r'[,\s]+', ipc_string) if code]
        
        if not ipc_codes:
            patent['patent_type'] = 'Unknown'
            continue

        software_count = 0
        other_count = 0
        
        for code in ipc_codes:
            if any(code.startswith(prefix) for prefix in SOFTWARE_PREFIXES):
                software_count += 1
            else:
                other_count += 1
        
        # 3. Assign type
        if software_count > 0 and other_count > 0:
            patent['patent_type'] = 'Hybrid'
        elif software_count > 0 and other_count == 0:
            patent['patent_type'] = 'Software'
        else:
            patent['patent_type'] = 'Non-Software'
            
        patent['ipc_codes'] = ipc_codes
        
        # Only save software-related patents
        if patent['patent_type'] in ['Software', 'Hybrid']:
            classified_patents.append(patent)

    # 4. Save results
    print(f"Filtering complete. Found {len(classified_patents)} software/hybrid patents.")
    utils.save_json_history(config.CLASSIFIED_PATENTS_JSON, classified_patents)
    print(f"Classified patents saved to {config.CLASSIFIED_PATENTS_JSON}")

if __name__ == '__main__':
    # Need to import 're' for standalone execution
    import re
    run_filter()