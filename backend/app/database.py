"""
Database utilities for FastAPI application
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

from app.config import get_config


config = get_config()


# PostgreSQL connection pool (for synchronous operations)
_connection_pool = None


def get_connection_pool():
    """Get or create connection pool."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=config.db.url
        )
    return _connection_pool


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get async database connection.

    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetch("SELECT * FROM students")
    """
    conn = await asyncpg.connect(config.db.url)

    try:
        yield conn
    finally:
        await conn.close()


def get_sync_connection():
    """
    Get synchronous database connection.

    Usage:
        with get_sync_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students")
            results = cursor.fetchall()
    """
    pool = get_connection_pool()
    return pool.getconn()


def release_sync_connection(conn):
    """Release synchronous connection back to pool."""
    pool = get_connection_pool()
    pool.putconn(conn)


async def init_db():
    """Initialize database - create tables if they don't exist."""
    # Read schema file
    import os
    from pathlib import Path

    schema_path = Path(__file__).parent.parent.parent / 'database' / 'schema.sql'

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Execute schema
    async with get_db_connection() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    await conn.execute(statement)
                except Exception as e:
                    # Ignore errors about existing tables
                    if "already exists" not in str(e):
                        raise

        await conn.close()

    print("Database initialized successfully")


async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with get_db_connection() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False


class DatabaseManager:
    """Helper class for database operations."""

    def __init__(self):
        self.pool = get_connection_pool()

    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results."""
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            self.pool.putconn(conn)

    def execute_update(self, query: str, params: tuple = None):
        """Execute an update/insert/delete query."""
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        finally:
            self.pool.putconn(conn)

    def execute_insert(self, query: str, params: tuple = None):
        """Execute an insert query and return the inserted ID."""
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.fetchone()[0]
        finally:
            self.pool.putconn(conn)


# Dependency for FastAPI routes
def get_db():
    """
    FastAPI dependency for database access.

    Usage in routes:
        @app.get("/students")
        def get_students(db: DatabaseManager = Depends(get_db)):
            results = db.execute_query("SELECT * FROM students")
            return results
    """
    return DatabaseManager()
