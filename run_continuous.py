import time
from datetime import datetime, timedelta
import logging
import sys
import json
from src.ecourts_scraper import ECourtsScraper
from src.database import Database

def get_last_scraped_case(db):
    """Get the last scraped case number from the database"""
    try:
        last_case = db.get_last_case_number()
        if last_case:
            # Extract the numeric part from the CNR number (e.g., '000011' from 'KLKN010000112019')
            numeric_part = last_case[6:12]  # Get the 6 digits after 'KLKN01'
            return int(numeric_part)
        return 0
    except Exception as e:
        logging.error(f"Error getting last case number: {str(e)}")
        return 0

def get_test_cnr_numbers(start_number=1, batch_size=10):
    """Return a list of test CNR numbers with pattern KLKN01XXXXXX2019"""
    cnr_numbers = []
    for i in range(start_number, start_number + batch_size):
        # Format the number with leading zeros (6 digits)
        number = str(i).zfill(6)
        cnr = f"KLKN01{number}2019"
        cnr_numbers.append(cnr)
    return cnr_numbers

def save_failed_cases(failed_cases):
    """Save failed cases to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"failed_cases_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(failed_cases, f, indent=4)
    return filename

def main():
    """Main function to run the scraper continuously"""
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize database
        db = Database()
        
        # Get last case number from database
        last_case_number = db.get_last_case_number()
        if last_case_number:
            # Extract the numeric part from the last case number
            last_number = int(last_case_number[6:12])
            current_batch = last_number + 1
            logging.info(f"Starting from case number: {current_batch}")
        else:
            current_batch = 1
            logging.info("No last case number found. Starting from 1")
        
        # Initialize session
        session = ECourtsScraper(db=db)
        logging.info("Session setup successful")
        
        # Statistics for reporting
        stats = {
            'total_attempted': 0,
            'successful': 0,
            'non_existent': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': time.time(),
            'successful_cases': [],
            'non_existent_cases': [],
            'failed_cases': [],
            'skipped_cases': []
        }
        
        while True:  # Run indefinitely
            try:
                # Generate CNR numbers for this batch
                cnr_numbers = get_test_cnr_numbers(current_batch, 10)
                logging.info(f"\nStarting batch {current_batch} with {len(cnr_numbers)} cases")
                logging.info("CNR numbers to process:")
                for cnr in cnr_numbers:
                    logging.info(f"- {cnr}")
                logging.info("")
                
                # Process each CNR number
                for i, cnr in enumerate(cnr_numbers, 1):
                    stats['total_attempted'] += 1
                    
                    # Check if case already exists in database
                    if db.case_exists(cnr):
                        stats['skipped'] += 1
                        stats['skipped_cases'].append(cnr)
                        logging.info(f"Skipping case {i}/{len(cnr_numbers)}: {cnr} (already exists)")
                        continue
                    
                    logging.info(f"\nProcessing case {i}/{len(cnr_numbers)}: {cnr}")
                    start_case_time = time.time()
                    
                    # Try to get case data
                    case_data = None
                    for attempt in range(1, 4):  # Try up to 3 times
                        try:
                            logging.info(f"Attempt {attempt}/3 for CNR {cnr}")
                            case_data = session.get_case_details(cnr)
                            if case_data:
                                logging.info(f"Successfully fetched data for CNR {cnr} on attempt {attempt}")
                                break
                        except Exception as e:
                            logging.warning(f"Error in response (attempt {attempt}): {str(e)}")
                            if attempt < 3:
                                time.sleep(1)  # Wait before retrying
                    
                    if case_data:
                        try:
                            # Ensure required fields are present
                            if not case_data.get('cnr_number'):
                                case_data['cnr_number'] = cnr
                            if not case_data.get('court_name'):
                                case_data['court_name'] = "Kannur District Court"  # Default court name
                            
                            # Save case data to database
                            case_id = db.insert_case(case_data)
                            if case_id:
                                stats['successful'] += 1
                                stats['successful_cases'].append(cnr)
                                logging.info(f"✓ Successfully scraped and saved case {cnr}")
                                logging.info(f"Case Type: {case_data.get('case_type')}")
                                logging.info(f"Filing Number: {case_data.get('filing_number')}")
                                logging.info(f"Decision Date: {case_data.get('decision_date')}")
                            else:
                                stats['failed'] += 1
                                stats['failed_cases'].append(cnr)
                                logging.error(f"Failed to save case {cnr} to database")
                        except Exception as e:
                            stats['failed'] += 1
                            stats['failed_cases'].append(cnr)
                            logging.error(f"Error saving case {cnr} to database: {str(e)}")
                    else:
                        stats['non_existent'] += 1
                        stats['non_existent_cases'].append(cnr)
                        logging.info(f"Case {cnr} does not exist")
                        logging.info(f"✓ Case {cnr} does not exist")
                    
                    # Update last case number in database
                    db.update_last_case_number(cnr)
                    
                    # Log time taken
                    time_taken = time.time() - start_case_time
                    logging.info(f"Time taken: {time_taken:.2f} seconds")
                    
                    # Wait between cases
                    time.sleep(2)
                
                # Print batch summary
                runtime = time.time() - stats['start_time']
                logging.info(f"\n=== Batch {current_batch} Summary ===")
                logging.info(f"Runtime so far: {time.strftime('%H:%M:%S', time.gmtime(runtime))}")
                logging.info(f"Cases in this batch: {len(cnr_numbers)}")
                logging.info(f"Success rate: {(stats['successful'] / stats['total_attempted']) * 100:.2f}%")
                logging.info(f"Average time per case: {runtime / stats['total_attempted']:.2f} seconds")
                
                # Increment batch number
                current_batch += 1
                
            except KeyboardInterrupt:
                logging.info("\nScraping interrupted by user")
                break
            except Exception as e:
                logging.error(f"Error processing batch: {str(e)}")
                time.sleep(5)  # Wait before retrying
                continue
        
        # Print final summary
        runtime = time.time() - stats['start_time']
        logging.info("\n=== Final Summary ===")
        logging.info(f"Total runtime: {time.strftime('%H:%M:%S', time.gmtime(runtime))}")
        logging.info(f"Total cases attempted: {stats['total_attempted']}")
        logging.info(f"Successfully scraped: {stats['successful']}")
        logging.info(f"Non-existent cases: {stats['non_existent']}")
        logging.info(f"Failed cases: {stats['failed']}")
        logging.info(f"Skipped cases: {stats['skipped']}")
        logging.info(f"Success rate: {(stats['successful'] / stats['total_attempted']) * 100:.2f}%")
        logging.info(f"Average time per case: {runtime / stats['total_attempted']:.2f} seconds")
        
        logging.info("\nSuccessful CNRs:")
        for cnr in stats['successful_cases']:
            logging.info(f"- {cnr}")
        
        logging.info("\nNon-existent CNRs:")
        for cnr in stats['non_existent_cases']:
            logging.info(f"- {cnr}")
        
        logging.info("\nFailed CNRs:")
        for cnr in stats['failed_cases']:
            logging.info(f"- {cnr}")
        
        logging.info("\nSkipped CNRs:")
        for cnr in stats['skipped_cases']:
            logging.info(f"- {cnr}")
        
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
    finally:
        if 'session' in locals():
            session.close()
        if 'db' in locals():
            del db

if __name__ == "__main__":
    main() 