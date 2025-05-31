import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.parser import Parser, AmexConfig, CitiConfig, DiscoverConfig
from unittest import TestCase


class TestParser:

    def test_determine_category(self):
        assert Parser.determine_category("Chevron Gas Station") == "GAS"
        assert Parser.determine_category("Netflix Subscription") == "STREAMING"
        assert Parser.determine_category("Unknown Merchant") == "OTHER"

    def test_convert_to_sql_date(self):
        assert Parser.convert_to_sql_date("01/06") == "2025-01-06"

    def test_extract_currency(self):
        assert Parser.extract_currency("$123.45") == 123.45
        assert Parser.extract_currency("-$1,234.56") == -1234.56
        assert Parser.extract_currency("$ 123.45") == 123.45
        assert Parser.extract_currency("$ -1,234.56") == -1234.56
        assert Parser.extract_currency("$ -4.56") == -4.56
        assert Parser.extract_currency("No currency here") == None

class TestAmexParser(TestParser):

    def test_parse_purchases_from_text(self):
        with open("tests/mock_amex.txt", "r") as file:
            mock_text = file.read()
        parser = Parser("tests/dummy_path.pdf", config=AmexConfig(), text=mock_text)
        purchases = parser.parse_purchases_from_text()
        print(purchases)

        expected_purchases = [
            {
                'Bank': 'AMEX',
                'Date': "2024-07-22",
                'Description': "PRUNEYARD CINEMAS ECOMM 000000001 CAMPBELL CA",
                'Amount': 35.50,
                'Category': "FOOD"
            },
            {
                'Bank': 'AMEX',
                'Date': "2024-07-23",
                'Description': "DOUBLETREE NORWALK NORWALK CA",
                'Amount': 852.49,
                'Category': "TRAVEL"
            },
            {
                'Bank': 'AMEX',
                'Date': "2024-12-16",
                'Description': "PARAMOUNT+ WEST HOLLYWOO CA",
                'Amount': 12.99,
                'Category': "STREAMING"
            },
            {
                'Bank': 'AMEX',
                'Date': "2024-12-20",
                'Description': "AplPay STEVENS CREEK TOYOTA SAN JOSE CA",
                'Amount': 139.99,
                'Category': "AUTO"
            },
            {
                'Bank': 'AMEX',
                'Date': "2024-12-20",
                'Description': "FASTRAK CSC TOLLS OAKLAND CA",
                'Amount': 7.00,
                'Category': "TRAVEL"
            },
            {
                'Bank': 'AMEX',
                'Date': "2024-12-21",
                'Description': "AMAZON GROCE*Z99KX7LU1 AMZN.COM/BILL WA",
                'Amount': 31.70,
                'Category': "AMAZON"
            },
            {
                'Bank': 'AMEX',
                'Date': "2024-12-22",
                'Description': "SNOW.COM/VAIL RESORTS SKI 888-838-0495 CO",
                'Amount': 173.00,
                'Category': "SKI"
            }
        ]
        TestCase().assertCountEqual(purchases, expected_purchases)

class TestCitiParser(TestParser):

    def test_parse_purchases_from_text(self):
        with open("tests/mock_citi.txt", "r") as file:
            mock_text = file.read()
        parser = Parser("tests/dummy_path.pdf", config=CitiConfig(), text=mock_text)
        purchases = parser.parse_purchases_from_text()
        print(purchases)

        expected_purchases = [
            {
                'Bank': 'CITI',
                'Date': "2025-01-25",
                'Description': "LYFT *1 RIDE 01-24 LYFT.COM CA",
                'Amount': 40.09,
                'Category': "TRAVEL"
            },
            {
                'Bank': 'CITI',
                'Date': "2025-01-25",
                'Description': "SLICE*KINGKONGNYPIZZA",
                'Amount': 35.08,
                'Category': "FOOD"
            },
            {
                'Bank': 'CITI',
                'Date': "2025-01-25",
                'Description': "HOUSE OF BAGELS CAMPBELL CA",
                'Amount': 15.73,
                'Category': "FOOD"
            },
            {
                'Bank': 'CITI',
                'Date': "2025-01-20",
                'Description': "COSTCO WHSE #0129 SANTA CLARA CA",
                'Amount': 10.88,
                'Category': "COSTCO"
            },
            {
                'Bank': 'CITI',
                'Date': "2025-01-20",
                'Description': "COSTCO GAS #0129 SANTA CLARA CA",
                'Amount': 42.26,
                'Category': "GAS"
            }
        ]
        TestCase().assertCountEqual(purchases, expected_purchases)

class TestDiscoverParser(TestParser):

    def test_parse_purchases_from_text(self):
        with open("tests/mock_discover.txt", "r") as file:
            mock_text = file.read()
        parser = Parser("tests/dummy_path.pdf", config=DiscoverConfig(), text=mock_text)
        purchases = parser.parse_purchases_from_text()
        print(purchases)

        expected_purchases = [
            {
                'Bank': 'DISCOVER',
                'Date': "2025-02-24",
                'Description': "JACK IN THE BOX 0533 OAKLAND CA",
                'Amount': 13.32,
                'Category': "FOOD"
            },
            {
                'Bank': 'DISCOVER',
                'Date': "2025-02-14",
                'Description': "INTERNET PAYMENT - THANK YOU",
                'Amount': -62.93,
                'Category': "INTERNET"
            },
            {
                'Bank': 'DISCOVER',
                'Date': "2025-02-14",
                'Description': "SQ *11TH HOUR COFFEE W SANTA CRUZ CA",
                'Amount': 55.80,
                'Category': "FOOD"
            },
            {
                'Bank': 'DISCOVER',
                'Date': "2025-02-13",
                'Description': "SAFEWAY #1476 SAN JOSE CA",
                'Amount': 43.45,
                'Category': "FOOD"
            },
            {
                'Bank': 'DISCOVER',
                'Date': "2025-01-27",
                'Description': "TARGET 00014274091 SAN JOSE CA",
                'Amount': -4.64,
                'Category': "TARGET"
            },
            {
                'Bank': 'DISCOVER',
                'Date': "2025-01-26",
                'Description': "TARGET 00022814091 SAN JOSE CA",
                'Amount': 75.53,
                'Category': "TARGET"
            }
        ]
        TestCase().assertCountEqual(purchases, expected_purchases)
