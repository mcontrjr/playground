from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import shutil
import matplotlib.pyplot as plt
from fastapi.responses import StreamingResponse

from typing import List, Optional
import os
import io
from datetime import datetime
from finance import Parser, DiscoverConfig, AmexConfig, CitiConfig
from logger import log
from handler import PostgresHandler

app = FastAPI()
handler = PostgresHandler()

@app.get("/records/")
async def get_records(bank_name: Optional[str] = Query(None)) -> List[dict]:
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
        records = handler.get_records(bank_name)
        
        # You can format the results to a list of dictionaries if needed
        results = []
        for record in records:
            results.append({
                'id': record[0],
                'bank': record[1],  # Assuming first column is bank
                'date': record[2],  # Assuming second column is date
                'description': record[3],  # Assuming third column is description
                'amount': record[4],  # Assuming fourth column is amount
                'category': record[5]  # Assuming fifth column is category
            })
        return results

    except Exception as e:
        log.error(f"Error retrieving records from database: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving records from database.")
    
@app.get("/plot/")
async def plot_records(bank_name: Optional[str] = Query(None), month: Optional[int] = Query(None)):
    
    if bank_name is None:
        bank_name = ""
        log.info("No bank name passed in query. Returning all records...")
    bank_name = bank_name.upper()

    if month is None:
        return {"error": "Month must be specified"}
    month = str(month).zfill(2)
    
    try:
        records = handler.get_records(bank_name)
        log.info(f"Records for month {month}: {records}")
        
        # Filter records by specified month
        log.info(f"Filtering records for month {month}")
        results = []
        for record in records:
            rec_month = record[2].strftime("%m")
            log.info(f"Record: {record} {rec_month} {month}")
            if rec_month == month:
                log.info(f"Appending: {record} for {record[4]} amount")
                results.append({
                    'id': record[0],
                    'bank': record[1],
                    'date': record[2].strftime("%m-%d"),
                    'description': record[3],
                    'amount': record[4],
                    'category': record[5]
                })
        
        dates = [r['date'] for r in results]
        amounts = [r['amount'] for r in results]
        categories = [r['category'] for r in results]
        log.info(f"Dates: {dates}\nAmounts: {amounts}\nCategories: {categories}")

        # Create a bar plot with colors based on categories
        unique_categories = list(set(categories))
        colors = plt.cm.get_cmap('tab10', len(unique_categories))
        color_map = {category: colors(i) for i, category in enumerate(unique_categories)}
        bar_colors = [color_map[category] for category in categories]

        plt.figure(figsize=(10, 6))
        _ = plt.bar(dates, amounts, color=bar_colors)
        plt.title(f'Records for {bank_name} - Month: {month}')
        plt.xlabel('Day of the Month')
        plt.ylabel('Amount')
        plt.xticks(dates, rotation=90)
        plt.grid(True)

        # Add legend
        handles = [plt.Line2D([0], [0], color=color_map[category], lw=4) for category in unique_categories]
        plt.legend(handles, unique_categories, title='Category')
        
        # Save plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        time = datetime.now()
        file_path = f"{os.path.curdir}/logs/plots/{month}_request_{time}.png"
        log.info(f"Saving plot to {file_path}")
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        plt.savefig(file_path)
        plt.close()
        
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        log.error("An error occurred while plotting records: %s", e)
        return {"error": "An error occurred while processing your request"}

@app.post("/parse/")
async def parse_upload_file(bank_name: str = File(...), pdf_files: List[UploadFile] = File(...)):
    log.info(f"Received bank name: '{bank_name}'")
    bank_name = bank_name.upper()
    
    bank_configs = {
        'DISCOVER': DiscoverConfig(),
        'AMEX': AmexConfig(),
        'CITI': CitiConfig()
    }
    
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
        statement = Parser(pdf_path, bank_configs[bank_name])
        handler.save_to_database(statement.purchases)
        
    return {"status": "success", "message": "File processed and data saved to database"}