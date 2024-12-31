#!/usr/bin/python3
import os
import argparse

# from utils import Bank, BankType, Discover, Amex, Citi
import re
import os
import logging
from PyPDF2 import PdfReader

import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))

# Logging 
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to ensure file handler can capture debug logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, 'logs', 'pdf_to_csv.log')),
        logging.StreamHandler()
    ]
)

log = logging.getLogger()

for handler in log.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.INFO)

# Bank Configurations
class Config():
    def __init__(self, bank: str, start_index: int = 0):
        self.bank = bank
        self.start_index = start_index
    
Discover = Config('discover', start_index=2)
Amex = Config('amex',  start_index=2)
Citi = Config('citi', start_index=1)

# Finance Parser
class Parser:
    keyword_to_category = {
        'Gasoline': {'GAS', 'CHEVRON', 'SHELL'},
        'Travel/Entertainment': {'TRIP', 'HOTEL'},
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
    }
    
    def __init__(self, path: str, config: Config):
        self.path = path
        self.purchases = []
        self.config = config
        if isinstance(config, Config):
            self.config = config
        else:
            raise ValueError("Need a valid Config to parse!")
    
    @staticmethod
    def _determine_category(description: str):
        description = description.upper()
        for category, keywords in Parser.keyword_to_category.items():
            if any(keyword in description for keyword in keywords):
                return category
        return 'Other'
        
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
        
    def extract_text_from_pdf(self, pdf_path):
        log.info(f"Opening PDF file: {pdf_path}")
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                log.info(f"Found {len(pdf_reader.pages)} pages in statement. Starting on page {Discover.start_index + 1}")
                for page in pdf_reader.pages[self.config.start_index:]:
                    text += page.extract_text() + "\n"
            log.info(f"Successfully extracted text from PDF: {pdf_path}")
            self.text = text
        except Exception as e:
            log.error(f"Error extracting text from PDF: {e}")
            raise e

    def parse_purchases_from_text(self):
        """
        Parses purchases from extracted text.

        :param text: Extracted text from PDF
        :return: JSON-like list of dictionaries with purchase details
        """
        log.info("Parsing extracted text...")
        try:
            date_pattern = r'^\d{2}\/\d{2}'  # Regex pattern to match dates in MM/DD format
            lines = self.text.split('\n') 

            for i, line in enumerate(lines):
                log.debug(line)
                if re.search(date_pattern, line):
                    date = re.search(date_pattern, line)
                    
                    if i + 2 < len(lines):
                        # combine lines and get relevant desc from match index
                        description = " ".join(lines[i:i+2]).strip()[:date.endpos]
                        date_str = date.group()
                        amount_line = (lines[i] + " " + lines[i + 1]).strip()

                        amount = self._extract_currency(amount_line)
                        if amount < 0:
                            continue

                        category = self._determine_category(description)
                        log.info(f"Found a purchase on {date_str} under {category} for ${amount} with description: \n\t{description}\n")

                        self.purchases.append({
                            'Bank': self.config.bank,
                            'Date': date_str,
                            'Description': description,
                            'Amount': amount,
                            'Category': category
                        })
                    else:
                        log.warning("Not enough lines to parse description and amount for date: %s", line)
            log.info("Successfully parsed purchases from text")
        except Exception as e:
            log.error(f"Error parsing purchases from text: {e}")
            raise
        
    def save(self, output_path):
        try:
            df = pd.DataFrame(self.purchases)
            df.to_csv(os.path.join(current_dir, output_path), index=False)
            log.info(f"Data exported to {os.path.join(current_dir, output_path)}")
        except Exception as e:
            log.error(f"Error converting JSON to DataFrame or exporting CSV: {e}")
            log.error(e)
            return

def main(args):
    
    if Discover.bank in args.pdf_path:
        bank = Parser(args.pdf_path, Discover)
    if Amex.bank in args.pdf_path:
        bank = Parser(args.pdf_path, Amex)
    if Citi.bank in args.pdf_path:
        bank = Parser(args.pdf_path, Citi)
    
    bank.extract_text_from_pdf(args.pdf_path)
    bank.parse_purchases_from_text()
    bank.save(args.output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract purchases from PDF and export to CSV.')
    parser.add_argument('-p', '--pdf_path', required=True, help='Path to the input PDF file.')
    parser.add_argument('-o', '--output_path', help='Path to the output file.')
    args = parser.parse_args()

    if args.output_path is None:
        # Generate default output CSV path based on the input PDF file name
        base_filename = os.path.splitext(os.path.basename(args.pdf_path))[0]
        output_file = base_filename + '_purchases.csv'
        args.output_path = os.path.join(current_dir, 'csvs', output_file)

    main(args)
