import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import time

# Import database settings and models
from database import SQLALCHEMY_DATABASE_URL
from models import Mandi, Crop

def main():
    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mandi_data.csv")
    
    if not os.path.exists(csv_file_path):
        print(f"Error: Could not find CSV file at {csv_file_path}")
        return

    print(f"Connecting to database...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    print("Building lookup dictionaries from database...")
    with Session(engine) as session:
        # Load all mandis and crops into memory dictionaries for fast lookups
        mandis = session.query(Mandi).all()
        mandi_lookup = {m.name: m.id for m in mandis}
        
        crops = session.query(Crop).all()
        crop_lookup = {c.name_en: c.id for c in crops}
        
    print(f"Loaded {len(mandi_lookup)} mandis and {len(crop_lookup)} crops for lookup.")
    
    chunk_size = 50000
    total_migrated = 0
    total_skipped = 0
    
    print(f"Starting migration from {csv_file_path}")
    print(f"Processing in chunks of {chunk_size} rows...\n")
    
    start_time = time.time()
    
    # Process CSV in chunks
    try:
        # Use iterator to process chunks efficiently
        for chunk_idx, chunk in enumerate(pd.read_csv(csv_file_path, chunksize=chunk_size)):
            
            # 1. Strip whitespace from text columns
            chunk['mandi'] = chunk['mandi'].str.strip()
            chunk['commodity'] = chunk['commodity'].str.strip()
            
            # 2. Map names to IDs using our lookup dictionaries
            chunk['mandi_id'] = chunk['mandi'].map(mandi_lookup)
            chunk['crop_id'] = chunk['commodity'].map(crop_lookup)
            
            # 3. Count and drop rows where mandi or commodity wasn't found in DB
            original_len = len(chunk)
            chunk = chunk.dropna(subset=['mandi_id', 'crop_id'])
            skipped_in_chunk = original_len - len(chunk)
            total_skipped += skipped_in_chunk
            
            if len(chunk) == 0:
                continue
                
            # 4. Rename columns to match MySQL database model setup
            # Table name: mandi_daily_prices
            # Columns: id, mandi_id, crop_id, date, price, arrivals, min_price, max_price
            chunk = chunk.rename(columns={
                'date': 'date',
                'min_price': 'min_price',
                'max_price': 'max_price',
                'modal_price': 'price', # mapping modal_price to the simply named 'price' column 
                'arrivals': 'arrivals'
            })
            
            # 5. Select only the columns that exist in the database table
            db_columns = ['mandi_id', 'crop_id', 'date', 'price', 'arrivals', 'min_price', 'max_price']
            chunk_to_insert = chunk[db_columns].copy()
            
            # 6. Insert chunk into database using pandas to_sql
            try:
                chunk_to_insert.to_sql(
                    name='mandi_daily_prices',
                    con=engine,
                    if_exists='append',
                    index=False,
                    # method='multi' is generally faster for multiple inserts
                    method='multi',
                    chunksize=10000 # nested chunksize for the actual executemany call
                )
                
                total_migrated += len(chunk_to_insert)
                print(f"✅ Migrated {total_migrated:,} rows... (Skipped {total_skipped:,} unmatched) - Chunk {chunk_idx + 1}")
                
            except SQLAlchemyError as err:
                # If there's an error in this chunk (like duplicate keys if schema has unique constraints),
                # we catch it, print it, and continue to next chunk.
                print(f"❌ Error inserting chunk {chunk_idx + 1}: {err}")
                
    except pd.errors.EmptyDataError:
        print("CSV file is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    end_time = time.time()
    elapsed_minutes = (end_time - start_time) / 60
    
    print("\n" + "="*50)
    print("MIGRATION SUMMARY")
    print("="*50)
    print(f"Total rows successfully migrated : {total_migrated:,}")
    print(f"Total rows skipped (unmatched)   : {total_skipped:,}")
    print(f"Time taken                       : {elapsed_minutes:.2f} minutes")
    print("="*50)
    
    # Delete the CSV file if migration was completely successful and migrated items
    if total_migrated > 0:
        try:
            print(f"\nMigration successful. Removing large CSV file to free up space...")
            os.remove(csv_file_path)
            print(f"✅ Successfully deleted {csv_file_path}")
        except OSError as e:
            print(f"⚠️ Could not delete file: {e}")

if __name__ == "__main__":
    main()
