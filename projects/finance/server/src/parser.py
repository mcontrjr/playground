#!/usr/bin/python3
import os
import argparse
import re
import os
from typing import List
from datetime import datetime
from pypdf import PdfReader, PageObject
from pypdf.errors import PdfReadError
from dotenv import load_dotenv

from src.handler import PostgresHandler
from src.logger import log

load_dotenv()

# Bank Configurations
class BankConfig():
    def __init__(self, bank: str, start_index: int = 0, date_pattern: str = r'^\d{2}\/\d{2}\/\d{2}', skip_date_in_desc: bool = True):
        self.bank = bank
        self.start_index = start_index
        self.date_pattern = date_pattern
        self.skip_date_in_desc = skip_date_in_desc

class DiscoverConfig(BankConfig):
    def __init__(self):
        super().__init__('DISCOVER', skip_date_in_desc=False)

class AmexConfig(BankConfig):
    def __init__(self):
        super().__init__('AMEX', start_index=2)

class CitiConfig(BankConfig):
    def __init__(self):
        super().__init__('CITI', start_index=1, date_pattern=r'^\d{2}\/\d{2}', skip_date_in_desc=False)
        
        
class DatabaseHandler:
    def __init__(self, config: dict):
        self.config = config

# Finance Parser
class Parser:
    keyword_to_category = {
        'GAS': {'GAS', 'CHEVRON', 'SHELL'},
        'TRAVEL': {'AMERICAN AI', 'TRIP', 'HOTEL', 'TOLLS', 'DOUBLETREE', 'AIRLINE', 'RENTAL CAR', 'EXPEDIA', 'HERTZ', 'ALAMO', 'AVIS', 'RENT A CAR', 'LYFT'},
        'PAYPAL': {'PAYPAL'},
        'AMAZON': {'AMAZON'},
        'GROCERIES': {'TRADER JOE', 'WHOLEF', 'SPROUTS'},
        'TARGET': {'TARGET'},
        'FOOD': {'JACK IN THE BOX', 'COFFEE', 'SAFEWAY', 'IL FORNAIO', 'KEBAB', 'BBQ', 'CHIPOTLE', 'STARBUCKS', 'EATALY', 'CAFE', 'TEA', 'DUNKIN', 'DISH', 'HOUSE OF BAGELS', 'THE MELT', 'DOORDASH', 'MENDOCINO', 'PRUNEYARD CINEMAS', 'PANDA EXPRESS', 'PIZZA', 'TACOS', 'BURGER', 'RESTAURANT'},
        'AUTO': {'GEICO', 'TOYOTA'},
        'COSTCO': {'COSTCO'},
        'STREAMING': {'NETFLIX', 'PARAMOUNT+', 'DISNEYPLUS', 'PEACOCKTV'},
        'PHARMACY': {'PHARMACY', 'CVS', 'WALGREENS'},
        'GYM': {'MOVEMENT'},
        'INTERNET': {'INTERNET', 'XFINITY'},
        'LAUNDRY': {'KIOSOFT'},
        'APPLE PAY': {'APLPAY'},
        'SKI': {'SNOW.COM/VAIL'},
        'PARKING': {'PARKING', 'PARKING GARAGE'},
    }
    
    def __init__(self, path: str, config: BankConfig = None, text: str = None):
        self.path = path
        self.purchases = []
        self.config = config
        self.text = self.extract_text_from_pdf(path) if not text else text
        self.purchases = self.parse_purchases_from_text()
        
    @staticmethod
    def determine_category(description: str):
        description = description.upper()
        for category, keywords in Parser.keyword_to_category.items():
            if any(keyword in description for keyword in keywords):
                return category
        return 'OTHER'
    
    @staticmethod
    def convert_to_sql_date(date_str: str) -> str:
        """
        Converts a date string in MM/DD format to YYYY-MM-DD format.

        :param date_str: str - Date in MM/DD format
        :return: str - Date in YYYY-MM-DD format
        """
        try:
            converted_date = datetime.strptime(f"{date_str}", "%m/%d/%y")
        except ValueError:
            # If year is missing, default to current year
            current_year = datetime.now().year
            converted_date = datetime.strptime(date_str, "%m/%d")
            converted_date = converted_date.replace(year=current_year)
        return converted_date.strftime("%Y-%m-%d")

    @staticmethod
    def extract_currency(text: str):
        """
        Extracts currency values from a given text and converts them to floats

        :param text: str - A string containing currency values to be extracted.
        :return: list of floats - A list of float numbers representing the extracted currency values.
        """
        text = text.replace(' ', '')
        patterns = [
            r'-\$[\d,]+\.\d{2}',  # (-$12,300.50 or -$345.67)
            r'\$-[\d,]+\.\d{2}',  # ($-12,300.50 or $-345.67)
            r'\$[\d,]+\.\d{2}',  # ($12,300.50 or $345.67)
        ]
        earliest_match = None
        earliest_pos = len(text)
        
        for pattern in patterns:
            log.debug(f"Searching for pattern: {pattern} in text: {text}")
            match = re.search(pattern, text)
            if match and match.start() < earliest_pos:
                earliest_match = match
                earliest_pos = match.start()
            
        if earliest_match:
            clean_value = earliest_match.group().replace('$', '').replace(',', '')
            return float(clean_value)
            
        return None

    @staticmethod
    def determine_bank(pages: List[PageObject]) -> BankConfig:
        """
        Determines the bank configuration based on the file content.

        :return: BankConfig - The bank configuration object.
        """
        config = None
        main_pages = pages[0].extract_text() + pages[-1].extract_text()
        log.debug(f"First and Last page: {main_pages}")
        if 'American Express' in main_pages:
            config = AmexConfig()
        if 'Citi' in main_pages:
            config = CitiConfig()
        if 'Discover Bank' in main_pages:
            config = DiscoverConfig()
        if config is None:
            raise Exception("Could not determine bank, check the first and last pages for keywords.")
        return config
     
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        log.info(f"Opening PDF file: {pdf_path}")
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                self.config = self.determine_bank(pdf_reader.pages)
                log.info(f"Bank config determined: {self.config.bank}")
                log.info(f"Found {len(pdf_reader.pages)} pages in statement. Starting on page {self.config.start_index + 1}")
                for page in pdf_reader.pages[self.config.start_index:]:
                    new_text = page.extract_text()
                    log.debug(f"New page: {new_text}")
                    text += new_text + "\n"
            log.info(f"Successfully extracted text from PDF: {pdf_path}")
            return text
        except PdfReadError as e:
            log.error(f"PdfReadError: {e}. Check if pdf file is corrupted and in a valid format.")
            raise e
        except Exception as e:
            log.error(f"Error extracting text from PDF: {e}")
            raise e

    def extract_description(self, lines: List[str], date: re.Match) -> str:
        log.debug(f"Extracting description from lines: {lines} with date: {date.group()}")
        description = " ".join(lines)[date.end():date.endpos].strip()
        description = " ".join(description.split())
        dollar_match = re.search(r'\$', description)
        description = description[:dollar_match.start()].strip() if dollar_match else description
        # Skip if description contains a date, common in only some statements
        if self.config.skip_date_in_desc and re.search(self.config.date_pattern, description):
            log.debug(f"Found a date in description: {description}. Skipping...")
            return None
        else:
            dup_date = re.search(self.config.date_pattern, description)
            description = description[dup_date.end():].strip() if dup_date else description
        return description
    
    def parse_purchases_from_text(self) -> List[dict]:
        """
        Parses purchases from extracted text.

        :param text: Extracted text from PDF
        :return: JSON-like list of dictionaries with purchase details
        """
        log.info("Parsing extracted text...")
        purchases = []
        try:
            lines = self.text.split('\n')
            for i, line in enumerate(lines):
                if date := re.search(self.config.date_pattern, line):
                    log.debug(f"Found date: {date.group()} in line {i}: {line}")
                    if i + 2 < len(lines):
                        if (description := self.extract_description(lines[i:i+2], date)) is None:
                            log.debug(f"Description was None. Skipping...")
                            continue
                        log.debug(f"Description: {description}. Lines: {lines[i:i+2]}. Date endpos: {date.endpos}")
                        date_str = date.group()
                        sql_date = self.convert_to_sql_date(date_str)
                        amount_line = " ".join([l for l in lines[i:i+5]])
                        log.debug(f"Amount Line: {amount_line}")
                        amount = self.extract_currency(amount_line)
                        if amount is None:
                            log.debug(f"Amount wasnt found in line: {amount_line}. Skipping...")
                            continue
                        category = self.determine_category(description)
                        log.info(f"Found a purchase on {date_str} under {category} for ${amount} with description: \n\t{description}\n")
                        purchases.append({
                            'Bank': self.config.bank,
                            'Date': sql_date,
                            'Description': description,
                            'Amount': amount,
                            'Category': category
                        })
                    else:
                        log.warning("Not enough lines to parse description and amount for date: %s", line)
            log.info(f"Successfully parsed purchases from text: {purchases}")
            return purchases
        except Exception as e:
            log.error(f"Error parsing purchases from text: {e}")
            raise



def parse(statement_file):
    
    bank_configs = {
        'DISCOVER': DiscoverConfig(),
        'AMEX': AmexConfig(),
        'CITI': CitiConfig()
    }
    
    bank = None
    for name, config in bank_configs.items():
        if name in statement_file.upper():
            bank = config
    
    if bank is None:
        log.error(f"No bank config found for {statement_file.upper()}")
    
    my_parser = Parser(statement_file, bank)
    
    db = PostgresHandler()
    db.save_to_database(my_parser.purchases)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract purchases from PDF and export to CSV.')
    parser.add_argument('-p', '--pdf_path', required=True, help='Path to the input PDF file.')
    parser.add_argument('-o', '--output_path', help='Path to the output file.')
    args = parser.parse_args()

    if args.output_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Generate default output CSV path based on the input PDF file name
        base_filename = os.path.splitext(os.path.basename(args.pdf_path))[0]
        output_file = base_filename + '_purchases.csv'
        args.output_path = os.path.join(current_dir, 'csvs', output_file)

    parse(args.pdf_path)
