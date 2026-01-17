"""
Database configuration and session management for Restaurant Reservation System.

This module sets up SQLAlchemy with SQLite database, provides session management,
and includes utilities for database initialization and connection handling.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./restaurant_reservations.db")
TEST_DATABASE_URL = "sqlite:///./test_restaurant_reservations.db"

# Determine if we're in test mode
IS_TEST_MODE = os.getenv("TESTING", "false").lower() == "true"

# Use appropriate database URL
SQLALCHEMY_DATABASE_URL = TEST_DATABASE_URL if IS_TEST_MODE else DATABASE_URL

# Create SQLAlchemy engine with appropriate configuration
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # SQLite specific configuration
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        poolclass=StaticPool if IS_TEST_MODE else None,  # Use StaticPool for tests
        echo=False,  # Set to True for SQL query logging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # Configuration for other databases (PostgreSQL, MySQL, etc.)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Maximum number of connections to maintain
        max_overflow=20,  # Maximum overflow connections
        echo=False,
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This function should be called on application startup to ensure
    all database tables exist.
    """
    try:
        # Import all models to ensure they're registered with Base
        from backend.models import Restaurant, Table, Customer, Booking, Order, Delivery  # noqa
        from backend.models_platform import (  # noqa
            RestaurantAccount, Menu, MenuCategory, MenuItem, MenuModifier, Transcript
        )

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Use with caution.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise

def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.
    
    WARNING: This will delete all data! Use with caution.
    """
    try:
        drop_db()
        init_db()
        logger.info("Database reset completed")
    except Exception as e:
        logger.error(f"Failed to reset database: {str(e)}")
        raise

def check_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

def get_db_stats() -> dict:
    """
    Get database statistics and connection pool information.
    
    Returns:
        dict: Database statistics including pool status
    """
    try:
        pool = engine.pool
        stats = {
            "database_url": SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL,
            "is_test_mode": IS_TEST_MODE,
            "connection_check": check_connection(),
        }
        
        # Add pool statistics if available
        if hasattr(pool, "size"):
            stats.update({
                "pool_size": pool.size(),
                "checked_in_connections": pool.checkedin(),
                "checked_out_connections": pool.checkedout(),
                "overflow": pool.overflow(),
                "total_connections": pool.checkedin() + pool.checkedout(),
            })
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {
            "error": str(e),
            "connection_check": False,
        }

class DatabaseTransaction:
    """
    Context manager for handling database transactions with automatic rollback.
    
    Example:
        async with DatabaseTransaction() as db:
            user = User(name="John")
            db.add(user)
            # Automatically commits on success, rolls back on exception
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize transaction context manager.
        
        Args:
            db: Optional existing database session
        """
        self._db = db
        self._should_close = db is None
        
    def __enter__(self) -> Session:
        """Enter the context manager."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager with automatic commit/rollback."""
        if exc_type is not None:
            self._db.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            try:
                self._db.commit()
            except SQLAlchemyError as e:
                self._db.rollback()
                logger.error(f"Failed to commit transaction: {str(e)}")
                raise
        
        if self._should_close:
            self._db.close()

def execute_in_transaction(func):
    """
    Decorator to execute a function within a database transaction.
    
    Args:
        func: Function to execute within transaction
        
    Returns:
        Wrapped function that executes within a transaction
        
    Example:
        @execute_in_transaction
        def create_user(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            return user
    """
    def wrapper(*args, **kwargs):
        # Check if a session is already provided
        db = kwargs.get("db")
        if db is not None:
            return func(*args, **kwargs)
        
        # Create a new session and execute within transaction
        with DatabaseTransaction() as db:
            kwargs["db"] = db
            return func(*args, **kwargs)
    
    return wrapper

# Create database tables on module import if not in test mode
if not IS_TEST_MODE:
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Failed to initialize database on import: {str(e)}")