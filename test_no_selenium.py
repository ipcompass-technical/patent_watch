import requests
from bs4 import BeautifulSoup

# The same URL
BASE_URL = 'https://search.ipindia.gov.in/IPOJournal/Journal/Patent'

print(f"Fetching {BASE_URL} using 'requests' (no Selenium)...")

try:
    # Use requests to get the RAW HTML, before JavaScript runs
    response = requests.get(BASE_URL, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # --- THIS IS THE TEST ---
    # We will search for the <form> tag and the "FileName" input
    
    # Test 1: Find all <form> tags
    forms = soup.find_all('form')
    print(f"\nFound {len(forms)} total <form> tags on the page.")
    
    # Test 2: Find the specific "FileName" input
    filename_inputs = soup.find_all('input', {'name': 'FileName'})
    print(f"Found {len(filename_inputs)} hidden 'FileName' inputs.")
    
    if not filename_inputs:
        print("\n--- TEST FAILED ---")
        print("As you can see, the 'FileName' inputs are NOT in the raw HTML.")
        print("This proves they are added by JavaScript, and Selenium is required.")
    else:
        print("\n--- TEST PASSED ---")
        print("Wow, you were right! The forms are in the raw HTML.")

except requests.exceptions.RequestException as e:
    print(f"Error fetching page: {e}")