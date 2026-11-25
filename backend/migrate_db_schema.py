from sqlalchemy import text
from database import engine

def main():
    print("Connecting to database to update schema...")
    with engine.connect() as conn:
        try:
            print("Renaming 'hashed_password' to 'password'...")
            conn.execute(text("ALTER TABLE farmers CHANGE hashed_password password VARCHAR(255) NOT NULL"))
            
            print("Resetting all existing encrypted passwords to 'auto_recovered' plaintext...")
            # If any passwords start with bcrypt's $2b$, reset them to a plaintext value
            conn.execute(text("UPDATE farmers SET password = 'auto_recovered' WHERE password LIKE '$2b$%'"))
            
            conn.commit()
            print("Successfully updated database schema for plaintext passwords!")
        except Exception as e:
            print(f"Error during schema update: {e}")
            conn.rollback()

if __name__ == "__main__":
    main()
