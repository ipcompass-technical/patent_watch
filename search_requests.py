import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# --- Your Sample Data (for this prototype) ---
patent_data = {
    "application_no": "202511087359 A",
    "date_of_filing": "15/09/2025",
    "publication_date": "24/10/2025",
    "title": "TALENT ACQUISITION AND EMPLOYEE RECRUITMENT SYSTEM",
    # ... other data
}

# --- Data Cleaning ---
app_number_clean = patent_data["application_no"].split(' ')[0]
original_date_str = patent_data["date_of_filing"]
date_obj = datetime.strptime(original_date_str, "%d/%m/%Y")
app_date_formatted = date_obj.strftime("%m/%d/%Y") # Convert to MM/DD/YYYY

# --- Setup ---
BASE_URL = "https://iprsearch.ipindia.gov.in/PublicSearch/"
# The form POSTS to a *different* URL than the one we GET
POST_URL = "https://iprsearch.ipindia.gov.in/PublicSearch/PublicationSearch/Search"
CAPTCHA_IMAGE_FILE = "captcha.jpg" # Will be overwritten each time

print(f"--- Prototyping Search (Requests-based) ---")
print(f"Date: {app_date_formatted} (MM/DD/YYYY)")
print(f"App No: {app_number_clean}")
print("-------------------------------------------\n")

# 1. Start a session to handle cookies
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    # We will need a Referer for all POSTs
    'Referer': BASE_URL 
})

# Suppress only the InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    # 2. GET Page (to get session cookies and find CAPTCHA)
    print(f"Connecting to {BASE_URL} to get session...")
    # Using verify=False to ignore potential SSL certificate issues on gov sites
    response = session.get(BASE_URL, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    print("Session started.")

    # 3. Find CAPTCHA Image
    captcha_img_tag = soup.find('img', {'id': 'Captcha'})
    if not captcha_img_tag:
        print("Error: Could not find CAPTCHA image tag with id='Captcha'.")
        exit()

    captcha_url_relative = captcha_img_tag['src']
    # Create absolute URL (e.g., /PublicSearch/Captcha... -> https://.../PublicSearch/Captcha...)
    captcha_url = urljoin(BASE_URL, captcha_url_relative)
    
    print(f"Found CAPTCHA image at: {captcha_url}")

    # 4. GET Image (using the same session)
    print(f"Downloading CAPTCHA image to {CAPTCHA_IMAGE_FILE}...")
    image_response = session.get(captcha_url, verify=False)
    image_response.raise_for_status()

    with open(CAPTCHA_IMAGE_FILE, 'wb') as f:
        f.write(image_response.content)
    print(f"Successfully saved {CAPTCHA_IMAGE_FILE}.")

    # 5. Pause (Human-in-the-Loop)
    print("\n" + "="*40)
    print("   !!! ACTION REQUIRED !!!")
    print(f"Please open the file '{CAPTCHA_IMAGE_FILE}' in your project folder.")
    print("Solve the CAPTCHA, then type the text below.")
    print("="*40)
    
    captcha_text = input("Enter CAPTCHA text here: ")

    # 6. Build Payload
    # This payload *exactly* matches your network log.
    form_payload = [
        # Checkboxes
        ('Published', 'true'),
        ('Published', 'false'),
        ('Granted', 'false'),
        
        # Row 1 (Date)
        ('DateField', 'APD'), 
        ('FromDate', app_date_formatted),
        ('ToDate', app_date_formatted),
        ('LogicField', 'AND'), 
        
        # Row 2 (Application Number)
        ('ItemField1', 'AP'),  
        ('TextField1', app_number_clean), 
        ('LogicField1', 'AND'), 
        
        # Captcha & Submit
        ('CaptchaText', captcha_text),
        ('submit', 'Search')
    ]

    print("Payload constructed.")

    # 7. POST Form
    print(f"\nSubmitting form with CAPTCHA: {captcha_text}...")
    
    # We must add a 'Referer' header to pretend we are a real browser
    post_headers = {
        'Referer': BASE_URL
    }
    
    # Post to the correct 'action' URL
    post_response = session.post(
        POST_URL, 
        data=form_payload, 
        headers=post_headers,
        verify=False
    )
    post_response.raise_for_status()

    # 8. Check Result
    if "Total Document(s): 1" in post_response.text:
        print("\n--- SUCCESS! (Stage 1) ---")
        print("Successfully reached the results page.")
        
        # 9. Parse results.html to find next link
        print("Parsing results page to find 'Application Number' link...")
        results_soup = BeautifulSoup(post_response.text, 'html.parser')
        details_form = results_soup.find('form', {'action': '/PublicSearch/PublicationSearch/PatentDetails'})
        
        if not details_form:
            print("  ERROR: Could not find the details form on the results page.")
            raise Exception("Results page HTML structure changed.")

        details_action_url = urljoin(BASE_URL, details_form['action'])
        connection_name_input = details_form.find('input', {'name': 'ConnectionName'})
        connection_name = connection_name_input['value'] if connection_name_input else None
        app_num_button = details_form.find('button', {'name': 'ApplicationNumber'})
        app_num_value = app_num_button['value'].strip() # Clean whitespace

        if not (connection_name and app_num_button):
            print("  ERROR: Could not find 'ConnectionName' or 'ApplicationNumber' button.")
            raise Exception("Results page HTML structure changed.")

        # 10. "Click" Link 1: Application Number
        print(f"  Found 'Application Number' link. Navigating to Details page...")
        payload_1 = {
            'ConnectionName': connection_name,
            'ApplicationNumber': app_num_value
        }
        details_headers = {'Referer': POST_URL}
        details_response = session.post(
            details_action_url, 
            data=payload_1, 
            headers=details_headers, 
            verify=False
        )
        
        # 11. Parse application_details.html to find next link
        print("  ✓ SUCCESS (Stage 2): Reached 'application_details.html'.")
        print("  Parsing details page to find 'View Application Status' button...")
        
        details_page_soup = BeautifulSoup(details_response.text, 'html.parser')
        status_form = details_page_soup.find('form', {'action': '/PublicSearch/PublicationSearch/GetApplicationStatus'})
        
        if not status_form:
             print("  ERROR: Could not find the 'GetApplicationStatus' form.")
             raise Exception("Details page HTML structure changed.")
        
        status_action_url = urljoin(BASE_URL, status_form['action'])
        app_num_hidden = status_form.find('input', {'name': 'ApplicationNumber'})
        app_num_value_for_status = app_num_hidden['value']
        
        payload_2 = {
            'ApplicationNumber': app_num_value_for_status,
            'submit': 'View Application Status'
        }
        
        print("  Navigating to Application Status page...")
        status_headers = {'Referer': details_action_url}
        status_response = session.post(
            status_action_url, 
            data=payload_2, 
            headers=status_headers, 
            verify=False
        )

        # 12. THIS IS THE NEW PART: Handle the JavaScript Redirect
        print("  ✓ SUCCESS (Stage 3): Reached 'application_status.html' redirect page.")
        print("  Parsing redirect page to bypass JavaScript...")
        
        redirect_soup = BeautifulSoup(status_response.text, 'html.parser')
        redirect_form = redirect_soup.find('form', {'name': 'form'})
        
        if not redirect_form:
            print("  ERROR: This was not the JS redirect page. Aborting.")
            # Save the file so we can see what went wrong
            with open("application_status.html", "w", encoding="utf-8") as f:
                f.write(status_response.text)
            raise Exception("Expected a JS redirect, but got something else. See application_status.html")
            
        # Extract the *new* URL and *new* hidden data
        redirect_action_url = redirect_form['action']
        redirect_app_num = redirect_form.find('input', {'name': 'AppNumber'})['value']
        redirect_otp = redirect_form.find('input', {'name': 'OTP'})['value']
        
        redirect_payload = {
            'AppNumber': redirect_app_num,
            'OTP': redirect_otp
        }
        
        print("  Manually submitting redirect form to get *real* status page...")
        # Make the 3rd POST request, mimicking the JavaScript
        real_status_response = session.post(
            redirect_action_url, 
            data=redirect_payload, 
            headers={'Referer': status_action_url}, # Referer is the previous page
            verify=False
        )
        
        print("  ✓ SUCCESS (Stage 4): Reached *real* status page.")
        
        # 13. Parse the *REAL* status page to find "View Documents"
        print("  Parsing real status page for 'View Documents' button...")
        real_status_soup = BeautifulSoup(real_status_response.text, 'html.parser')
        
        # Find the form for "View Documents"
        docs_form = real_status_soup.find('form', {'action': '/PatentSearch/PatentSearch/ViewDocuments'})
        if not docs_form:
             print("  ERROR: Could not find the 'ViewDocuments' form. Saving page as 'real_status_page.html' for debugging.")
             with open("real_status_page.html", "w", encoding="utf-8") as f:
                f.write(real_status_response.text)
             raise Exception("Could not find 'View Documents' form.")
        
        # Re-build the full URL, as this is a relative path
        docs_action_url = urljoin(BASE_URL, docs_form['action'])
        
        # We need to find the payload for this form.
        docs_app_num_input = docs_form.find('input', {'name': 'APPLICATION_NUMBER'})
        if not docs_app_num_input:
            print("  ERROR: Could not find 'APPLICATION_NUMBER' in the 'View Documents' form.")
            raise Exception("View Documents form HTML structure changed.")
            
        docs_app_num = docs_app_num_input['value']
        
        docs_payload = {
            'APPLICATION_NUMBER': docs_app_num,
            'SubmitAction': 'View Documents' # This is the button value
        }
        
        print("  Navigating to View Documents page...")
        docs_response = session.post(
            docs_action_url,
            data=docs_payload,
            headers={'Referer': redirect_action_url}, # Referer is the *real* status page
            verify=False
        )
        
        with open("view_documents.html", "w", encoding="utf-8") as f:
            f.write(docs_response.text)
        print("  ✓ SUCCESS (FINAL): Saved 'view_documents.html'.")
        
    elif "Invalid Captcha" in post_response.text:
        print("\n--- FAILED ---")
        print("Search failed: Invalid CAPTCHA.")
        print("Please run the script again.")
    
    else:
        print("\n--- FAILED ---")
        print("Search failed. Did not find 'Total Document(s): 1'.")
        print("This likely means the search criteria were wrong.")
        print("Response saved to 'error.html' for debugging.")
        with open("error.html", "w", encoding="utf-8") as f:
            f.write(post_response.text)

except requests.exceptions.RequestException as e:
    print(f"\nAn error occurred: {e}")
except Exception as e:
    print(f"\nA general error occurred: {e}")