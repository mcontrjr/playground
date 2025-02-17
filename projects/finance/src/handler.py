import psycopg2
import os
from typing import Optional
from fastapi import HTTPException

from src.logger import log


class PostgresHandler:
    def __init__(self):
        self.config = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def save_to_database(self, purchases: list):
        """
        Appends purchases from statements into a DB. DB is configured to only accept unique description entries.
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            cur = conn.cursor()

            for purchase in purchases:
                try:
                    cur.execute("""
                        INSERT INTO bank_statements (bank, date, description, amount, category) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        (purchase['Bank'], purchase['Date'], purchase['Description'], purchase['Amount'], purchase['Category']))
                except psycopg2.IntegrityError:
                    log.info(f"Entry with description '{purchase['Description']}' already exists. Skipping insertion.")
                    conn.rollback()
                    continue
            conn.commit()
            cur.close()
            log.info(f"{len(purchases)} purchases successfully saved to database.")
        except Exception as e:
            log.error(f"Error saving to database: {e}")
        finally:
            if conn is not None:
                conn.close()
                
    def get_records(self, bank_name: Optional[str]):
        conn = None
        records = []
        try:
            conn = psycopg2.connect(**self.config)
            cur = conn.cursor()
            
            query = "SELECT * FROM bank_statements"
            if bank_name:
                query += " WHERE bank = %s"
                cur.execute(query, (bank_name,))
            else:
                cur.execute(query)
            log.info(f"Query: {query}")
            
            records = cur.fetchall()
            log.info(f"Retrieved {len(records)} records from the database.")
            
            return records
        except Exception as e:
            log.error(f"Error retrieving records from database: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving records from database.")
        finally:
            if conn is not None:
                conn.close()