"""
Reset script - truncates ALL application tables so you can test from scratch.
Schema and table structure are preserved.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

TABLES = [
    "order_items",
    "inventory_movements",
    "orders",
    "products",
    "stores",
    "transactions",
    "scores",
    "vaults",
    "virtual_accounts",
    "wallets",
    "suppliers",
    "mono_transactions",
    "failed_transfers",
    "income_streams",
    "notification_logs",
    "escalations",
    "events",
    "ledger_entries",
    "flow_sessions",
    "consents",
    "score_events",
    "bizprint_snapshots",
    "audit_logs",
    "campaign_links",
    "campaign_visits",
    "campaign_events",
    "campaign_conversions",
    "users",
]

async def reset():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        for table in TABLES:
            try:
                await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
                print(f"  OK: {table}")
            except Exception as e:
                print(f"  SKIP: {table} -- {e}")
    await engine.dispose()
    print("\nDone! All tables truncated. Database is clean for a fresh test.")

if __name__ == "__main__":
    asyncio.run(reset())
