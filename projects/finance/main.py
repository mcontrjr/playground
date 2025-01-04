from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os

# Import your existing script functionality
from finance import Parser, Discover, Amex, Citi, db_config, log

app = FastAPI()

@app.post("/parse/")
async def parse_upload_file(bank_name: str = File(...), pdf_file: UploadFile = File(...)):
    log.info(f"Received bank name: '{bank_name}'")
    log.info(f"Received pdf file: {pdf_file.filename}")
    
    # Save the uploaded file
    pdf_path = f"./uploads/{pdf_file.filename}"
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(pdf_file.file, buffer)
        

    log.info(f"Received bank name: {bank_name}")
    # Determine the bank configuration
    bank_config = None
    if bank_name.upper() == 'DISCOVER':
        bank_config = Discover
    elif bank_name.upper() == 'AMEX':
        bank_config = Amex
    elif bank_name.upper() == 'CITI':
        bank_config = Citi
    else:
        raise HTTPException(status_code=400, detail="Invalid bank name.")

    # Parse the PDF
    parser = Parser(pdf_path, bank_config)
    parser.extract_text_from_pdf(pdf_path)
    parser.parse_purchases_from_text()
    parser.save_to_database(db_config)
    
    return {"status": "success", "message": "File processed and data saved to database"}