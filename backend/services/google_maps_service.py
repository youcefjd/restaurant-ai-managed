"""
Google Maps Places API service for fetching restaurant information and operating hours.
"""

import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    import googlemaps
except ImportError:
    googlemaps = None

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service for interacting with Google Maps Places API."""
    
    def __init__(self):
        """Initialize Google Maps client with API key from environment."""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set. Google Maps features will be disabled.")
            self.client = None
        elif googlemaps is None:
            logger.warning("googlemaps package not installed. Google Maps features will be disabled.")
            self.client = None
        else:
            try:
                self.client = googlemaps.Client(key=api_key)
                logger.info("Google Maps client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps client: {str(e)}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Google Maps service is available."""
        return self.client is not None
    
    def search_places(self, query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for places using Google Maps Places API.
        
        Args:
            query: Search query (e.g., "restaurant name" or "restaurant name, city")
            location: Optional location bias (e.g., "New York, NY")
        
        Returns:
            List of place dictionaries with id, name, address, etc.
        """
        if not self.is_available():
            raise ValueError("Google Maps API is not configured. Please set GOOGLE_MAPS_API_KEY environment variable.")
        
        try:
            # Use Places API Text Search
            if location:
                query_with_location = f"{query} {location}"
            else:
                query_with_location = query
            
            # Search for places
            places_result = self.client.places(query=query_with_location, type='restaurant')
            
            results = []
            for place in places_result.get('results', []):
                place_data = {
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'formatted_address': place.get('formatted_address'),
                    'vicinity': place.get('vicinity'),
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'geometry': place.get('geometry'),
                    'types': place.get('types', []),
                }
                results.append(place_data)
            
            logger.info(f"Found {len(results)} places for query: {query}")
            return results
        
        except Exception as e:
            logger.error(f"Error searching Google Maps places: {str(e)}")
            raise
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a place including operating hours.
        
        Args:
            place_id: Google Maps place ID
        
        Returns:
            Dictionary with place details including opening_hours
        """
        if not self.is_available():
            raise ValueError("Google Maps API is not configured. Please set GOOGLE_MAPS_API_KEY environment variable.")
        
        try:
            # Get place details
            place_details = self.client.place(
                place_id=place_id,
                fields=[
                    'name',
                    'formatted_address',
                    'formatted_phone_number',
                    'opening_hours',
                    'website',
                    'rating',
                    'user_ratings_total',
                    'geometry',
                    'types'
                ]
            )
            
            result = place_details.get('result', {})
            
            # Extract and format operating hours
            opening_hours = result.get('opening_hours', {})
            periods = opening_hours.get('periods', [])
            weekday_text = opening_hours.get('weekday_text', [])
            
            # Convert Google Maps hours format to our format
            operating_hours_data = self._parse_opening_hours(periods, weekday_text)
            
            place_data = {
                'place_id': place_id,
                'name': result.get('name'),
                'formatted_address': result.get('formatted_address'),
                'formatted_phone_number': result.get('formatted_phone_number'),
                'website': result.get('website'),
                'rating': result.get('rating'),
                'user_ratings_total': result.get('user_ratings_total'),
                'geometry': result.get('geometry'),
                'types': result.get('types', []),
                'opening_hours': operating_hours_data,
                'is_open_now': opening_hours.get('open_now', False),
            }
            
            logger.info(f"Retrieved place details for place_id: {place_id}")
            return place_data
        
        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")
            raise
    
    def _parse_opening_hours(self, periods: List[Dict], weekday_text: List[str]) -> Dict[str, Any]:
        """
        Parse Google Maps opening hours format into our format.
        
        Google Maps format:
        - periods: [{"open": {"day": 0, "time": "0900"}, "close": {"day": 0, "time": "2200"}}, ...]
        - weekday_text: ["Monday: 9:00 AM – 10:00 PM", ...]
        
        Our format:
        - operating_days: [0, 1, 2, 3, 4, 5, 6] (Monday-Sunday)
        - opening_time: "09:00"
        - closing_time: "22:00"
        """
        if not periods:
            return {
                'operating_days': [],
                'opening_time': None,
                'closing_time': None,
                'weekday_text': weekday_text
            }
        
        # Group periods by day to find common hours
        # For simplicity, we'll use the first period's hours as the standard
        # In a more sophisticated implementation, we could handle different hours per day
        
        # Find the most common opening/closing times
        opening_times = {}
        closing_times = {}
        operating_days = set()
        
        for period in periods:
            open_info = period.get('open', {})
            close_info = period.get('close', {})
            
            if open_info and close_info:
                day = open_info.get('day')
                open_time = open_info.get('time', '')
                close_time = close_info.get('time', '')
                
                if day is not None and open_time and close_time:
                    operating_days.add(day)
                    # Convert "0900" to "09:00"
                    formatted_open = f"{open_time[:2]}:{open_time[2:]}"
                    formatted_close = f"{close_time[:2]}:{close_time[2:]}"
                    
                    time_key = f"{formatted_open}-{formatted_close}"
                    if time_key not in opening_times:
                        opening_times[time_key] = formatted_open
                        closing_times[time_key] = formatted_close
        
        # Use the most common hours (or first if all same)
        if opening_times:
            # For now, use the first time slot
            # In production, you might want to handle multiple time slots per day
            time_key = list(opening_times.keys())[0]
            opening_time = opening_times[time_key]
            closing_time = closing_times[time_key]
        else:
            opening_time = None
            closing_time = None
        
        return {
            'operating_days': sorted(list(operating_days)),
            'opening_time': opening_time,
            'closing_time': closing_time,
            'weekday_text': weekday_text,
            'periods': periods  # Keep raw data for reference
        }


# Global instance
google_maps_service = GoogleMapsService()
