import shutil
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from typing import List, Optional
import os
import io
from datetime import datetime

from src.parser import Parser
from src.logger import log
from src.handler import PostgresHandler

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
handler = PostgresHandler()

MONTH_MAP = {
    'january': '01', 'jan': '01', '1': '01', '01': '01',
    'february': '02', 'feb': '02', '2': '02', '02': '02',
    'march': '03', 'mar': '03', '3': '03', '03': '03',
    'april': '04', 'apr': '04', '4': '04', '04': '04',
    'may': '05', 'may': '05', '5': '05', '05': '05',
    'june': '06', 'jun': '06', '6': '06', '06': '06',
    'july': '07', 'jul': '07', '7': '07', '07': '07',
    'august': '08', 'aug': '08', '8': '08', '08': '08',
    'september': '09', 'sep': '09', '9': '09', '09': '09',
    'october': '10', 'oct': '10', '10': '10',
    'november': '11', 'nov': '11', '11': '11',
    'december': '12', 'dec': '12', '12': '12'
}

def get_normalized_month(month: Optional[str]) -> Optional[str]:
    """Convert various month formats to padded number format (01-12)."""
    if month is None:
        return None
    return MONTH_MAP.get(month.lower())

def format_record(record: tuple) -> dict:
    """Format a database record into a dictionary."""
    return {
        'id': record[0],
        'bank': record[1],
        'date': record[2].strftime("%m-%d"),
        'description': record[3],
        'amount': record[4],
        'category': record[5]
    }

def filter_records_by_month(records: List[tuple], target_month: str) -> List[dict]:
    """Filter records by month and format them."""
    results = []
    for record in records:
        rec_month = record[2].strftime("%m")
        if rec_month == target_month:
            log.info(f"Appending: {record} for {record[4]} amount")
            results.append(format_record(record))
    return results

def create_plot(results: List[dict], bank: str, month: str) -> io.BytesIO:
    """Create a plot from the results and return it as a BytesIO object."""
    dates = [r['date'] for r in results]
    amounts = [r['amount'] for r in results]
    categories = [r['category'] for r in results]
    log.info(f"Dates: {dates}\nAmounts: {amounts}\nCategories: {categories}")

    # Create color mapping
    unique_categories = list(set(categories))
    colors = plt.cm.get_cmap('tab10', len(unique_categories))
    color_map = {category: colors(i) for i, category in enumerate(unique_categories)}
    bar_colors = [color_map[category] for category in categories]

    # Create plot
    plt.figure(figsize=(10, 6))
    _ = plt.bar(dates, amounts, color=bar_colors)
    plt.title(f'Records for {bank} - Month: {month}')
    plt.xlabel('Day of the Month')
    plt.ylabel('Amount')
    plt.xticks(dates, rotation=90)
    plt.grid(True)

    # Add legend
    handles = [plt.Line2D([0], [0], color=color_map[category], lw=4) for category in unique_categories]
    plt.legend(handles, unique_categories, title='Category')

    # Save plot
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Save to file system
    time = datetime.now()
    file_path = f"{os.path.curdir}/logs/plots/{month}_request_{time}.png"
    log.info(f"Saving plot to {file_path}")
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    plt.savefig(file_path)
    plt.close()

    return buf

@app.get("/records/")
async def get_records(bank_name: Optional[str] = Query(None)) -> dict:
    """
    Retrieve records from the database, optionally filtering by bank name.
    
    :param bank_name: Optional; filter results by the bank name.
    :return: List of records matching the criteria.
    """
    if bank_name is None:
        bank_name = ""
        log.info("No bank name passed in query. Returning all records...")
    bank_name = bank_name.upper()
    records = []
    try:
        response = handler.get_records(bank_name)
        records = response.get('records', [])
        
        results = []
        for record in records:
            results.append({
                'id': record[0],
                'bank': record[1],
                'date': record[2],
                'description': record[3],
                'amount': record[4],
                'category': record[5]
            })
        resp = {
            'records': results,
            'count': len(results)
        }
        return resp

    except Exception as e:
        log.error(f"Error retrieving records from database: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving records from database.")
    
@app.get("/plot/")
async def plot_records(bank: Optional[str] = Form(None), month: Optional[str] = Form(None)):
    """
    Endpoint to plot records for a specific bank and month.
    Month can be specified as number (1-12), padded number (01-12), or month name.
    """
    # Initialize bank if None
    bank = bank.upper() if bank else ""
    log.info("No bank name passed in form. Returning all records..." if not bank else f"Processing request for bank: {bank}")

    # Validate and normalize month
    month = get_normalized_month(month)
    if month is None:
        return {"error": "Month must be specified and be valid"}

    try:
        # Get records from database
        resp = handler.get_records(bank)
        records = resp.get('records', [])

        log.info(f"Records for month {month}: {records}")
        if not records:
            log.info(f"No records found for bank {bank} in month {month}")
            return {"error": "No records found for this query"}

        # Filter and format records
        results = filter_records_by_month(records, month)
        if not results:
            return {"error": "No records found for the specified month"}

        # Create and return plot
        buf = create_plot(results, bank, month)
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        log.error("An error occurred while plotting records: %s", e)
        return {"error": "An error occurred while processing your request"}

@app.post("/parse/")
async def parse_upload_file(pdf_files: List[UploadFile] = File(...)):
    """
    Endpoint to upload and parse PDF files.
    """
    log.info(f"Received {len(pdf_files)} files: {[file.filename for file in pdf_files]}")
    
    # Save the uploaded file
    os.makedirs("./uploads", exist_ok=True)
    
    for pdf_file in pdf_files:
        log.info(f"Processing pdf file: {pdf_file.filename}")
        
        # Save the uploaded file
        pdf_path = f"./uploads/{pdf_file.filename}"
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        
        # Process each PDF file
        statement = Parser(pdf_path)
        handler.save_to_database(statement.purchases)
        
    return {"status": "success", "message": "File processed and data saved to database"}