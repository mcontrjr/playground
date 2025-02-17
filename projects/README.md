# Financial Parser

## Purpose
The Financial Parser is a tool designed to extract and categorize purchase transactions from bank statements in PDF format. It supports multiple banks and saves the parsed data into a PostgreSQL database. Additionally, it provides a FastAPI-based web service to retrieve and visualize the parsed data.

## Features
- Extracts text from PDF bank statements.
- Categorizes transactions based on predefined keywords.
- Saves parsed transactions to a PostgreSQL database.
- Provides API endpoints to retrieve and visualize transaction data.

## Supported Banks
- Discover
- Amex
- Citi

## API Specification

### GET /records/
Retrieve records from the database, optionally filtering by bank name.

**Query Parameters:**
- `bank_name` (optional): Filter results by the bank name.

**Response:**
- List of records matching the criteria.

### GET /plot/
Generate a bar plot of transactions for a specified bank and month.

**Query Parameters:**
- `bank_name` (optional): Filter results by the bank name.
- `month` (required): Specify the month to filter transactions.

**Response:**
- A PNG image of the bar plot.

### POST /parse/
Upload PDF bank statements and parse transactions.

**Form Data:**
- `bank_name` (required): The name of the bank.
- `pdf_files` (required): List of PDF files to be uploaded and parsed.

**Response:**
- Status message indicating success or failure.

## Usage
1. Ensure you have a PostgreSQL database set up and configured.
2. Install the required dependencies.
3. Run the FastAPI server.
4. Use the provided API endpoints to interact with the parsed data.

## Installation
```bash
pip install -r requirements.txt
```

## Running the Server
```bash
uvicorn main:app --reload
```

## License
This project is licensed under the MIT License.