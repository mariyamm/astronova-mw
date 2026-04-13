"""
Timezone calculation service

This service calculates timezone information based on geographic coordinates
"""

from datetime import datetime
from typing import Tuple, Optional
import httpx
from app.core.config import settings


class TimezoneService:
    """Service for calculating timezone from coordinates"""
    
    @staticmethod
    async def get_timezone_from_coordinates(
        latitude: float, 
        longitude: float,
        timestamp: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Get timezone information from coordinates using TimeZoneDB API
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            timestamp: Unix timestamp (optional, defaults to current time)
            
        Returns:
            Tuple of (timezone_name, timezone_offset)
            Example: ("Europe/Sofia", "+02:00")
        """
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        
        # Using TimeZoneDB API (free tier available)
        # Alternative: you can use Google Maps Time Zone API
        api_key = settings.TIMEZONEDB_API_KEY
        
        # If no API key is configured, use fallback
        if not api_key:
            return TimezoneService._calculate_timezone_fallback(longitude)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://api.timezonedb.com/v2.1/get-time-zone",
                    params={
                        "key": api_key,
                        "format": "json",
                        "by": "position",
                        "lat": latitude,
                        "lng": longitude,
                        "time": timestamp
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK":
                        timezone_name = data.get("zoneName", "UTC")
                        gmt_offset = data.get("gmtOffset", 0)
                        
                        # Convert offset to string format (+02:00)
                        hours = gmt_offset // 3600
                        minutes = (abs(gmt_offset) % 3600) // 60
                        timezone_offset = f"{'+' if hours >= 0 else '-'}{abs(hours):02d}:{minutes:02d}"
                        
                        return timezone_name, timezone_offset
        except Exception as e:
            print(f"Error fetching timezone: {e}")
        
        # Fallback: calculate basic timezone from longitude
        return TimezoneService._calculate_timezone_fallback(longitude)
    
    @staticmethod
    def _calculate_timezone_fallback(longitude: float) -> Tuple[str, str]:
        """
        Fallback method to estimate timezone from longitude
        This is approximate and should only be used when API is unavailable
        
        Args:
            longitude: Longitude coordinate
            
        Returns:
            Tuple of (timezone_name, timezone_offset)
        """
        # Rough calculation: 15 degrees of longitude = 1 hour
        offset_hours = round(longitude / 15)
        
        # Clamp to valid range
        offset_hours = max(-12, min(14, offset_hours))
        
        hours = int(offset_hours)
        timezone_offset = f"{'+' if hours >= 0 else '-'}{abs(hours):02d}:00"
        timezone_name = f"UTC{timezone_offset}"
        
        return timezone_name, timezone_offset
    
    @staticmethod
    def get_local_timezone_by_country(country_code: str) -> str:
        """
        Get default timezone for a country
        Useful for common countries
        
        Args:
            country_code: ISO country code (e.g., "BG", "US", "GB")
            
        Returns:
            Timezone name
        """
        common_timezones = {
            "BG": "Europe/Sofia",
            "GB": "Europe/London",
            "US": "America/New_York",
            "DE": "Europe/Berlin",
            "FR": "Europe/Paris",
            "IT": "Europe/Rome",
            "ES": "Europe/Madrid",
            "GR": "Europe/Athens",
            "TR": "Europe/Istanbul",
            "RU": "Europe/Moscow",
            "UA": "Europe/Kiev",
            "RO": "Europe/Bucharest",
        }
        
        return common_timezones.get(country_code.upper(), "UTC")


timezone_service = TimezoneService()
