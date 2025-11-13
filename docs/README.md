# Patent Watch - Data Pipeline

This project is a set of Python scripts that form a data pipeline to download, filter, and retrieve specific documents for Indian patent applications.

All scripts are run using the central `main.py` control script.

## Prerequisites

-   Python 3.x
    
-   pip (Python package installer)
    

## Installation

1.  Clone or download this project.
    
2.  Install the required Python libraries using the `requirements.txt` file:
    
    ```
    pip install -r requirements.txt
    
    ```
    

## How to Run

All commands must be run from the main `patent_watch/` root directory.

### To Run a Specific Step:

Use `python main.py [command]`

-   **Download new journals:**
    
    ```
    python main.py download
    
    ```
    
-   **Extract data from PDFs:**
    
    ```
    python main.py extract
    
    ```
    
-   **Filter for software patents:**
    
    ```
    python main.py filter
    
    ```
    

### To Run the Full Pipeline:

This command will run the download, extract, and filter steps all in one go.

```
python main.py all

```

### To Retrieve Specific Documents:

This is the "human-in-the-loop" search script. You can run it in two ways:

1.  **Test Mode (uses default test data):**
    
    ```
    python main.py search
    
    ```
    
2.  **Live Mode (searches for a specific patent):**
    
    ```
    python main.py search "202511087359 A"
    
    ```
