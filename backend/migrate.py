import os
import csv
import pandas as pd
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import engine, Base, SessionLocal
from models import Mandi, Farmer, Crop, MandiDailyPrice

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def migrate_mandis_and_crops(db: Session):
    print("Migrating Mandis and Crops...")
    from master_data import MASTER_DATA, DISTRICT_MANDIS, MANDI_TO_DISTRICT
    
    # 1. Migrate Mandis
    mandi_objects = {}
    for district, mandis in DISTRICT_MANDIS.items():
        for mandi_name in mandis:
            if mandi_name not in mandi_objects:
                existing_mandi = db.query(Mandi).filter_by(name=mandi_name).first()
                if existing_mandi:
                    mandi_objects[mandi_name] = existing_mandi
                    continue
                mandi = Mandi(
                    name=mandi_name,
                    district=district,
                    state="Andhra Pradesh"
                )
                db.add(mandi)
                mandi_objects[mandi_name] = mandi
    
    # Add extra mandis from MASTER_DATA
    for mandi_name in MASTER_DATA.get("Andhra Pradesh", {}).keys():
        if mandi_name not in mandi_objects:
            existing_mandi = db.query(Mandi).filter_by(name=mandi_name).first()
            if existing_mandi:
                mandi_objects[mandi_name] = existing_mandi
                continue
            district = MANDI_TO_DISTRICT.get(mandi_name, "Unknown")
            mandi = Mandi(
                name=mandi_name,
                district=district,
                state="Andhra Pradesh"
            )
            db.add(mandi)
            mandi_objects[mandi_name] = mandi

    db.commit()
    print(f"Migrated {len(mandi_objects)} Mandis.")
    
    # 2. Migrate Crops
    all_crops = set()
    for mandi_crops in MASTER_DATA.get("Andhra Pradesh", {}).values():
        all_crops.update(mandi_crops)
        
    crop_objects = {}
    for crop_name in all_crops:
        existing_crop = db.query(Crop).filter_by(name_en=crop_name).first()
        if existing_crop:
            crop_objects[crop_name] = existing_crop
            continue
        crop = Crop(name_en=crop_name)
        db.add(crop)
        crop_objects[crop_name] = crop
        
    db.commit()
    print(f"Migrated {len(all_crops)} Crops.")

def migrate_farmers(db: Session):
    print("Migrating Farmers...")
    farmers_csv = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "farmers_data.csv"
    )
    
    if not os.path.exists(farmers_csv):
        print(f"File {farmers_csv} not found. Skipping farmers migration.")
        return

    count = 0
    with open(farmers_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_farmer = db.query(Farmer).filter_by(name=row["name"]).first()
            if existing_farmer:
                continue
            hashed_password = get_password_hash(row["password"])
            farmer = Farmer(
                id=row["id"],
                name=row["name"],
                hashed_password=hashed_password,
                state=row.get("state", "Andhra Pradesh"),
                district=row.get("district", ""),
                mandi=row.get("mandi", ""),
                crops=row.get("crops", "")
            )
            db.add(farmer)
            count += 1
            
    db.commit()
    print(f"Migrated {count} Farmers. Passwords hashed with bcrypt.")

def migrate_price_data(db: Session):
    print("Migrating Price Data (3.3 million rows)...")
    print("This will take 15-30 minutes. Please wait...")

    mandi_data_csv = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "mandi_data.csv"
    )

    if not os.path.exists(mandi_data_csv):
        print("mandi_data.csv not found. Skipping price migration.")
        return

    # Build lookup dictionaries for speed
    print("Building lookup tables...")
    mandi_lookup = {m.name: m.id for m in db.query(Mandi).all()}
    crop_lookup = {c.name_en: c.id for c in db.query(Crop).all()}

    # Debug — print sample keys to verify
    print(f"  Mandi lookup sample: {list(mandi_lookup.keys())[:3]}")
    print(f"  Crop lookup sample: {list(crop_lookup.keys())[:3]}")

    CHUNK_SIZE = 10000
    total_migrated = 0
    total_skipped = 0
    chunk_data = []

    print("Reading and inserting price data...")

    with open(mandi_data_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # ✅ Fixed column names to match your CSV
                mandi_name = row["mandi"].strip()
                crop_name = row["commodity"].strip()

                mandi_id = mandi_lookup.get(mandi_name)
                crop_id = crop_lookup.get(crop_name)

                if not mandi_id or not crop_id:
                    total_skipped += 1
                    continue

                # ✅ Fixed price column names to match your CSV
                chunk_data.append({
                    "mandi_id": mandi_id,
                    "crop_id": crop_id,
                    "price_date": row["date"].strip(),
                    "min_price": float(row["min_price"]) if row.get("min_price") else None,
                    "max_price": float(row["max_price"]) if row.get("max_price") else None,
                    "modal_price": float(row["modal_price"]) if row.get("modal_price") else None,
                    "arrivals_quantity": float(row["arrivals"]) if row.get("arrivals") else None,
                })

                if len(chunk_data) >= CHUNK_SIZE:
                    db.execute(
                        MandiDailyPrice.__table__.insert(),
                        chunk_data
                    )
                    db.commit()
                    total_migrated += len(chunk_data)
                    chunk_data = []
                    print(f"  ✅ Migrated {total_migrated:,} rows so far...")

            except Exception as e:
                total_skipped += 1
                continue

        # Insert remaining rows
        if chunk_data:
            db.execute(
                MandiDailyPrice.__table__.insert(),
                chunk_data
            )
            db.commit()
            total_migrated += len(chunk_data)

    print(f"✅ Price data migration complete!")
    print(f"   Migrated : {total_migrated:,} rows")
    print(f"   Skipped  : {total_skipped:,} rows")

def main():
    print("Starting Migration Process...")
    init_db()
    
    db = SessionLocal()
    try:
        migrate_mandis_and_crops(db)
        migrate_farmers(db)
        migrate_price_data(db)
        print("✅ Full Migration completed successfully!")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()