import psycopg2
import os
from typing import Optional
from fastapi import HTTPException

from src.logger import log

## Class for a single record + objects for responses


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
            
            existing_purchases = self.get_records(None).get('records', [])
            log.debug(f"Existing purchases in database: {existing_purchases}")
            inserted = 0

            for purchase in purchases:
                if existing_purchases:
                    if any(purchase['Description'] == existing_purchase[3] and 
                        purchase['Amount'] == float(existing_purchase[4]) and 
                        purchase['Date'] == existing_purchase[2].strftime('%Y-%m-%d') 
                        for existing_purchase in existing_purchases):
                        log.info(f"Purchase {purchase} already exists in database. Skipping insertion.")
                        continue
                else:
                    log.info(f"Purchase {purchase}")
                try:
                    cur.execute("""
                        INSERT INTO bank_statements (bank, date, description, amount, category) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        (purchase['Bank'], purchase['Date'], purchase['Description'], purchase['Amount'], purchase['Category']))
                    log.info(f"Inserted purchase: {purchase}")
                    inserted += 1
                except psycopg2.IntegrityError as e:
                    conn.commit()
                    log.info(f"{e}: Purchase {purchase} already exists. Skipping insertion.")
                    conn.rollback()
                    continue
                except Exception as e:
                    conn.commit()
                    log.error(f"Error inserting purchase {purchase}: {e}")
                    conn.rollback()
                    continue
            conn.commit()
            cur.close()
            log.info(f"Inserted {inserted} new purchases into the database.")
        except Exception as e:
            log.error(f"Error saving to database: {e}")
        finally:
            if conn is not None:
                conn.close()
                
    def get_records(self, bank_name: Optional[str]) -> dict:
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
            resp = {
                'records': records,
                'count': len(records)
            }
            return resp
        except Exception as e:
            log.error(f"Error retrieving records from database: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving records from database.")
        finally:
            if conn is not None:
                conn.close()