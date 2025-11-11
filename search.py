import os
import json
import time
import shutil
from datetime import datetime  # <-- Import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# --- Your Sample Data (for this prototype) ---
patent_data = {
    "application_no": "202511087359 A",
    "date_of_filing": "15/09/2025",
    "publication_date": "24/10/2025",
    "title": "TALENT ACQUISITION AND EMPLOYEE RECRUITMENT SYSTEM",
    # ... other data
}

# --- Data Cleaning ---
# Remove the " A" from the application number
app_number_clean = patent_data["application_no"].split(' ')[0]

# --- NEW: Date Formatting ---
# 1. Parse the date from DD/MM/YYYY format
original_date_str = patent_data["date_of_filing"]
date_obj = datetime.strptime(original_date_str, "%d/%m/%Y")
# 2. Re-format it to MM/DD/YYYY for the website
app_date_formatted = date_obj.strftime("%m/%d/%Y")


print(f"--- Prototyping Search ---")
print(f"Target URL: https://iprsearch.ipindia.gov.in/PublicSearch/")
print(f"Original Date: {original_date_str}")
print(f"Formatted Date (MM/DD/YYYY): {app_date_formatted}")
print(f"App No: {app_number_clean}")
print("---------------------------\n")

# --- Set up Selenium (Visible, not headless) ---
print("Setting up Chromium browser...")

# Set TMPDIR environment variable
os.environ['TMPDIR'] = os.getcwd()

# Find Chromium binary
chromium_paths = [
    shutil.which('chromium'),
    shutil.which('chromium-browser'),
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/snap/bin/chromium',
]
chromium_binary = next((path for path in chromium_paths if path and os.path.exists(path)), None)

chrome_options = Options()
if chromium_binary:
    chrome_options.binary_location = chromium_binary
    print(f"Found Chromium at: {chromium_binary}")
else:
    print("Warning: Chromium binary not found. Using default Chrome/Chromium.")

# We MUST run in visible mode to see the CAPTCHA
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--remote-debugging-port=9222')

# Create a user data directory
user_data_dir = os.path.join(os.getcwd(), 'chromium_user_data')
os.makedirs(user_data_dir, exist_ok=True)
chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

print("Setting up ChromeDriver...")
service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Navigate to the webpage
    driver.get('https://iprsearch.ipindia.gov.in/PublicSearch/')
    wait = WebDriverWait(driver, 20)
    print("Page loaded. Filling form...")

    # --- Step 1: Fill First Row (Application Date) ---
    
    print("Waiting for date fields...")
    # Fill From Date (Using 'name' attribute and *formatted* date)
    from_date_input = wait.until(EC.presence_of_element_located((By.NAME, 'FromDate')))
    from_date_input.send_keys(app_date_formatted)
    print(f"Filled From Date: {app_date_formatted}")

    # Fill To Date (Using 'name' attribute and *formatted* date)
    to_date_input = driver.find_element(By.NAME, 'ToDate')
    to_date_input.send_keys(app_date_formatted)
    print(f"Filled To Date: {app_date_formatted}")

    # --- Step 2: NO "Add" button click ---
    # We are now proceeding based on your correct observation.
    
    # --- Step 3: Fill Second Row (Application Number) ---
    
    # Define the *exact* XPaths we need
    # This is the XPath you provided for the dropdown
    SECOND_DROPDOWN_XPATH = "/html/body/div[1]/div[2]/div/div[4]/form/section/div/div/div/div/div[3]/div/div[1]/select"
    # This is the relative XPath for the text field next to it
    SECOND_TEXTFIELD_XPATH = "/html/body/div[1]/div[2]/div/div[4]/form/section/div/div/div/div/div[3]/div/div[2]/input"

    print("Waiting for second search row dropdown (using full XPath)...")
    
    # Wait for the dropdown to be present
    select_field2_element = wait.until(
        EC.presence_of_element_located((By.XPATH, SECOND_DROPDOWN_XPATH))
    )
    
    # Now it is safe to access the second dropdown
    select_field2 = Select(select_field2_element)
    
    # Use your new, more reliable select_by_value
    select_field2.select_by_value('AP') 
    print("Selected 'Application Number' in second row (using value 'AP').")
    
    # Find the text field using its specific XPath
    app_num_input = driver.find_element(By.XPATH, SECOND_TEXTFIELD_XPATH)
    app_num_input.send_keys(app_number_clean)
    print(f"Filled App Number: {app_number_clean}")

    # --- Step 4: Human-in-the-Loop (CAPTCHA) ---
    # This is the new, more robust workflow.
    print("\n" + "="*40)
    print("   !!! ACTION REQUIRED !!!")
    print("The form is filled. Please solve the CAPTCHA in the browser,")
    print("then type the text below and press Enter.")
    print("="*40)
    
    # Use standard Python input() to pause the script
    captcha_text = input("Enter CAPTCHA text here: ")

    # --- Step 5: Submit ---
    # NOW we find the elements and submit, all at once.
    # This prevents the CAPTCHA from expiring while we wait.
    print(f"Submitting with CAPTCHA: {captcha_text}...")
    
    # Find CAPTCHA input field (FIXED: Using correct case 'CaptchaText')
    captcha_input = driver.find_element(By.ID, 'CaptchaText')
    captcha_input.send_keys(captcha_text)
    
    # Find and click the "Search" button
    search_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Search']")
    search_button.click()

    # --- Step 6: Wait to see results ---
    print("\nSearch submitted! Keeping browser open for 30 seconds to view results...")
    time.sleep(30)
    print("Prototype script finished.")

finally:
    # Close the browser
    print("Closing browser.")
    driver.quit()