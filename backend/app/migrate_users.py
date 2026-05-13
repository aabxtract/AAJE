import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Checking for missing columns in 'users' table...")
        # Check if verified_bank_name exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='verified_bank_name';
        """))
        if not result.scalar():
            print("Adding column 'verified_bank_name' to 'users' table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN verified_bank_name VARCHAR(100);"))
            print("Column 'verified_bank_name' added.")
        else:
            print("Column 'verified_bank_name' already exists.")

        # Check for other columns that might be missing based on the model
        columns_to_check = [
            ("squad_customer_id", "VARCHAR(100)"),
            ("mono_account_id", "VARCHAR(100)"),
        ]
        
        for col_name, col_type in columns_to_check:
            result = await conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='{col_name}';
            """))
            if not result.scalar():
                print(f"Adding column '{col_name}' to 'users' table...")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                print(f"Column '{col_name}' added.")
            else:
                print(f"Column '{col_name}' already exists.")

if __name__ == "__main__":
    asyncio.run(migrate())
