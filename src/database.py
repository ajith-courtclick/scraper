from typing import Dict, Any, List
import logging
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, JSON, DateTime, inspect, text, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
import pandas as pd
import os
import json
import mysql.connector
from mysql.connector import Error
import re

from config.settings import MYSQL_DATABASE

class Database:
    def __init__(self):
        """Initialize database connection"""
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="password",
                database="ecourts",
                consume_results=True  # Auto-consume unread results
            )
            self.cursor = self.connection.cursor(dictionary=True)
            self.setup_database()
            self.create_tables()  # Create tables after database setup
            logging.info("Database tables created successfully")
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            raise

    def setup_database(self):
        """Create database tables if they don't exist"""
        try:
            # Create tables using the schema
            with open('schema.sql', 'r') as f:
                sql_commands = f.read().split(';')
                for command in sql_commands:
                    if command.strip():
                        try:
                            self.cursor.execute(command)
                            self.connection.commit()
                        except mysql.connector.Error as e:
                            # Ignore errors for duplicate entries in categories table
                            if e.errno == 1062 and 'categories.PRIMARY' in str(e):
                                continue
                            # Ignore "table already exists" errors
                            elif e.errno == 1050:
                                continue
                            else:
                                raise
        except Error as e:
            logging.error(f"Error setting up database: {e}")
            raise

    def _parse_date(self, date_str):
        """Parse date string into MySQL format"""
        if not date_str:
            return None
            
        # Convert to string if needed
        if isinstance(date_str, (int, float)):
            date_str = str(date_str)
        elif not isinstance(date_str, str):
            try:
                date_str = str(date_str)
            except:
                return None
            
        # Remove ordinal indicators and clean the string
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        date_str = date_str.strip()
        
        formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%d-%b-%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None

    def _get_or_create_case_type(self, case_type):
        """Get or create case type and return its ID"""
        if not case_type:
            return None
            
        # Split into short and expanded form (e.g., "OP - ORIGINAL PETITION")
        parts = case_type.split(' - ', 1)
        short_form = parts[0].strip()
        expanded_form = parts[1].strip() if len(parts) > 1 else None
        
        query = "INSERT IGNORE INTO case_types (short_form, expanded_form) VALUES (%s, %s)"
        self.cursor.execute(query, (short_form, expanded_form))
        self.connection.commit()
        
        self.cursor.execute("SELECT case_type_id FROM case_types WHERE short_form = %s", (short_form,))
        result = self.cursor.fetchone()
        return result['case_type_id'] if result else None

    def _clean_litigant_name(self, name):
        """Clean litigant name by removing special characters and extra whitespace"""
        if name is None:
            return None
        
        # Convert numeric types to string
        if isinstance(name, (int, float)):
            name = str(name)
        elif not isinstance(name, str):
            try:
                name = str(name)
            except:
                return None
        
        # Remove number prefix pattern (e.g., "1 ", "2) ", etc.)
        name = re.sub(r'^\d+[\s\)]+', '', name)
        
        # Remove special characters and extra whitespace
        cleaned = re.sub(r'[^\w\s]', ' ', name)
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip() if cleaned else None

    def _get_or_create_state_district(self, cnr_number):
        """Get or create state and district from CNR number"""
        # For CNR KLKN010000132019:
        # KL = Kerala
        # KN = Kannur
        state_name = "Kerala"  # Static for now as per requirement
        district_name = "Kannur"  # Static for now as per requirement
        
        # Insert state if not exists
        query = """
            INSERT IGNORE INTO states (name, created_at, updated_at)
            VALUES (%s, NOW(), NOW())
        """
        self.cursor.execute(query, (state_name,))
        self.connection.commit()
        
        # Get state ID
        self.cursor.execute("SELECT id FROM states WHERE name = %s", (state_name,))
        state_id = self.cursor.fetchone()['id']
        
        # Insert district if not exists
        query = """
            INSERT IGNORE INTO districts (name, state_id, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
        """
        self.cursor.execute(query, (district_name, state_id))
        self.connection.commit()
        
        # Get district ID
        self.cursor.execute("SELECT id FROM districts WHERE name = %s", (district_name,))
        district_id = self.cursor.fetchone()['id']
        
        return state_id, district_id

    def _get_or_create_court(self, court_name, state_id, district_id):
        """Get or create court and return its ID"""
        if not court_name:
            return None
            
        # Category ID for District Courts is 3
        category_id = 3
        
        query = """
            INSERT IGNORE INTO courts (name, state_id, district_id, category_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
        self.cursor.execute(query, (court_name, state_id, district_id, category_id))
        self.connection.commit()
        
        self.cursor.execute(
            "SELECT id FROM courts WHERE name = %s AND state_id = %s AND district_id = %s",
            (court_name, state_id, district_id)
        )
        result = self.cursor.fetchone()
        return result['id'] if result else None

    def _get_or_create_court_hall(self, court_number_and_judge, court_id):
        """Get or create court hall and return its ID and judge name"""
        if not court_number_and_judge:
            return None, None
            
        # Parse court number and judge from string like "4-3rd Additional District Judge"
        match = re.match(r'(\d+)\s*-\s*(.+)', court_number_and_judge)
        if match:
            court_hall_number = match.group(1)
            judge_name = match.group(2).strip()
            
            query = """
                INSERT IGNORE INTO court_halls (name, court_id, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """
            self.cursor.execute(query, (court_hall_number, court_id))
            self.connection.commit()
            
            self.cursor.execute(
                "SELECT id FROM court_halls WHERE name = %s AND court_id = %s",
                (court_hall_number, court_id)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None, judge_name
        return None, None

    def _get_or_create_litigant(self, name):
        """Get or create a litigant by name"""
        if not name:
            return None
            
        try:
            # Clean the name first
            cleaned_name = self._clean_litigant_name(name)
            if not cleaned_name:
                return None
            
            # Check if litigant exists
            query = "SELECT litigant_id FROM litigants WHERE litigant_name = %s"
            self.cursor.execute(query, (cleaned_name,))
            result = self.cursor.fetchone()
            
            if result:
                return result['litigant_id']
            
            # Create new litigant
            query = "INSERT INTO litigants (litigant_name) VALUES (%s)"
            self.cursor.execute(query, (cleaned_name,))
            self.connection.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            logging.error(f"Error in _get_or_create_litigant: {e}")
            return None

    def _get_or_create_advocate(self, name):
        """Get or create advocate and return its ID"""
        if not name:
            return None
            
        query = "INSERT IGNORE INTO advocates (advocate_name) VALUES (%s)"
        self.cursor.execute(query, (name,))
        self.connection.commit()
        
        self.cursor.execute("SELECT advocate_id FROM advocates WHERE advocate_name = %s", (name,))
        result = self.cursor.fetchone()
        return result['advocate_id'] if result else None

    def _get_or_create_act(self, act_name):
        """Get or create act and return its ID"""
        if not act_name:
            return None
            
        try:
            # Convert to string if needed
            if isinstance(act_name, (int, float)):
                act_name = str(act_name)
            elif not isinstance(act_name, str):
                try:
                    act_name = str(act_name)
                except:
                    return None
            
            # Clean up act name
            act_name = act_name.strip()
            
            # Remove trailing backslash and whitespace
            act_name = act_name.rstrip('\\').strip()
            
            # Handle act name with year - combine them properly
            parts = [part.strip() for part in act_name.split(',')]
            if len(parts) > 1 and parts[1].strip().isdigit():
                act_name = f"{parts[0].strip()}, {parts[1].strip()}"
            else:
                # Check if the act name contains a year at the end
                parts = act_name.split()
                if len(parts) > 1 and parts[-1].isdigit():
                    year = parts[-1]
                    name = ' '.join(parts[:-1])
                    act_name = f"{name}, {year}"
                
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            query = """
                INSERT INTO acts (name, created_at, updated_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), updated_at=%s
            """
            self.cursor.execute(query, (act_name, current_timestamp, current_timestamp, current_timestamp))
            self.connection.commit()
            
            self.cursor.execute("SELECT id FROM acts WHERE name = %s", (act_name,))
            result = self.cursor.fetchone()
            return result['id'] if result else None
            
        except Exception as e:
            logging.error(f"Error in _get_or_create_act: {e}")
            return None

    def _get_or_create_section(self, section_number):
        """Get or create section and return its ID"""
        if not section_number:
            return None
            
        try:
            # Convert to string if needed
            if isinstance(section_number, (int, float)):
                section_number = str(section_number)
            elif not isinstance(section_number, str):
                try:
                    section_number = str(section_number)
                except:
                    return None
            
            # Clean up section number
            section_number = section_number.strip()
            
            query = """
                INSERT INTO sections (section_number, created_at, updated_at)
                VALUES (%s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE section_id=LAST_INSERT_ID(section_id)
            """
            self.cursor.execute(query, (section_number,))
            self.connection.commit()
            
            self.cursor.execute("SELECT section_id FROM sections WHERE section_number = %s", (section_number,))
            result = self.cursor.fetchone()
            return result['section_id'] if result else None
            
        except Exception as e:
            logging.error(f"Error in _get_or_create_section: {e}")
            return None

    def _get_or_create_act_section(self, act_id, section_number):
        """Get or create act section and return its ID"""
        if not act_id or not section_number:
            return None
            
        try:
            # First get or create the section
            section_id = self._get_or_create_section(section_number)
            if not section_id:
                return None
            
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            query = """
                INSERT INTO act_sections (act_id, section_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), updated_at=%s
            """
            self.cursor.execute(query, (act_id, section_id, current_timestamp, current_timestamp, current_timestamp))
            self.connection.commit()
            
            self.cursor.execute(
                "SELECT id FROM act_sections WHERE act_id = %s AND section_id = %s",
                (act_id, section_id)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None
            
        except Exception as e:
            logging.error(f"Error in _get_or_create_act_section: {e}")
            return None

    def insert_case(self, case_details):
        """Insert case details into database"""
        try:
            # Log case details for debugging
            logging.debug(f"Case details: {json.dumps(case_details, indent=2, default=str)}")
            
            # Get state and district IDs from CNR
            state_id, district_id = self._get_or_create_state_district(case_details['cnr_number'])
            
            # Get or create court using the court name from case details
            court_id = self._get_or_create_court(case_details['court_name'], state_id, district_id)
            
            # Get or create court hall and judge
            court_hall_id, judge_name = self._get_or_create_court_hall(
                case_details['court_number_and_judge'],
                court_id
            )
            
            # Get or create case type
            case_type_id = self._get_or_create_case_type(case_details['case_type'])
            
            # Parse dates
            filing_date = self._parse_date(case_details['filing_date'])
            registration_date = self._parse_date(case_details['registration_date'])
            first_hearing_date = self._parse_date(case_details['first_hearing_date'])
            decision_date = self._parse_date(case_details['decision_date'])
            disposal_date = self._parse_date(case_details['disposal_date'])
            
            # Insert case
            query = """
                INSERT INTO cases (
                    cnr_number, case_type_id, filing_number, filing_date,
                    registration_number, registration_date, case_status,
                    first_hearing_date, decision_date, disposal_date,
                    disposal_nature, court_hall_id, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """
            self.cursor.execute(query, (
                case_details['cnr_number'], case_type_id, case_details['filing_number'],
                filing_date, case_details['registration_number'], registration_date,
                case_details['case_status'], first_hearing_date, decision_date,
                disposal_date, case_details['disposal_nature'], court_hall_id
            ))
            self.connection.commit()
            
            # Get case ID
            self.cursor.execute("SELECT LAST_INSERT_ID() as id")
            case_id = self.cursor.fetchone()['id']
            
            # Insert petitioner and advocate
            if case_details['petitioner_name']:
                petitioner_id = self._get_or_create_litigant(
                    self._clean_litigant_name(case_details['petitioner_name'])
                )
                petitioner_advocate_id = self._get_or_create_advocate(case_details['petitioner_advocate'])
                
                # Insert into case_litigants
                query = """
                    INSERT INTO case_litigants (
                        case_id, litigant_id, advocate_id, party_type,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, NOW(), NOW())
                """
                self.cursor.execute(query, (
                    case_id, petitioner_id, petitioner_advocate_id, 'Petitioner'
                ))
                self.connection.commit()
            
            # Insert respondent and advocate
            if case_details['respondent_name']:
                respondent_id = self._get_or_create_litigant(
                    self._clean_litigant_name(case_details['respondent_name'])
                )
                respondent_advocate_id = self._get_or_create_advocate(case_details['respondent_advocate'])
                
                # Insert into case_litigants
                query = """
                    INSERT INTO case_litigants (
                        case_id, litigant_id, advocate_id, party_type,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, NOW(), NOW())
                """
                self.cursor.execute(query, (
                    case_id, respondent_id, respondent_advocate_id, 'Respondent'
                ))
                self.connection.commit()
            
            # Insert acts and sections
            if case_details['under_acts']:
                try:
                    # Convert acts to string if needed
                    acts_str = str(case_details['under_acts']) if not isinstance(case_details['under_acts'], str) else case_details['under_acts']
                    acts = [act.strip() for act in acts_str.split(',') if act.strip()]
                    
                    sections = []
                    if case_details['under_sections']:
                        # Convert sections to string if needed
                        sections_str = str(case_details['under_sections']) if not isinstance(case_details['under_sections'], str) else case_details['under_sections']
                        sections = [section.strip() for section in sections_str.split(',') if section.strip()]
                    
                    # Handle case where act might contain the year
                    if len(acts) == 2 and acts[1].isdigit():
                        acts = [f"{acts[0]}, {acts[1]}"]
                    
                    # Ensure sections list is at least as long as acts list
                    while len(sections) < len(acts):
                        sections.append(None)
                    
                    for act, section in zip(acts, sections):
                        if act:  # Only process if act is not empty
                            act_id = self._get_or_create_act(act)
                            if act_id:
                                act_section_id = None
                                if section:
                                    # Get or create act_section relationship
                                    act_section_id = self._get_or_create_act_section(act_id, section)
                                
                                # Insert case-act relationship
                                query = """
                                    INSERT INTO case_acts (
                                        case_id, act_id, act_section_id, created_at, updated_at
                                    ) VALUES (%s, %s, %s, NOW(), NOW())
                                """
                                self.cursor.execute(query, (case_id, act_id, act_section_id))
                                self.connection.commit()
                except Exception as e:
                    logging.error(f"Error processing acts and sections: {e}")
            
            # Insert case history
            if case_details['case_history']:
                for entry in case_details['case_history']:
                    business_date = self._parse_date(entry['business_date'])
                    hearing_date = self._parse_date(entry['hearing_date'])
                    
                    query = """
                        INSERT INTO case_history (
                            case_id, judge, business_date, hearing_date,
                            purpose, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    self.cursor.execute(query, (
                        case_id, entry['judge'], business_date,
                        hearing_date, entry['purpose']
                    ))
                    self.connection.commit()
            
            # Insert case transfers
            if case_details['transfer_details']:
                for transfer in case_details['transfer_details']:
                    transfer_date = self._parse_date(transfer['transfer_date'])
                    
                    query = """
                        INSERT INTO case_transfers (
                            case_id, registration_number, transfer_date,
                            from_court, to_court, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    self.cursor.execute(query, (
                        case_id, transfer['registration_number'],
                        transfer_date, transfer['from_court'],
                        transfer['to_court']
                    ))
                    self.connection.commit()

            # Insert IA details
            if case_details.get('ia_details'):
                for ia in case_details['ia_details']:
                    dt_filing = self._parse_date(ia.get('dt_filing'))
                    dt_reg = self._parse_date(ia.get('next_date'))  # Use next_date as dt_reg
                    
                    # Get or create litigant for IA party
                    ia_party_id = None
                    party_name = None
                    if ia.get('party'):
                        party_name = str(ia['party'])  # Convert to string if it's a number
                        ia_party_id = self._get_or_create_litigant(party_name)
                    
                    query = """
                        INSERT INTO case_ias (
                            case_id, ia_no, classification, ia_status,
                            dt_filing, dt_reg, ia_party_id, party,
                            status, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    self.cursor.execute(query, (
                        case_id, ia['ia_no'], ia.get('classification', 'General'),
                        ia['ia_status'], dt_filing, dt_reg,
                        ia_party_id, party_name, ia.get('ia_status', '')
                    ))
                    self.connection.commit()
                    
                    # Ensure all results are read
                    while self.cursor.nextset():
                        pass
            
            logging.info(f"Successfully saved case {case_details['cnr_number']} to database")
            return case_id
            
        except Exception as e:
            logging.error(f"Failed to save case {case_details['cnr_number']} to database: {str(e)}")
            self.connection.rollback()
            raise

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def case_exists(self, cnr_number):
        """Check if a case with the given CNR number already exists in the database"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM cases WHERE cnr_number = %s", (cnr_number,))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logging.error(f"Error checking if case exists: {str(e)}")
            return False

    def create_tables(self):
        """Create all required database tables if they don't exist."""
        try:
            with self.connection.cursor() as cursor:
                # Create categories table first
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(50) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create states table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS states (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # Create districts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS districts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100),
                        state_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (state_id) REFERENCES states(id)
                    )
                """)
                
                # Create courts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS courts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100),
                        state_id INT,
                        district_id INT,
                        category_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (state_id) REFERENCES states(id),
                        FOREIGN KEY (district_id) REFERENCES districts(id),
                        FOREIGN KEY (category_id) REFERENCES categories(id)
                    )
                """)
                
                # Create court_halls table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS court_halls (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(50),
                        court_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (court_id) REFERENCES courts(id)
                    )
                """)
                
                # Create case_types table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_types (
                        case_type_id INT AUTO_INCREMENT PRIMARY KEY,
                        short_form VARCHAR(50),
                        expanded_form VARCHAR(200),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create litigants table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS litigants (
                        litigant_id INT AUTO_INCREMENT PRIMARY KEY,
                        litigant_name VARCHAR(200),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create advocates table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS advocates (
                        advocate_id INT AUTO_INCREMENT PRIMARY KEY,
                        advocate_name VARCHAR(200),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create acts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS acts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(200) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # Create sections table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sections (
                        section_id INT AUTO_INCREMENT PRIMARY KEY,
                        section_number VARCHAR(50) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # Create act_sections table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS act_sections (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        act_id INT,
                        section_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (act_id) REFERENCES acts(id),
                        FOREIGN KEY (section_id) REFERENCES sections(section_id)
                    )
                """)
                
                # Create cases table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cases (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        cnr_number VARCHAR(20) UNIQUE,
                        case_type_id INT,
                        filing_number VARCHAR(50),
                        filing_date DATE,
                        registration_number VARCHAR(50),
                        registration_date DATE,
                        case_status VARCHAR(100),
                        first_hearing_date DATE,
                        decision_date DATE,
                        disposal_date DATE,
                        disposal_nature VARCHAR(100),
                        court_hall_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (case_type_id) REFERENCES case_types(case_type_id),
                        FOREIGN KEY (court_hall_id) REFERENCES court_halls(id)
                    )
                """)
                
                # Create case_litigants table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_litigants (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        case_id INT,
                        litigant_id INT,
                        advocate_id INT,
                        party_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (case_id) REFERENCES cases(id),
                        FOREIGN KEY (litigant_id) REFERENCES litigants(litigant_id),
                        FOREIGN KEY (advocate_id) REFERENCES advocates(advocate_id)
                    )
                """)
                
                # Create case_acts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_acts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        case_id INT,
                        act_id INT,
                        act_section_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (case_id) REFERENCES cases(id),
                        FOREIGN KEY (act_id) REFERENCES acts(id),
                        FOREIGN KEY (act_section_id) REFERENCES act_sections(id)
                    )
                """)
                
                # Create case_history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        case_id INT,
                        judge VARCHAR(100),
                        business_date DATE,
                        hearing_date DATE,
                        purpose VARCHAR(200),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                    )
                """)
                
                # Create case_transfers table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_transfers (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        case_id INT,
                        registration_number VARCHAR(50),
                        transfer_date DATE,
                        from_court VARCHAR(100),
                        to_court VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                    )
                """)
                
                # Create case_ias table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_ias (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        case_id INT,
                        ia_no VARCHAR(50),
                        classification VARCHAR(50),
                        ia_status VARCHAR(100),
                        dt_filing DATE,
                        dt_reg DATE,
                        ia_party_id INT,
                        party VARCHAR(200),
                        status VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                        FOREIGN KEY (ia_party_id) REFERENCES litigants(litigant_id)
                    )
                """)
                
                # Create last_case_number table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS last_case_number (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        cnr_number VARCHAR(20),
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert default categories
                cursor.execute("""
                    INSERT IGNORE INTO categories (name) VALUES 
                    ('High Court'),
                    ('District Court'),
                    ('Subordinate Court')
                """)
                
                self.connection.commit()
                logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating database tables: {e}")
            raise

    def get_last_case_number(self):
        """Get the last scraped case number from the database"""
        try:
            self.cursor.execute("SELECT cnr_number FROM last_case_number ORDER BY id DESC LIMIT 1")
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logging.error(f"Error getting last case number: {str(e)}")
            return None

    def update_last_case_number(self, cnr_number):
        """Update the last scraped case number in the database"""
        try:
            self.cursor.execute("""
                INSERT INTO last_case_number (cnr_number) 
                VALUES (%s) 
                ON DUPLICATE KEY UPDATE cnr_number = VALUES(cnr_number)
            """, (cnr_number,))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Error updating last case number: {str(e)}")
            self.connection.rollback()
            return False

class DatabaseHandler:
    def __init__(self):
        self.setup_logging()
        self.engine = None
        self.session = None

    def setup_logging(self):
        """Configure logging for the database handler."""
        self.logger = logging.getLogger(__name__)

    def connect(self) -> None:
        """Establish connection to MySQL database."""
        try:
            connection_string = (
                f"mysql://{MYSQL_DATABASE['user']}:{MYSQL_DATABASE['password']}"
                f"@{MYSQL_DATABASE['host']}:{MYSQL_DATABASE['port']}"
                f"/{MYSQL_DATABASE['database']}"
            )
            self.engine = create_engine(connection_string)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            self.logger.info("Successfully connected to MySQL database")
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise

    def create_table(self, table_name: str, columns: Dict[str, Any]) -> bool:
        """Create a table with the specified columns."""
        try:
            # Drop table if it exists
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
            
            # Create table
            metadata = MetaData()
            table = Table(table_name, metadata,
                Column('id', Integer, primary_key=True),
                *[Column(name, type_) for name, type_ in columns.items()]
            )
            metadata.create_all(self.engine)
            self.logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create table {table_name}: {str(e)}")
            return False

    def insert_data(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """
        Insert data into MySQL table.
        
        Args:
            table_name: Name of the table
            data: List of dictionaries containing the data to insert
        """
        try:
            df = pd.DataFrame(data)
            df.to_sql(table_name, self.engine, if_exists='append', index=False)
            self.logger.info(f"Successfully inserted {len(data)} rows into {table_name}")
        except Exception as e:
            self.logger.error(f"Failed to insert data into MySQL: {str(e)}")
            raise

    def close_connection(self) -> None:
        """Close database connection."""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        self.logger.info("Closed database connection") 