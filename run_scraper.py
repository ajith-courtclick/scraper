#!/usr/bin/env python3
import logging
import time
from datetime import datetime
from src.ecourts_scraper import ECourtsScraper
from src.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the scraper"""
    # List of CNR numbers to scrape
    cnr_numbers = [
        'KLKN220000012019',  # RCP case
        'KLKN220000022019',  # EP case
        'KLKN220000032019',  # EP case
        'KLKN220000042019',  # EP case
        'KLKN220000052019',  # OS case
        'KLKN220000062019',
        'KLKN220000072019',
        'KLKN220000082019',
        'KLKN220000092019',
        'KLKN220000102019'
    ]
    
    print("\n=== Scraping Configuration ===")
    print(f"Total cases to scrape: {len(cnr_numbers)}")
    print("CNR numbers:")
    for cnr in cnr_numbers:
        print(f"- {cnr}")
    
    # Initialize database
    db = Database()
    
    # Statistics
    start_time = time.time()
    successful_cases = 0
    failed_cases = 0
    total_cases = len(cnr_numbers)
    case_timings = []
    
    print("\n=== Starting Scraper ===")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run scraper
    with ECourtsScraper(db=db) as scraper:
        results = []
        for idx, cnr in enumerate(cnr_numbers, 1):
            case_start = time.time()
            print(f"\nProcessing case {idx}/{total_cases}: {cnr}")
            
            try:
                case_details = scraper.get_case_details(cnr)
                if case_details:
                    successful_cases += 1
                    results.append(case_details)
                    if db.insert_case(case_details):
                        print(f"✓ Successfully scraped and saved to database")
                    else:
                        print(f"✗ Scraped but failed to save to database")
                else:
                    failed_cases += 1
                    print(f"✗ Failed to scrape case details")
                
                case_time = time.time() - case_start
                case_timings.append(case_time)
                print(f"Time taken: {case_time:.2f} seconds")
                
            except Exception as e:
                failed_cases += 1
                print(f"✗ Error processing case: {str(e)}")
        
        # Calculate statistics
        total_time = time.time() - start_time
        avg_time = sum(case_timings) / len(case_timings) if case_timings else 0
        
        # Print final summary
        print("\n=== Scraping Summary ===")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per case: {avg_time:.2f} seconds")
        print(f"Success rate: {successful_cases}/{total_cases} ({(successful_cases/total_cases)*100:.1f}%)")
        
        print("\n=== Case Details ===")
        for result in results:
            print(f"\nCNR: {result['cnr_number']}")
            print(f"Case Type: {result.get('case_type', 'N/A')}")
            print(f"Filing Number: {result.get('filing_number', 'N/A')}")
            print(f"Decision Date: {result.get('decision_date', 'N/A')}")
            print(f"Nature of Disposal: {result.get('nature_of_disposal', 'N/A')}")
            print("-" * 50)

if __name__ == "__main__":
    main() 