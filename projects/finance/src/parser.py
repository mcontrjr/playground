#!/usr/bin/python3
import os
import argparse
import re
import os
from typing import List
from datetime import datetime
from pypdf import PdfReader
from dotenv import load_dotenv

from src.handler import PostgresHandler
from src.logger import log

load_dotenv()

# Bank Configurations
class BankConfig():
    def __init__(self, bank: str, start_index: int = 0):
        self.bank = bank
        self.start_index = start_index
        
class DiscoverConfig(BankConfig):
    def __init__(self):
        super().__init__('DISCOVER', start_index=2)
        
class AmexConfig(BankConfig):
    def __init__(self):
        super().__init__('AMEX', start_index=2)

class CitiConfig(BankConfig):
    def __init__(self):
        super().__init__('CITI', start_index=1)
        
class DatabaseHandler:
    def __init__(self, config: dict):
        self.config = config

# Finance Parser
class Parser:
    keyword_to_category = {
        'GAS': {'GAS', 'CHEVRON', 'SHELL'},
        'TRAVEL': {'TRIP', 'HOTEL', 'TOLLS'},
        'PAYPAL': {'PAYPAL'},
        'AMAZON': {'AMAZON'},
        'GROCERIES': {'TARGET', 'TRADER JOE', 'WHOLEF', 'SPROUTS'},
        'FOOD': {'DISH', 'HOUSE OF BAGELS', 'THE MELT', 'DOORDASH', 'MENDOCINO'},
        'AUTO': {'GEICO', 'TOYOTA'},
        'COSTCO': {'COSTCO'},
        'STREAMING': {'NETFLIX', 'PARAMOUNT+', 'DISNEYPLUS', 'PEACOCKTV'},
        'PHARMACY': {'PHARMACY', 'CVS', 'WALGREENS'},
        'GYM': {'MOVEMENT'},
        'INTERNET': {'INTERNET', 'XFINITY'},
        'LAUNDRY': {'KIOSOFT'},
        'APPLE PAY': {'APLPAY'},
        'SKI': {'SNOW.COM/VAIL'},
    }
    
    def __init__(self, path: str, config: BankConfig):
        self.path = path
        self.text = None
        self.purchases = []
        self.config = config
        if isinstance(config, BankConfig):
            self.config = config
        else:
            raise ValueError("Need a valid Config to parse!")
        
        self.text = self.extract_text_from_pdf(path)
        self.purchases = self.parse_purchases_from_text()
        
    
    @staticmethod
    def _determine_category(description: str):
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
        converted_date = datetime.strptime(f"{date_str}", "%m/%d/%y")
        return converted_date.strftime("%Y-%m-%d")
        
    @staticmethod
    def _extract_currency(text: str):
        """
        Extracts currency values from a given text and converts them to floats

        :param text: str - A string containing currency values to be extracted.
        :return: list of floats - A list of float numbers representing the extracted currency values.
        """
        # Define the regex pattern for currency (-$12,300.50 or $345.67)
        pattern = r'-?\$[\d,]+\.\d{2}'
        
        # Find all matches in the text
        match = re.search(pattern, text)
        if match:
            clean_value = match.group().replace('$', '').replace(',', '')
            return float(clean_value)
        else:
            return 0.0
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        log.info(f"Opening PDF file: {pdf_path}")
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                log.info(f"Found {len(pdf_reader.pages)} pages in statement. Starting on page {self.config.start_index + 1}")
                for page in pdf_reader.pages[self.config.start_index:]:
                    new_text = page.extract_text()
                    log.debug(f"New page: {new_text}")
                    text += new_text + "\n"
            log.info(f"Successfully extracted text from PDF: {pdf_path}")
            return text
        except Exception as e:
            log.error(f"Error extracting text from PDF: {e}")
            raise e

    def parse_purchases_from_text(self) -> List[dict]:
        """
        Parses purchases from extracted text.

        :param text: Extracted text from PDF
        :return: JSON-like list of dictionaries with purchase details
        """
        log.info("Parsing extracted text...")
        purchases = []
        try:
            date_pattern = r'^\d{2}\/\d{2}\/\d{2}'  # Regex pattern to match dates in MM/DD format
            lines = self.text.split('\n') 

            for i, line in enumerate(lines):
                if re.search(date_pattern, line):
                    date = re.search(date_pattern, line)
                    
                    if i + 2 < len(lines):
                        description = " ".join(lines[i:i+2])[date.end():date.endpos].strip()
                        log.debug(f"Description: {description}. Lines: {lines[i:i+2]}. Date endpos: {date.endpos}")
                        date_str = date.group()
                        sql_date = self.convert_to_sql_date(date_str)
                        amount_line = (lines[i] + " " + lines[i + 1]).strip()

                        amount = self._extract_currency(amount_line)
                        if amount < 0:
                            continue

                        category = self._determine_category(description)
                        log.info(f"Found a purchase on {date_str} under {category} for ${amount} with description: \n\t{description}\n")
                        log.debug(f"Current lines: {lines[i:i+2]}")
                        purchases.append({
                            'Bank': self.config.bank,
                            'Date': sql_date,
                            'Description': description,
                            'Amount': amount,
                            'Category': category
                        })
                    else:
                        log.warning("Not enough lines to parse description and amount for date: %s", line)
            log.info("Successfully parsed purchases from text")
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
