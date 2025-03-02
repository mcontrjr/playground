import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.parser import Parser, AmexConfig
from unittest import TestCase


class TestAmexParser:
    @pytest.fixture
    def mock_extract_text(self):
        with patch('src.parser.Parser.extract_text_from_pdf') as mock_extract_text:
            with open("tests/mock_amex.txt", "r") as file:
                mock_extract_text.return_value = file.read()
            yield mock_extract_text
            
    @pytest.fixture
    def mock_bank_config(self):
        with patch.object(Parser, 'config', new_callable=MagicMock) as mock_bank_config:
            mock_bank_config.return_value = AmexConfig()
            yield mock_bank_config

    def test_determine_category(self):
        assert Parser.determine_category("Chevron Gas Station") == "GAS"
        assert Parser.determine_category("Netflix Subscription") == "STREAMING"
        assert Parser.determine_category("Unknown Merchant") == "OTHER"

    def test_convert_to_sql_date(self):
        assert Parser.convert_to_sql_date("01/06/25") == "2025-01-06"

    def test_extract_currency(self):
        assert Parser.extract_currency("$123.45") == 123.45
        assert Parser.extract_currency("-$1,234.56") == -1234.56
        assert Parser.extract_currency("No currency here") == None

    def test_parse_purchases_from_text(self, mock_extract_text, mock_bank_config):
        parser = Parser("tests/dummy_path.pdf")
        parser.config = mock_bank_config.return_value
        parser.text = mock_extract_text.return_value
        purchases = parser.parse_purchases_from_text()

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