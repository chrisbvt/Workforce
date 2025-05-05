import asyncio
import os
from app.database import reset_db

async def main():
    # Delete the SQLite database file if it exists
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "crewai.db"))
    if os.path.exists(db_path):
        print(f"Deleting existing database file: {db_path}")
        os.remove(db_path)
    
    print("Resetting database...")
    await reset_db()
    print("Database reset complete!")

if __name__ == "__main__":
    asyncio.run(main()) 