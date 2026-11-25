"""
One-time script to filter mandi_data.csv to only Andhra Pradesh rows.
This dramatically reduces file size and speeds up server startup.
"""
import pandas as pd
import os
import shutil

DATA_FILE = os.path.join(os.path.dirname(__file__), "mandi_data.csv")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "mandi_data_backup.csv")

def filter_to_ap():
    if not os.path.exists(DATA_FILE):
        print("No mandi_data.csv found!")
        return

    print(f"Loading {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    total_rows = len(df)
    print(f"Total rows: {total_rows}")
    
    if 'state' not in df.columns:
        print("No 'state' column found. Cannot filter.")
        return

    # Show state distribution
    print("\nState distribution:")
    print(df['state'].value_counts().head(10))

    # Filter
    ap_df = df[df['state'] == 'Andhra Pradesh'].copy()
    ap_rows = len(ap_df)
    print(f"\nAP rows: {ap_rows} ({ap_rows/total_rows*100:.1f}%)")
    
    if ap_df.empty:
        print("WARNING: No Andhra Pradesh data found! Not replacing file.")
        return

    # Backup original
    print(f"Backing up original to {BACKUP_FILE}...")
    shutil.copy2(DATA_FILE, BACKUP_FILE)

    # Save filtered
    ap_df.to_csv(DATA_FILE, index=False)
    
    old_size_mb = os.path.getsize(BACKUP_FILE) / (1024*1024)
    new_size_mb = os.path.getsize(DATA_FILE) / (1024*1024)
    
    print(f"\n✓ Done!")
    print(f"  Old size: {old_size_mb:.1f} MB ({total_rows} rows)")
    print(f"  New size: {new_size_mb:.1f} MB ({ap_rows} rows)")
    print(f"  Reduction: {(1 - new_size_mb/old_size_mb)*100:.1f}%")

if __name__ == "__main__":
    filter_to_ap()
