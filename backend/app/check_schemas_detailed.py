import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name='users';
        """))
        tables = result.fetchall()
        print("Found 'users' tables in these schemas:")
        for t in tables:
            print(f" - {t[0]}.{t[1]}")

        # Now check columns for public.users
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema='public' AND table_name='users'
        """))
        print("\nColumns in public.users:")
        for col in result.fetchall():
            print(f" - {col[0]}")

if __name__ == "__main__":
    asyncio.run(check())
