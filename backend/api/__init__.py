"""
Restaurant Reservation System API Module

This module exports API routers for use in the main application.
"""

from . import restaurants, tables, customers, bookings, availability

__all__ = ["restaurants", "tables", "customers", "bookings", "availability"]
