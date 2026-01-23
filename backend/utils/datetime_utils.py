"""
Datetime utilities for consistent timezone handling.

All timestamps should be stored in UTC in the database.
Frontend is responsible for converting to local timezone for display.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Get current UTC datetime as ISO string."""
    return utc_now().isoformat()


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC. Assumes naive datetimes are in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def days_ago(days: int) -> datetime:
    """Get datetime for N days ago in UTC."""
    return utc_now() - timedelta(days=days)


def days_ago_iso(days: int) -> str:
    """Get ISO string for N days ago in UTC."""
    return days_ago(days).isoformat()


def today_start_utc() -> datetime:
    """Get start of today in UTC (midnight)."""
    now = utc_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def today_end_utc() -> datetime:
    """Get end of today in UTC (23:59:59)."""
    now = utc_now()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)


def parse_iso(iso_string: str) -> Optional[datetime]:
    """Parse ISO format datetime string safely."""
    if not iso_string:
        return None
    try:
        # Handle various ISO formats
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return to_utc(dt)
    except (ValueError, AttributeError):
        return None


def format_for_display(dt: datetime, format_str: str = '%Y-%m-%d %H:%M') -> str:
    """Format datetime for display. Note: Frontend handles timezone conversion."""
    if dt is None:
        return ''
    return dt.strftime(format_str)
