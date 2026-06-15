from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine_kwargs = {"echo": False}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def add_missing_model_columns(connection):
    """Add newly introduced model columns to an existing database.

    ``Base.metadata.create_all`` creates missing tables, but it does not alter
    existing tables. AAJE's schema has moved from the older WhatsApp/banking
    shape into the storefront platform shape, so existing dev and hosted
    databases can lag behind the current SQLAlchemy models.

    This shim is intentionally additive: it creates missing columns only and
    leaves existing data, constraints, and indexes untouched.
    """
    if connection.dialect.name not in {"sqlite", "postgresql"}:
        return

    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns or column.primary_key:
                continue
            column_type = column.type.compile(dialect=connection.dialect)
            quoted_table = connection.dialect.identifier_preparer.quote(table.name)
            quoted_column = connection.dialect.identifier_preparer.quote(column.name)
            try:
                connection.exec_driver_sql(
                    f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} {column_type}"
                )
            except Exception:
                # Column likely already exists, safe to ignore
                pass


def normalize_known_schema_drift(connection):
    """Repair known legacy schema details that column backfill cannot cover."""
    if connection.dialect.name != "postgresql":
        return

    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())

    if "users" in existing_tables:
        connection.exec_driver_sql("ALTER TABLE users ALTER COLUMN whatsapp_no DROP NOT NULL")

    if "order_items" in existing_tables:
        connection.exec_driver_sql(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_attribute
                    WHERE attrelid = 'order_items'::regclass
                      AND attname = 'total_price'
                      AND attgenerated <> ''
                ) THEN
                    ALTER TABLE order_items ALTER COLUMN total_price DROP EXPRESSION;
                END IF;
            END $$;
            """
        )

    if "stores" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("stores")}
        if "slug" not in columns:
            connection.exec_driver_sql("ALTER TABLE stores ADD COLUMN slug VARCHAR(180)")
        if "store_slug" not in columns:
            connection.exec_driver_sql("ALTER TABLE stores ADD COLUMN store_slug VARCHAR(180)")
        connection.exec_driver_sql(
            """
            UPDATE stores
            SET slug = COALESCE(
                NULLIF(slug, ''),
                NULLIF(store_slug, ''),
                'store-' || replace(id::text, '-', '')
            )
            WHERE slug IS NULL OR slug = ''
            """
        )
        connection.exec_driver_sql(
            """
            UPDATE stores
            SET store_slug = COALESCE(NULLIF(store_slug, ''), slug)
            WHERE store_slug IS NULL OR store_slug = ''
            """
        )
        connection.exec_driver_sql("ALTER TABLE stores ALTER COLUMN slug SET NOT NULL")
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_stores_slug ON stores(slug)"
        )
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_stores_store_slug "
            "ON stores(store_slug) WHERE store_slug IS NOT NULL"
        )


add_missing_sqlite_columns = add_missing_model_columns


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
