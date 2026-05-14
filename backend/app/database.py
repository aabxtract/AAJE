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


def add_missing_sqlite_columns(connection):
    """Add newly introduced model columns to an existing local SQLite DB.

    ``Base.metadata.create_all`` creates missing tables, but it does not alter
    existing tables. Local dev databases can therefore lag behind the models.
    This additive shim keeps development webhooks from crashing on old schemas.
    """
    if connection.dialect.name != "sqlite":
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
            connection.exec_driver_sql(
                f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} {column_type}"
            )


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
