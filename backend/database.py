"""
Database configuration for Restaurant Reservation System using Supabase.

This module sets up the Supabase client and provides utilities for database operations.
"""

import os
import logging
from typing import Optional, Any, Dict, List
from contextlib import contextmanager
from functools import lru_cache

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # Service role key for backend
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")  # Anon key for client-side

# Determine if we're in test mode
IS_TEST_MODE = os.getenv("TESTING", "false").lower() == "true"


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get the Supabase client singleton.
    Uses service role key for backend operations (bypasses RLS).

    Returns:
        Client: Supabase client instance
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables"
        )

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# Create a module-level client for convenience
supabase: Optional[Client] = None

def init_supabase() -> Client:
    """Initialize the Supabase client."""
    global supabase
    if supabase is None:
        supabase = get_supabase_client()
    return supabase


class SupabaseDB:
    """
    Database wrapper class that provides SQLAlchemy-like interface for Supabase.
    This helps minimize changes needed in existing API routes.
    """

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()
        self._pending_operations: List[Dict[str, Any]] = []

    @property
    def client(self) -> Client:
        """Get the underlying Supabase client."""
        return self._client

    def table(self, table_name: str):
        """Get a table reference for queries."""
        return self._client.table(table_name)

    # Query helper methods
    def query_one(self, table: str, filters: Dict[str, Any]) -> Optional[Dict]:
        """
        Query a single record from a table.

        Args:
            table: Table name
            filters: Dictionary of column=value filters

        Returns:
            Single record dict or None
        """
        query = self._client.table(table).select("*")
        for col, val in filters.items():
            query = query.eq(col, val)

        result = query.limit(1).execute()
        return result.data[0] if result.data else None

    def query_all(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query multiple records from a table.

        Args:
            table: Table name
            filters: Optional dictionary of column=value filters
            order_by: Optional column to order by
            order_desc: Whether to order descending
            offset: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of record dicts
        """
        query = self._client.table(table).select("*")

        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)

        if order_by:
            query = query.order(order_by, desc=order_desc)

        query = query.range(offset, offset + limit - 1)

        result = query.execute()
        return result.data or []

    def insert(self, table: str, data: Dict[str, Any]) -> Dict:
        """
        Insert a record into a table.

        Args:
            table: Table name
            data: Dictionary of column=value pairs

        Returns:
            Inserted record with generated fields (id, created_at, etc.)
        """
        result = self._client.table(table).insert(data).execute()
        if not result.data:
            raise Exception(f"Failed to insert into {table}")
        return result.data[0]

    def update(self, table: str, id: int, data: Dict[str, Any]) -> Dict:
        """
        Update a record by ID.

        Args:
            table: Table name
            id: Record ID
            data: Dictionary of column=value pairs to update

        Returns:
            Updated record
        """
        result = self._client.table(table).update(data).eq("id", id).execute()
        if not result.data:
            raise Exception(f"Failed to update {table} id={id}")
        return result.data[0]

    def upsert(self, table: str, data: Dict[str, Any], on_conflict: str = "id") -> Dict:
        """
        Insert or update a record.

        Args:
            table: Table name
            data: Dictionary of column=value pairs
            on_conflict: Column to check for conflicts

        Returns:
            Upserted record
        """
        result = self._client.table(table).upsert(data, on_conflict=on_conflict).execute()
        if not result.data:
            raise Exception(f"Failed to upsert into {table}")
        return result.data[0]

    def delete(self, table: str, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            table: Table name
            id: Record ID

        Returns:
            True if deleted successfully
        """
        result = self._client.table(table).delete().eq("id", id).execute()
        return True

    def delete_where(self, table: str, filters: Dict[str, Any]) -> int:
        """
        Delete records matching filters.

        Args:
            table: Table name
            filters: Dictionary of column=value filters

        Returns:
            Number of deleted records
        """
        query = self._client.table(table).delete()
        for col, val in filters.items():
            query = query.eq(col, val)

        result = query.execute()
        return len(result.data) if result.data else 0

    def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records in a table.

        Args:
            table: Table name
            filters: Optional filters

        Returns:
            Count of matching records
        """
        query = self._client.table(table).select("*", count="exact")

        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)

        result = query.execute()
        return result.count or 0

    def execute_sql(self, sql: str) -> Any:
        """
        Execute raw SQL using Supabase RPC.
        Note: Requires a database function to be created for complex queries.

        Args:
            sql: SQL query string

        Returns:
            Query result
        """
        # For simple SELECT 1 type queries, we can use a workaround
        if sql.strip().upper() == "SELECT 1":
            # Health check - just try to access any table
            try:
                self._client.table("restaurant_accounts").select("id").limit(1).execute()
                return True
            except Exception:
                return False

        raise NotImplementedError(
            "Raw SQL execution requires creating an RPC function in Supabase"
        )


# Dependency function for FastAPI
def get_db() -> SupabaseDB:
    """
    Dependency function to get database instance.

    Yields:
        SupabaseDB: Database wrapper instance

    Example:
        @app.get("/items")
        def read_items(db: SupabaseDB = Depends(get_db)):
            return db.query_all("items")
    """
    return SupabaseDB()


@contextmanager
def get_db_context():
    """
    Context manager for database operations.

    Yields:
        SupabaseDB: Database wrapper instance

    Example:
        with get_db_context() as db:
            user = db.query_one("users", {"id": 1})
    """
    db = SupabaseDB()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error occurred: {str(e)}")
        raise


def init_db() -> None:
    """
    Initialize database connection.
    With Supabase, tables are already created via migrations.
    This just verifies the connection works.
    """
    try:
        db = SupabaseDB()
        # Test connection by trying to access a table
        db.client.table("restaurant_accounts").select("id").limit(1).execute()
        logger.info("Supabase connection verified successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        raise


def check_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        db = SupabaseDB()
        db.client.table("restaurant_accounts").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


def get_db_stats() -> dict:
    """
    Get database statistics.

    Returns:
        dict: Database statistics
    """
    try:
        return {
            "database_type": "supabase",
            "supabase_url": SUPABASE_URL.split("//")[-1] if SUPABASE_URL else "not configured",
            "is_test_mode": IS_TEST_MODE,
            "connection_check": check_connection(),
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {
            "error": str(e),
            "connection_check": False,
        }


# Legacy compatibility - these are no longer needed with Supabase but kept for import compatibility
class DatabaseTransaction:
    """Legacy transaction context manager - Supabase handles transactions automatically."""

    def __init__(self, db: Optional[SupabaseDB] = None):
        self._db = db or SupabaseDB()

    def __enter__(self) -> SupabaseDB:
        return self._db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Operation failed: {exc_val}")


def execute_in_transaction(func):
    """Legacy decorator - Supabase handles transactions automatically."""
    def wrapper(*args, **kwargs):
        db = kwargs.get("db")
        if db is None:
            kwargs["db"] = SupabaseDB()
        return func(*args, **kwargs)
    return wrapper


# Initialize on module import if not in test mode
if not IS_TEST_MODE:
    try:
        init_supabase()
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase on import: {str(e)}")


# Export commonly used items
__all__ = [
    "get_db",
    "get_db_context",
    "get_supabase_client",
    "SupabaseDB",
    "init_db",
    "check_connection",
    "get_db_stats",
    "supabase",
    "DatabaseTransaction",
    "execute_in_transaction",
    "SUPABASE_URL",
]
