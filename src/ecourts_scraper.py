import requests
import json
import time
import logging
from datetime import datetime
from urllib.parse import urljoin
import re
import io
import pytesseract
from PIL import Image, ImageEnhance
from bs4 import BeautifulSoup
from io import BytesIO
from selenium.webdriver.common.by import By

from src.database import Database

class ECourtsScraper:
    def __init__(self, db=None):
        """Initialize scraper with database connection"""
        self.base_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
        self.session = requests.Session()
        self.db = db if db else Database()
        self.app_token = None
        
        # Initialize components
        self.setup_session()

    def setup_session(self):
        """Setup requests session with headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': self.base_url
        })
        logging.info("Session setup successful")

    def _get_app_token_and_captcha(self, max_retries=3):
        """Get a fresh app token and CAPTCHA from the homepage"""
        for attempt in range(max_retries):
            try:
                # First get the main page to get cookies and app token
                response = self.session.get(self.base_url)
                
                # Extract app token
                if 'app_token' in response.text:
                    token_start = response.text.find('app_token') + len('app_token') + 2
                    token_end = response.text.find('"', token_start)
                    self.app_token = response.text[token_start:token_end]
                    logging.info("Successfully retrieved new app token")
                    
                    # Get CAPTCHA directly
                    captcha_url = urljoin(self.base_url, "vendor/securimage/securimage_show.php")
                    captcha_response = self.session.post(
                        captcha_url,
                        headers={
                            'Referer': self.base_url,
                            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Connection': 'keep-alive',
                            'Sec-Fetch-Site': 'same-origin',
                            'Sec-Fetch-Mode': 'no-cors',
                            'Sec-Fetch-Dest': 'image',
                        }
                    )
                    
                    if captcha_response.status_code == 200 and captcha_response.headers.get('content-type', '').startswith('image/'):
                        # Process CAPTCHA image
                        img = Image.open(io.BytesIO(captcha_response.content))
                        
                        # Save for debugging
                        img.save('last_captcha.png')
                        
                        # Enhance image for better OCR
                        img = img.convert('L')  # Convert to grayscale
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(2)  # Increase contrast
                        
                        # OCR the CAPTCHA
                        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                        captcha_text = pytesseract.image_to_string(img, config=custom_config).strip()
                        
                        logging.info(f"Successfully extracted CAPTCHA text: {captcha_text}")
                        return True, captcha_text
                    else:
                        logging.error(f"Failed to get CAPTCHA image: HTTP {captcha_response.status_code}")
                else:
                    logging.error("Could not find app token in page")
                
            except Exception as e:
                logging.error(f"Failed to get app token and CAPTCHA (attempt {attempt+1}/{max_retries}): {str(e)}")
                time.sleep(1)
                
        return False, None

    def _parse_case_details(self, html_content):
        """
        Parse case details from the HTML response.
        Returns None if the case does not exist.
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check if case does not exist
            error_msg = soup.find('span', text='This Case Code does not exists')
            if error_msg:
                return None
            
            case_details = {
                'html_content': html_content,  # Store the HTML content
                'cnr_number': None,
                'case_type': None,
                'filing_number': None,
                'filing_date': None,
                'registration_number': None,
                'registration_date': None,
                'case_status': None,
                'disposal_nature': None,
                'disposal_date': None,
                'decision_date': None,
                'court_number_and_judge': None,
                'petitioner_name': None,
                'petitioner_advocate': None,
                'respondent_name': None,
                'respondent_advocate': None,
                'under_acts': None,
                'under_sections': None,
                'first_hearing_date': None,
                'case_history': [],
                'transfer_details': [],  # Add transfer_details list
                'ia_details': [],  # Add ia_details list
                'court_name': None  # Add court_name field
            }

            # Extract court name from the heading
            court_heading = soup.find('h2', class_='h4', id='chHeading')
            if court_heading:
                case_details['court_name'] = str(court_heading.get_text(strip=True))

            # Check if the page contains case details
            if 'Case Details' not in html_content:
                logging.error("No case details found in the response")
                return None

            # Parse case details table
            case_details_table = soup.find('table', class_='case_details_table')
            if case_details_table:
                rows = case_details_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        label = cols[0].get_text(strip=True).lower()
                        if 'case type' in label:
                            case_details['case_type'] = str(cols[1].get_text(strip=True))
                        elif 'filing number' in label:
                            case_details['filing_number'] = str(cols[1].get_text(strip=True))
                            if len(cols) >= 4:
                                case_details['filing_date'] = str(cols[3].get_text(strip=True))
                        elif 'registration number' in label:
                            case_details['registration_number'] = str(cols[1].get_text(strip=True))
                            if len(cols) >= 4:
                                case_details['registration_date'] = str(cols[3].get_text(strip=True))
                        elif 'cnr number' in label:
                            # Extract only the 16-character CNR number
                            cnr_text = cols[1].get_text(strip=True)
                            # Get first word and ensure it's exactly 16 characters
                            case_details['cnr_number'] = str(cnr_text[:16])

            # Parse case status table
            case_status_table = soup.find('table', class_='case_status_table')
            if case_status_table:
                rows = case_status_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        label = cols[0].get_text(strip=True).lower()
                        if 'first hearing date' in label:
                            case_details['first_hearing_date'] = str(cols[1].get_text(strip=True))
                        elif 'decision date' in label:
                            decision_date = str(cols[1].get_text(strip=True))
                            case_details['decision_date'] = decision_date
                            # For disposed cases, set disposal_date to decision_date
                            if case_details.get('case_status') == 'Case disposed':
                                case_details['disposal_date'] = decision_date
                        elif 'case status' in label:
                            case_details['case_status'] = str(cols[1].get_text(strip=True))
                        elif 'nature of disposal' in label:
                            case_details['disposal_nature'] = str(cols[1].get_text(strip=True))
                        elif 'court number and judge' in label:
                            case_details['court_number_and_judge'] = str(cols[1].get_text(strip=True))

            # Parse petitioner and advocate details
            petitioner_table = soup.find('table', class_='Petitioner_Advocate_table')
            if petitioner_table:
                rows = petitioner_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 1:
                        text = str(cols[0].get_text(strip=True))
                        parts = text.split('Advocate-')
                        if len(parts) >= 2:
                            case_details['petitioner_name'] = str(parts[0].strip())
                            case_details['petitioner_advocate'] = str(parts[1].strip())
                        else:
                            case_details['petitioner_name'] = text

            # Parse respondent and advocate details
            respondent_table = soup.find('table', class_='Respondent_Advocate_table')
            if respondent_table:
                rows = respondent_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 1:
                        text = str(cols[0].get_text(strip=True))
                        parts = text.split('Advocate-')
                        if len(parts) >= 2:
                            case_details['respondent_name'] = str(parts[0].strip())
                            case_details['respondent_advocate'] = str(parts[1].strip())
                        else:
                            case_details['respondent_name'] = text

            # Parse acts and sections
            case_details['under_acts'], case_details['under_sections'] = self._extract_acts_and_sections(soup)

            # Extract Case History
            try:
                history_table = soup.find('table', class_='history_table')
                if history_table:
                    # Get all rows except the header
                    rows = history_table.find_all('tr')[1:]  # Skip header row
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 4:
                            history_entry = {
                                "judge": str(cols[0].get_text(strip=True)),
                                "business_date": str(cols[1].get_text(strip=True).split('\n')[0]),  # Get only the date, not the link text
                                "hearing_date": str(cols[2].get_text(strip=True)),
                                "purpose": str(cols[3].get_text(strip=True))
                            }
                            # Only add entries that have valid data
                            if any(history_entry.values()):
                                case_details['case_history'].append(history_entry)
                    logging.info(f"Found {len(case_details['case_history'])} case history entries")
            except Exception as e:
                logging.error(f"Error extracting case history: {str(e)}")
                case_details['case_history'] = []
                pass

            # Extract Case Transfer Details
            try:
                transfer_table = soup.find('table', class_='transfer_table')
                if transfer_table:
                    rows = transfer_table.find_all('tr')[1:]  # Skip header row
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 4:
                            transfer_entry = {
                                "registration_number": str(cols[0].get_text(strip=True)),
                                "transfer_date": str(cols[1].get_text(strip=True)),
                                "from_court": str(cols[2].get_text(strip=True)),
                                "to_court": str(cols[3].get_text(strip=True))
                            }
                            case_details['transfer_details'].append(transfer_entry)
                    logging.info(f"Found {len(case_details['transfer_details'])} case transfer entries")
            except Exception as e:
                logging.error(f"Error extracting case transfer details: {str(e)}")
                case_details['transfer_details'] = []
                pass

            # Extract IA Details
            try:
                ia_entries = self._extract_ia_details(soup)
                case_details['ia_details'] = ia_entries
                logging.info(f"Found {len(case_details['ia_details'])} IA entries")
                logging.debug(f"IA details: {json.dumps(case_details['ia_details'], indent=2)}")
            except Exception as e:
                logging.error(f"Error extracting IA details: {str(e)}")
                case_details['ia_details'] = []
                pass

            # Return all fields, including None values
            return case_details
        except Exception as e:
            logging.error(f"Error parsing case details: {str(e)}")
            return None

    def fetch_case_history(self, cnr):
        """Fetch case history using the history API endpoint"""
        try:
            if not self.app_token:
                self._get_app_token_and_captcha()

            # Parse CNR number to get required parameters
            court_code = cnr[4:6]
            state_code = cnr[2:4]
            national_court_code = cnr[:6]

            # First get the case details to extract establishment code
            search_url = urljoin(self.base_url, "?p=cnr_status/searchByCNR")
            data = {
                'cino': cnr,
                'ajax_req': 'true',
                'app_token': self.app_token
            }

            # Get a fresh token for history request
            self._get_app_token_and_captcha()

            # Then fetch case history
            history_url = urljoin(self.base_url, "?p=home/viewBusiness")
            history_data = {
                'establishment_code': national_court_code,
                'court_code': court_code,
                'state_code': state_code,
                'dist_code': national_court_code[2:4],
                'case_number1': cnr,
                'disposal_flag': 'DisposedP',
                'national_court_code': national_court_code,
                'court_no': '1',
                'search_by': 'cnr',
                'srno': '1',
                'ajax_req': 'true',
                'app_token': self.app_token,
                'cino': cnr,
                'business_type': 'case_history',
                'case_type': 'EP',  # Default to EP since most cases are EP
                'case_no': cnr[6:],  # Extract case number from CNR
                'year': '20' + cnr[-4:],  # Extract year from CNR
                'state_name': 'Kerala',  # Hardcode for now since all cases are from Kerala
                'dist_name': 'KANNUR',  # Hardcode for now since all cases are from Kannur
                'court_name': 'Munsiffss Court Kuthuparamba',  # Hardcode for now
                'business_flag': 'true',
                'business_type_flag': 'true',
                'business_date': datetime.now().strftime('%d-%m-%Y')
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Referer': self.base_url + '?p=cnr_status/searchByCNR',
                'Origin': 'https://services.ecourts.gov.in',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty'
            }

            # First make a GET request to set up session
            self.session.get(self.base_url + '?p=home/business')

            # Then make the POST request for history
            response = self.session.post(history_url, data=history_data, headers=headers)
            logging.debug(f"History response status: {response.status_code}")
            logging.debug(f"History response content: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    history_data = response.json() if response.text.strip() else None
                    if history_data and isinstance(history_data, dict):
                        if 'errormsg' not in history_data:
                            logging.info(f"Successfully fetched history for CNR {cnr}")
                            return history_data
                        else:
                            logging.warning(f"Error in history response: {history_data['errormsg']}")
                    else:
                        logging.warning(f"No valid history data in response for CNR {cnr}")
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON response for case history {cnr}: {str(e)}")
            else:
                logging.error(f"HTTP {response.status_code} error for history of CNR {cnr}")
            return None

        except Exception as e:
            logging.error(f"Error fetching case history for {cnr}: {str(e)}")
            return None

    def get_case_details(self, cnr, max_attempts=3):
        """Get case details for a given CNR number with enhanced error handling"""
        if not self.app_token:
            success, _ = self._get_app_token_and_captcha()
            if not success:
                logging.error("Failed to get initial app token")
                return None
            
        for attempt in range(max_attempts):
            try:
                logging.info(f"Attempt {attempt + 1}/{max_attempts} for CNR {cnr}")
                
                # Get fresh token and CAPTCHA
                success, _ = self._get_app_token_and_captcha()
                if not success:
                    logging.warning(f"Failed to get app token on attempt {attempt + 1}")
                    continue
                
                # Extract CAPTCHA text
                captcha_text = self._extract_captcha_text()
                if not captcha_text:
                    logging.warning(f"Failed to solve CAPTCHA on attempt {attempt + 1}")
                    continue
                
                logging.info(f"Using CAPTCHA text: {captcha_text}")
                
                # Make initial request to set up session
                self.session.get(self.base_url)
                
                # Prepare request data
                data = {
                    'cino': cnr,
                    'fcaptcha_code': captcha_text,
                    'ajax_req': 'true',
                    'app_token': self.app_token
                }
                
                # Make request with detailed logging
                logging.info(f"Sending request with data: {json.dumps(data)}")
                response = self.session.post(
                    f"{self.base_url}?p=cnr_status/searchByCNR",
                    data=data,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Origin': 'https://services.ecourts.gov.in',
                        'Referer': self.base_url + '?p=cnr_status/searchByCNR',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Dest': 'empty'
                    }
                )
                
                logging.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if 'errormsg' in result:
                            logging.warning(f"Error in response (attempt {attempt + 1}): {result['errormsg']}")
                            # Save failed response for debugging
                            with open(f'failed_response_{attempt + 1}.json', 'w') as f:
                                json.dump(result, f, indent=2)
                            continue
                            
                        # Save HTML response for debugging
                        html_content = result.get('casetype_list', '')
                        with open('last_response.html', 'w') as f:
                            f.write(html_content)
                        logging.info("Saved HTML response to last_response.html")
                            
                        # Check if case exists
                        if 'This Case Code does not exists' in html_content:
                            logging.info(f"Case {cnr} does not exist")
                            return {'cnr_number': cnr, 'exists': False}
                            
                        # Parse case details from HTML response
                        case_details = self._parse_case_details(html_content)
                        if case_details:
                            case_details['exists'] = True
                            logging.info(f"Successfully fetched data for CNR {cnr} on attempt {attempt + 1}")
                            return case_details
                        else:
                            logging.warning(f"Failed to parse case details from response on attempt {attempt + 1}")
                            
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON response on attempt {attempt + 1}: {str(e)}")
                        continue
                    except Exception as e:
                        logging.error(f"Error parsing response on attempt {attempt + 1}: {str(e)}")
                        continue
                else:
                    logging.error(f"HTTP {response.status_code} error on attempt {attempt + 1}")
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                continue
                
            # Add delay between attempts
            if attempt < max_attempts - 1:
                time.sleep(2)
                
        logging.error(f"Failed to fetch case details for {cnr} after {max_attempts} attempts")
        return None

    def run(self, cnr_numbers):
        """Run the scraper for multiple CNR numbers"""
        results = []
        total_cases = len(cnr_numbers)
        successful_cases = 0
        
        print(f"\nStarting to scrape {total_cases} cases...")
        
        for idx, cnr in enumerate(cnr_numbers, 1):
            print(f"\nProcessing case {idx}/{total_cases}: {cnr}")
            case_details = self.get_case_details(cnr)
            
            if case_details:
                successful_cases += 1
                results.append(case_details)
                if self.db:
                    try:
                        self.db.insert_case(case_details)
                    except Exception as e:
                        logging.error(f"Failed to store case {cnr}: {str(e)}")
            
            # Add delay between cases
            if idx < total_cases:
                time.sleep(2)
        
        # Print scraped data in a readable format
        print(f"\n=== Scraped Case Details ({successful_cases}/{total_cases} successful) ===")
        for case in results:
            print(f"\nCase CNR: {case['cnr_number']}")
            print("-" * 50)
            for key, value in sorted(case.items()):
                if value is not None and key not in ['created_at', 'updated_at']:
                    print(f"{key}: {value}")
        
        return results

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        if self.session:
            self.session.close()
            
    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()

    def _extract_captcha_text(self):
        """Extract text from CAPTCHA image with enhanced preprocessing"""
        try:
            # Get CAPTCHA image
            captcha_url = urljoin(self.base_url, "vendor/securimage/securimage_show.php")
            captcha_response = self.session.post(
                captcha_url,
                headers={
                    'Referer': self.base_url,
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Dest': 'image',
                }
            )
            
            if captcha_response.status_code != 200:
                logging.error(f"Failed to get CAPTCHA image: HTTP {captcha_response.status_code}")
                return None
                
            if not captcha_response.headers.get('content-type', '').startswith('image/'):
                logging.error("Response is not an image")
                return None
            
            # Process CAPTCHA image
            img = Image.open(io.BytesIO(captcha_response.content))
            
            # Save original for debugging
            img.save('last_captcha_original.png')
            
            # Enhanced image processing
            img = img.convert('L')  # Convert to grayscale
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)
            
            # Increase brightness
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.5)
            
            # Threshold to make it black and white
            threshold = 128
            img = img.point(lambda x: 255 if x > threshold else 0)
            
            # Save processed image for debugging
            img.save('last_captcha_processed.png')
            
            # OCR with different PSM modes
            psm_modes = [7, 8, 13]  # Different page segmentation modes to try
            for psm in psm_modes:
                custom_config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                captcha_text = pytesseract.image_to_string(img, config=custom_config).strip()
                
                if captcha_text and len(captcha_text) >= 4:  # Most CAPTCHAs are at least 4 chars
                    logging.info(f"Successfully extracted CAPTCHA text with PSM {psm}: {captcha_text}")
                    return captcha_text
            
            logging.warning("Failed to extract valid CAPTCHA text with any PSM mode")
            return None
            
        except Exception as e:
            logging.error(f"Error processing CAPTCHA: {str(e)}")
            return None

    def test_parse_html(self, html_content):
        """Test function to parse HTML content directly"""
        case_details = self._parse_case_details(html_content)
        if case_details:
            print("\n=== Parsed Case Details ===")
            for key, value in sorted(case_details.items()):
                if value is not None:
                    print(f"\n{key}:")
                    print("-" * 50)
                    print(value)
        return case_details

    def _extract_ia_details(self, soup):
        ia_table = soup.find('table', {'class': 'IAheading'})
        if not ia_table:
            return []

        ia_entries = []
        rows = ia_table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                # Get raw text values and ensure they are strings
                try:
                    ia_no = str(cols[0].get_text(strip=True))
                    party_raw = str(cols[1].get_text(strip=True))
                    dt_filing = str(cols[2].get_text(strip=True))
                    next_date_purpose = str(cols[3].get_text(strip=True))
                    ia_status = str(cols[4].get_text(strip=True))
                except:
                    continue  # Skip this row if any value can't be converted to string

                # Clean party name - ensure it's a string and handle numeric values
                try:
                    party_name = party_raw.replace('<br/>', ' ').strip()
                except:
                    party_name = ""

                # Split next date and purpose
                next_date = ""
                purpose = ""
                if next_date_purpose:
                    parts = next_date_purpose.split('(', 1)
                    next_date = str(parts[0].strip())
                    purpose = str(parts[1].rstrip(')').strip()) if len(parts) > 1 else ""

                ia_entry = {
                    'ia_no': ia_no,
                    'party': party_name,
                    'dt_filing': dt_filing,
                    'next_date': next_date,
                    'purpose': purpose,
                    'ia_status': ia_status,
                    'classification': 'General'
                }
                ia_entries.append(ia_entry)

        return ia_entries

    def _extract_acts_and_sections(self, soup):
        """Extract acts and sections from the HTML."""
        acts = []
        sections = []
        
        # Find the acts table
        acts_table = soup.find('table', {'id': 'act_table'})
        if acts_table:
            # Skip header row
            rows = acts_table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    act = cols[0].get_text(strip=True).rstrip('\\')  # Remove trailing backslash
                    section = cols[1].get_text(strip=True)
                    if act:
                        acts.append(act)
                    if section:
                        sections.append(section)
        
        return ','.join(acts) if acts else None, ','.join(sections) if sections else None
