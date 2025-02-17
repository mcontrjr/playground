import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.parser import Parser, AmexConfig


class TestAmexParser:
    @pytest.fixture
    def mock_extract_text(self):
        with patch('src.parser.Parser.extract_text_from_pdf') as mock_extract_text:
            with open("tests/mock_amex.txt", "r") as file:
                mock_extract_text.return_value = file.read()
            yield mock_extract_text

    def test_determine_category(self):
        assert Parser._determine_category("Chevron Gas Station") == "GAS"
        assert Parser._determine_category("Netflix Subscription") == "STREAMING"
        assert Parser._determine_category("Unknown Merchant") == "OTHER"

    def test_convert_to_sql_date(self):
        assert Parser.convert_to_sql_date("01/06/25") == f"2025-01-06"

    def test_extract_currency(self):
        assert Parser._extract_currency("$123.45") == 123.45
        assert Parser._extract_currency("-$1,234.56") == -1234.56
        assert Parser._extract_currency("No currency here") == 0.0

    def test_parse_purchases_from_text(self, mock_extract_text):
        parser = Parser("tests/dummy_path.pdf", AmexConfig())
        purchases = parser.parse_purchases_from_text()

        expected_purchases = [
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
        assert purchases == expected_purchases