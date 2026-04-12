"""
Astrology API Service

This service handles all communication with the Astrology API
for generating astrological charts and calculations.

API Documentation: https://api.astrology-api.io/
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime


class AstrologyAPIService:
    """Service for interacting with Astrology API"""
    
    BASE_URL = "https://api.astrology-api.io/api/v3"
    API_KEY = "ask_16954fd6f59bfd1a99f74d9bb3e301a4dae33fe6a2ad391af33d27a20f492abb"
    
    # Default chart options
    DEFAULT_HOUSE_SYSTEM = "P"  # Placidus  house system
    DEFAULT_ZODIAC_TYPE = "Tropic"
    DEFAULT_ACTIVE_POINTS = [
        "Sun", "Moon", "Mercury", "Venus", "Mars", 
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
        "Ascendant", "Medium_Coeli"
    ]
    
    @classmethod
    async def get_solar_return_chart(
        cls,
        name: str,
        birth_date: datetime,
        birth_latitude: float,
        birth_longitude: float,
        return_year: int,
        birthday_date: datetime,
        birthday_latitude: float,
        birthday_longitude: float,
        house_system: str = None,
        zodiac_type: str = None,
        precision: int = 6
    ) -> Dict[str, Any]:
        """
        Get Solar Return chart from Astrology API
        
        Args:
            name: Person's name
            birth_date: Birth datetime
            birth_latitude: Birth place latitude
            birth_longitude: Birth place longitude
            return_year: Solar return year (e.g., 2025)
            birthday_date: Date/time when birthday is celebrated this year
            birthday_latitude: Location latitude for birthday celebration
            birthday_longitude: Location longitude for birthday celebration
            house_system: House system to use (default: Koch)
            zodiac_type: Zodiac type (default: Tropic)
            precision: Calculation precision (default: 6)
            
        Returns:
            Solar return chart data from API
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        
        # Prepare request payload
        payload = {
            "subject": {
                "name": name,
                "birth_data": {
                    "year": birth_date.year,
                    "month": birth_date.month,
                    "day": birth_date.day,
                    "hour": birth_date.hour,
                    "minute": birth_date.minute,
                    "second": birth_date.second,
                    "latitude": birth_latitude,
                    "longitude": birth_longitude
                }
            },
            "return_year": return_year,
            "options": {
                "house_system": house_system or cls.DEFAULT_HOUSE_SYSTEM,
                "zodiac_type": zodiac_type or cls.DEFAULT_ZODIAC_TYPE,
                "active_points": cls.DEFAULT_ACTIVE_POINTS,
                "precision": precision
            },
            "return_location": {
                "day": birthday_date.day,
                "hour": birthday_date.hour,
                "minute": birthday_date.minute,
                "month": birthday_date.month,
                "year": birthday_date.year,
                "latitude": birthday_latitude,
                "longitude": birthday_longitude
            }
        }
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{cls.BASE_URL}/charts/solar-return"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    @classmethod
    async def get_natal_chart(
        cls,
        name: str,
        birth_date: datetime,
        birth_latitude: float,
        birth_longitude: float,
        house_system: str = None,
        zodiac_type: str = None,
        precision: int = 6
    ) -> Dict[str, Any]:
        """
        Get Natal chart from Astrology API
        
        Args:
            name: Person's name
            birth_date: Birth datetime
            birth_latitude: Birth place latitude
            birth_longitude: Birth place longitude
            house_system: House system to use (default: Koch)
            zodiac_type: Zodiac type (default: Tropic)
            precision: Calculation precision (default: 6)
            
        Returns:
            Natal chart data from API
        """
        
        payload = {
            "subject": {
                "name": name,
                "birth_data": {
                    "year": birth_date.year,
                    "month": birth_date.month,
                    "day": birth_date.day,
                    "hour": birth_date.hour,
                    "minute": birth_date.minute,
                    "second": birth_date.second,
                    "latitude": birth_latitude,
                    "longitude": birth_longitude
                }
            },
            "options": {
                "house_system": house_system or cls.DEFAULT_HOUSE_SYSTEM,
                "zodiac_type": zodiac_type or cls.DEFAULT_ZODIAC_TYPE,
                "active_points": cls.DEFAULT_ACTIVE_POINTS,
                "precision": precision
            }
        }
        
        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{cls.BASE_URL}/charts/natal"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


# Create a singleton instance
astrology_api = AstrologyAPIService()
