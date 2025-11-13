import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys

# Import configuration and utilities
import config
from . import utils

# Suppress only the InsecureRequestWarning from requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def run_searcher(patent_app_no=None):
    """
    Performs the 5-stage "human-in-the-loop" search to retrieve
    all document pages for a single patent application.
    """
    print("--- Running Searcher ---")
    
    # 1. Get the patent to search for
    if patent_app_no:
        # Load the classified patents list
        patents = utils.load_json_history(config.CLASSIFIED_PATENTS_JSON)
        if not patents:
            print("Error: `classified_patents.json` is empty. Run filter first.")
            return
        
        # Find the patent by app number
        patent_data = next((p for p in patents if p['application_no'] == patent_app_no), None)
        if not patent_data:
            print(f"Error: Could not find patent {patent_app_no} in classified list.")
            return
        print(f"Found patent to search: {patent_data['title']}")
    else:
        # Fallback to default test data if no number is provided
        print("No application number provided. Using default test data.")
        patent_data = {
            "application_no": "202511087359 A",
            "date_of_filing": "15/09/2025",
        }

    # 2. Clean data for the form
    app_number_clean = patent_data["application_no"].split(' ')[0]
    app_date_formatted = utils.reformat_search_date(patent_data["date_of_filing"])
    
    if not app_date_formatted:
        return # Error already printed by utils

    print(f"Date: {app_date_formatted} (MM/DD/YYYY)")
    print(f"App No: {app_number_clean}")

    # 3. Start a session to handle cookies
    session = requests.Session()
    session.headers.update(config.REQUESTS_HEADER)

    try:
        # ------ STAGE 1: GET CAPTCHA ------
        print(f"\nConnecting to {config.SEARCH_BASE_URL} to get session...")
        response = session.get(config.SEARCH_BASE_URL, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Session started.")

        captcha_img_tag = soup.find('img', {'id': 'Captcha'})
        if not captcha_img_tag:
            print("Error: Could not find CAPTCHA image tag.")
            return

        captcha_url = urljoin(config.SEARCH_BASE_URL, captcha_img_tag['src'])
        print(f"Downloading CAPTCHA image to {config.CAPTCHA_IMAGE_FILE}...")
        image_response = session.get(captcha_url, verify=False)
        with open(config.CAPTCHA_IMAGE_FILE, 'wb') as f:
            f.write(image_response.content)

        # ------ STAGE 2: HUMAN-IN-THE-LOOP ------
        print("\n" + "="*40)
        print("   !!! ACTION REQUIRED !!!")
        print(f"Please open the file '{config.CAPTCHA_IMAGE_FILE}'.")
        print("Solve the CAPTCHA, then type the text below.")
        print("="*40)
        captcha_text = input("Enter CAPTCHA text here: ")

        # ------ STAGE 3: POST SEARCH FORM ------
        form_payload = [
            ('Published', 'true'), ('Published', 'false'), ('Granted', 'false'),
            ('DateField', 'APD'), 
            ('FromDate', app_date_formatted), ('ToDate', app_date_formatted),
            ('LogicField', 'AND'), 
            ('ItemField1', 'AP'), ('TextField1', app_number_clean), 
            ('LogicField1', 'AND'), 
            ('CaptchaText', captcha_text),
            ('submit', 'Search')
        ]
        print("\nPayload constructed. Submitting search...")
        
        post_headers = {'Referer': config.SEARCH_BASE_URL}
        post_response = session.post(
            config.SEARCH_POST_URL, 
            data=form_payload, 
            headers=post_headers,
            verify=False
        )
        post_response.raise_for_status()

        if "Invalid Captcha" in post_response.text:
            print("\n--- FAILED: Invalid CAPTCHA. Please run the script again. ---")
            return
        if "Total Document(s): 1" not in post_response.text:
            print("\n--- FAILED: Search was not successful. ---")
            with open(config.ERROR_HTML, "w", encoding="utf-8") as f:
                f.write(post_response.text)
            print(f"Response saved to {config.ERROR_HTML} for debugging.")
            return

        print("\n--- SUCCESS! (Stage 1) ---")
        print("Successfully reached results page.")
        
        # ------ STAGE 4: "CLICK" APPLICATION NUMBER ------
        print("Parsing results to find 'Application Number' link...")
        results_soup = BeautifulSoup(post_response.text, 'html.parser')
        details_form = results_soup.find('form', {'action': '/PublicSearch/PublicationSearch/PatentDetails'})
        details_action_url = urljoin(config.SEARCH_BASE_URL, details_form['action'])
        
        conn_name = details_form.find('input', {'name': 'ConnectionName'})['value']
        app_num_val = details_form.find('button', {'name': 'ApplicationNumber'})['value'].strip()

        payload_1 = {'ConnectionName': conn_name, 'ApplicationNumber': app_num_val}
        details_headers = {'Referer': config.SEARCH_POST_URL}
        
        details_response = session.post(
            details_action_url, data=payload_1, headers=details_headers, verify=False
        )
        print("  ✓ SUCCESS (Stage 2): Reached 'application_details.html'.")

        # ------ STAGE 5: "CLICK" VIEW APPLICATION STATUS ------
        print("  Parsing details page for 'View Application Status' button...")
        details_page_soup = BeautifulSoup(details_response.text, 'html.parser')
        status_form = details_page_soup.find('form', {'action': '/PublicSearch/PublicationSearch/GetApplicationStatus'})
        status_action_url = urljoin(config.SEARCH_BASE_URL, status_form['action'])
        app_num_for_status = status_form.find('input', {'name': 'ApplicationNumber'})['value']
        
        payload_2 = {'ApplicationNumber': app_num_for_status, 'submit': 'View Application Status'}
        status_headers = {'Referer': details_action_url}
        
        status_response = session.post(
            status_action_url, data=payload_2, headers=status_headers, verify=False
        )
        print("  ✓ SUCCESS (Stage 3): Reached 'application_status.html' (redirect page).")
        
        # ------ STAGE 6: BYPASS JAVASCRIPT REDIRECT ------
        print("  Parsing redirect page to bypass JavaScript...")
        redirect_soup = BeautifulSoup(status_response.text, 'html.parser')
        redirect_form = redirect_soup.find('form', {'name': 'form'})
        
        if not redirect_form:
            with open(config.STATUS_HTML, "w", encoding="utf-8") as f:
                f.write(status_response.text)
            print(f"  ERROR: Expected JS redirect, got something else. Saved to {config.STATUS_HTML}")
            return
            
        redirect_action_url = redirect_form['action']
        redirect_payload = {
            'AppNumber': redirect_form.find('input', {'name': 'AppNumber'})['value'],
            'OTP': redirect_form.find('input', {'name': 'OTP'})['value']
        }
        
        print("  Manually submitting redirect to get *real* status page...")
        real_status_response = session.post(
            redirect_action_url, data=redirect_payload, headers={'Referer': status_action_url}, verify=False
        )
        print("  ✓ SUCCESS (Stage 4): Reached *real* status page.")
        
        # ------ STAGE 7: "CLICK" VIEW DOCUMENTS ------
        print("  Parsing real status page for 'View Documents' button...")
        real_status_soup = BeautifulSoup(real_status_response.text, 'html.parser')
        docs_form = real_status_soup.find('form', {'action': '/PatentSearch/PatentSearch/ViewDocuments'})
        
        if not docs_form:
            with open(config.REAL_STATUS_HTML, "w", encoding="utf-8") as f:
                f.write(real_status_response.text)
            print(f"  ERROR: Could not find 'ViewDocuments' form. Saved page to {config.REAL_STATUS_HTML}")
            return
            
        docs_action_url = urljoin(config.SEARCH_BASE_URL, docs_form['action'])
        docs_app_num = docs_form.find('input', {'name': 'APPLICATION_NUMBER'})['value']
        
        docs_payload = {
            'APPLICATION_NUMBER': docs_app_num,
            'SubmitAction': 'View Documents'
        }
        
        print("  Navigating to View Documents page...")
        docs_response = session.post(
            docs_action_url, data=docs_payload, headers={'Referer': redirect_action_url}, verify=False
        )
        
        with open(config.DOCUMENTS_HTML, "w", encoding="utf-8") as f:
            f.write(docs_response.text)
        print(f"\n--- SUCCESS! (FINAL) ---")
        print(f"Saved final page to {config.DOCUMENTS_HTML}.")

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred: {e}")
    except Exception as e:
        print(f"\nA general error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # This allows you to run: python src/searcher.py
    run_searcher()