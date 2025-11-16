# -----------------------------------------------------------------
# MAIN.PY (Pipeline Runner)
# -----------------------------------------------------------------
# This is the main entry point for the entire application.
#
# To run a specific step:
#   python main.py download
#   python main.py extract
#   python main.py filter
#   python main.py search [application_number]
#
# -----------------------------------------------------------------

import sys
# Add this import
from src import database, downloader, extractor, filter, searcher

def main():
    """
    Parses command-line arguments to run the correct
    part of the pipeline.
    """
    # Get the command (e.g., 'download') from the user
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == 'download':
        downloader.run_downloader()
        
    elif command == 'extract':
        extractor.run_extractor()
        
    elif command == 'filter':
        filter.run_filter()
        
    elif command == 'search':
        app_no = None
        if len(sys.argv) > 2:
            app_no = sys.argv[2]
            print(f"Search target: {app_no}")
        else:
            print("No application number provided. Running search with default test data.")
        searcher.run_searcher(app_no)
        
    elif command == 'all':
        print("--- Running Full Pipeline (Download, Extract, Filter) ---")
        downloader.run_downloader()
        extractor.run_extractor()
        filter.run_filter()
        print("\nFull pipeline complete.")

    elif command == 'init':
        print("--- Initializing Database ---")
        # Check the return value
        if database.create_tables():
            print("\nDatabase initialized successfully.")
        else:
            print("\nDatabase initialization FAILED.")
        
    else:
        print(f"Unknown command: '{command}'")
        print_help()

def print_help():
    print("\n--- Patent Watch Pipeline ---")
    print("Usage: python main.py [command]")
    print("\nAvailable Commands:")
    print("  download    - Download new journals from the website.")
    print("  extract     - Extract patent data from downloaded PDFs.")
    print("  filter      - Filter all patents for software/hybrid ones.")
    print("  search [app] - Run the 'human-in-the-loop' search for a")
    print("                 specific application number (e.g., '202511087359 A')")
    print("                 (If no app number is given, runs in test mode).")
    print("  all         - Run the full download, extract, and filter pipeline.")
    print("  init        - Initialize the database.")

if __name__ == "__main__":
    main()