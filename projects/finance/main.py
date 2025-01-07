from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import shutil
import psycopg2
from typing import List, Optional
import os

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

@app.post("/parse/")
async def parse_upload_file(bank_name: str = File(...), pdf_file: UploadFile = File(...)):
    bank_configs = {
        'DISCOVER': DiscoverConfig(),
        'AMEX': AmexConfig(),
        'CITI': CitiConfig()
    }
    
    log.info(f"Received bank name: '{bank_name}'")
    log.info(f"Received pdf file: {pdf_file.filename}")
    
    # Save the uploaded file
    pdf_path = f"./uploads/{pdf_file.filename}"
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(pdf_file.file, buffer)
        

    log.info(f"Received bank name: {bank_name}")
    # Determine the bank configuration
    bank_config = None
    if bank_name.upper() in bank_configs.keys():
        bank_config = bank_configs[bank_name.upper()]
    else:
        raise HTTPException(status_code=400, detail="Invalid bank name.")

    statement = Parser(pdf_path, bank_config)
    handler.save_to_database(statement.purchases)
    
    return {"status": "success", "message": "File processed and data saved to database"}