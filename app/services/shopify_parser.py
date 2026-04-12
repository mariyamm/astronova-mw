"""
Shopify data parser

This service parses Shopify line items and extracts person data from properties
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from models.shopify_order import ProductType, Gender
from services.timezone_service import timezone_service


class ShopifyDataParser:
    """Parser for Shopify order data to extract analysis information"""
    
    # Product type mapping based on SKU or title keywords
    PRODUCT_TYPE_KEYWORDS = {
        ProductType.LOVE_SYNASTRY: ["синастрия", "любовна синастрия", "love synastry", "synastry", "couple"],
        ProductType.DETAILED_ANALYSIS: ["подробен анализ", "detailed analysis", "natal", "персонален"],
        ProductType.SOLAR_RETURN: ["соларна карта", "solar return", "соларна", "solar"]
    }
    
    @staticmethod
    def detect_product_type(product_title: str, sku: Optional[str] = None) -> ProductType:
        """
        Detect product type from title or SKU
        
        Args:
            product_title: Product title
            sku: Product SKU (optional)
            
        Returns:
            ProductType enum value
        """
        title_lower = product_title.lower()
        sku_lower = sku.lower() if sku else ""
        
        # Check for solar return keywords first (more specific)
        for keyword in ShopifyDataParser.PRODUCT_TYPE_KEYWORDS[ProductType.SOLAR_RETURN]:
            if keyword in title_lower or keyword in sku_lower:
                return ProductType.SOLAR_RETURN
        
        # Check for love synastry keywords
        for keyword in ShopifyDataParser.PRODUCT_TYPE_KEYWORDS[ProductType.LOVE_SYNASTRY]:
            if keyword in title_lower or keyword in sku_lower:
                return ProductType.LOVE_SYNASTRY
        
        # Check for detailed analysis keywords
        for keyword in ShopifyDataParser.PRODUCT_TYPE_KEYWORDS[ProductType.DETAILED_ANALYSIS]:
            if keyword in title_lower or keyword in sku_lower:
                return ProductType.DETAILED_ANALYSIS
        
        # Default to detailed analysis
        return ProductType.DETAILED_ANALYSIS
    
    @staticmethod
    def parse_properties(properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse line item properties to extract person data
        
        Properties can be in various formats:
        - Direct: {"name": "Name", "value": "John Doe"}
        - Bulgarian: {"name": "Име", "value": "Иван Петров"}
        - Partner format: {"name": "Partner 1 Name", "value": "John Doe"}
        
        Args:
            properties: List of property dictionaries from Shopify
            
        Returns:
            Dictionary with parsed person data
        """
        result = {}
        props_dict = {prop["name"]: prop["value"] for prop in properties}
        
        print(f"      DEBUG: Property keys found: {list(props_dict.keys())[:10]}")  # Show first 10 keys
        
        # Try different prefixes for person 1
        person1_prefixes = ["Partner 1", "Person 1", ""]
        for prefix in person1_prefixes:
            person1_data = ShopifyDataParser._parse_person_data(
                props_dict, 
                prefix=prefix,
                person_number=1 if prefix else None
            )
            if person1_data:
                print(f"      ✅ Parsed person1 with prefix '{prefix or '(none)'}'")
                result["person1"] = person1_data
                break
        else:
            print(f"      ❌ Could not parse person1 data")
        
        # Try different prefixes for person 2
        person2_prefixes = ["Partner 2", "Person 2", "Партньор "]
        for prefix in person2_prefixes:
            person2_data = ShopifyDataParser._parse_person_data(
                props_dict, 
                prefix=prefix,
                person_number=2 if prefix and prefix != "Партньор " else None
            )
            if person2_data:
                print(f"      ✅ Parsed person2 with prefix '{prefix}'")
                result["person2"] = person2_data
                break
        
        return result
    
    @staticmethod
    def parse_person_by_number(properties: List[Dict[str, Any]], person_num: int) -> Optional[Dict[str, Any]]:
        """
        Parse data for a specific person number from properties
        
        When quantity > 1, Shopify sends all people in one line item with properties like:
        Person 1 Name, Person 2 Name, Person 3 Name, etc.
        
        Args:
            properties: List of property dictionaries from Shopify
            person_num: Which person to extract (1, 2, 3, etc.)
            
        Returns:
            Dictionary with person data or None if not found
        """
        props_dict = {prop["name"]: prop["value"] for prop in properties}
        
        # Try different prefixes for this person number
        prefixes = [f"Person {person_num}", f"Partner {person_num}"]
        
        for prefix in prefixes:
            person_data = ShopifyDataParser._parse_person_data(
                props_dict,
                prefix=prefix,
                person_number=person_num
            )
            if person_data:
                return person_data
        
        return None
    
    @staticmethod
    def _parse_person_data(props: Dict[str, str], prefix: str = "", person_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Parse data for one person from properties dictionary
        
        Args:
            props: Dictionary of property name -> value
            prefix: Prefix for property names:
                    "" = no prefix (direct properties like "Name", "Име")
                    "Partner 1" / "Person 1" = English format person 1
                    "Partner 2" / "Person 2" = English format person 2
                    "Партньор " = Bulgarian format person 2
            person_number: Person number (1 or 2) for looking up person-specific coordinates (_p1_lat, _p2_lat, etc.)
            
        Returns:
            Dictionary with person data or None if essential data is missing
        """
        # Build property name variations based on prefix
        if prefix:
            # With prefix like "Partner 1", "Person 1", or "Партньор "
            name_keys = [
                f"{prefix} Name",
                f"{prefix} Име",
                f"{prefix}Name",  # No space version
            ]
            gender_keys = [
                f"{prefix} Gender",
                f"{prefix} Пол",
                f"{prefix}Gender",
            ]
            date_keys = [
                f"{prefix} DOB",
                f"{prefix} Birth Date",
                f"{prefix} Дата на раждане",
                f"{prefix}DOB",
            ]
            time_keys = [
                f"{prefix} TOB",
                f"{prefix} Birth Time",
                f"{prefix} Час на раждане",
                f"{prefix}TOB",
            ]
            place_keys = [
                f"{prefix} POB",
                f"{prefix} Birth Place",
                f"{prefix} Място на раждане",
                f"{prefix}POB",
            ]
            birthday_location_keys = [
                f"{prefix} Birthday Location",
                f"{prefix} Място на празнуване",
                f"{prefix}Birthday Location",
            ]
            solar_year_keys = [
                f"{prefix} Solar Return Year",
                f"{prefix} Year",
                f"{prefix} Година",
                f"{prefix}Solar Return Year",
                f"{prefix}Year",
            ]
            coords_keys = [
                f"{prefix} Coordinates",
                f"{prefix} Координати",
                f"{prefix}Coordinates",
            ]
        else:
            # No prefix - direct property names
            name_keys = ["Name", "Име"]
            gender_keys = ["Gender", "Пол"]
            date_keys = ["DOB", "Birth Date", "Дата на раждане"]
            time_keys = ["TOB", "Birth Time", "Час на раждане"]
            place_keys = ["POB", "Birth Place", "Място на раждане"]
            birthday_location_keys = ["Birthday Location", "Място на празнуване"]
            solar_year_keys = ["Solar Return Year", "Year", "Година"]
            coords_keys = ["Coordinates", "Координати"]
        
        # Common latitude/longitude keys (used across all formats)
        lat_keys = ["_latitude", "latitude", "Latitude"]
        lon_keys = ["_longitude", "longitude", "Longitude"]
        
        # Add person-specific coordinate keys if person_number is provided
        if person_number:
            # Add numbered coordinate fields with priority
            lat_keys = [
                f"_p{person_number}_lat",
                f"_partner{person_number}_lat"
            ] + lat_keys
            lon_keys = [
                f"_p{person_number}_lng",
                f"_partner{person_number}_lng"
            ] + lon_keys
            
            # Add birthday location coordinate keys for Solar Return
            birthday_lat_keys = [
                f"_pb{person_number}_lat",
                f"_birthday{person_number}_lat"
            ]
            birthday_lon_keys = [
                f"_pb{person_number}_lng",
                f"_birthday{person_number}_lng"
            ]
        else:
            birthday_lat_keys = ["_birthday_lat", "_pb_lat"]
            birthday_lon_keys = ["_birthday_lng", "_pb_lng"]
        
        # Get values
        name = ShopifyDataParser._get_value(props, name_keys)
        gender_str = ShopifyDataParser._get_value(props, gender_keys)
        date_str = ShopifyDataParser._get_value(props, date_keys)
        time_str = ShopifyDataParser._get_value(props, time_keys)
        place = ShopifyDataParser._get_value(props, place_keys)
        solar_year_str = ShopifyDataParser._get_value(props, solar_year_keys)
        birthday_location = ShopifyDataParser._get_value(props, birthday_location_keys)
        coords_str = ShopifyDataParser._get_value(props, coords_keys)
        
        # Try to get latitude/longitude
        latitude = None
        longitude = None
        
        if coords_str:
            # Parse combined coordinates
            try:
                coords_parts = coords_str.replace(" ", "").split(",")
                latitude = float(coords_parts[0])
                longitude = float(coords_parts[1])
            except (ValueError, IndexError):
                pass
        
        # If combined coords failed or not found, try separate lat/lon fields
        if latitude is None or longitude is None:
            lat_str = ShopifyDataParser._get_value(props, lat_keys)
            lon_str = ShopifyDataParser._get_value(props, lon_keys)
            if lat_str and lon_str:
                try:
                    latitude = float(lat_str)
                    longitude = float(lon_str)
                except ValueError:
                    pass
        
        # Try to get birthday location coordinates (for Solar Return)
        birthday_latitude = None
        birthday_longitude = None
        
        birthday_lat_str = ShopifyDataParser._get_value(props, birthday_lat_keys)
        birthday_lon_str = ShopifyDataParser._get_value(props, birthday_lon_keys)
        if birthday_lat_str and birthday_lon_str:
            try:
                birthday_latitude = float(birthday_lat_str)
                birthday_longitude = float(birthday_lon_str)
            except ValueError:
                pass
        
        # Check essential fields
        if not all([name, date_str, place]) or latitude is None or longitude is None:
            return None
        
        # Parse birth datetime
        try:
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",      # 1990-05-15
                "%d/%m/%Y",      # 15/05/1990
                "%m/%d/%Y",      # 05/15/1990
                "%d/%m/%y",      # 15/05/90 (2-digit year)
                "%m/%d/%y",      # 05/15/90 (2-digit year)
            ]
            
            birth_date = None
            for fmt in date_formats:
                try:
                    birth_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not birth_date:
                return None
            
            # Add time if available
            if time_str:
                try:
                    time_formats = ["%H:%M", "%H:%M:%S", "%I:%M %p"]
                    time_obj = None
                    for time_fmt in time_formats:
                        try:
                            time_obj = datetime.strptime(time_str, time_fmt).time()
                            break
                        except ValueError:
                            continue
                    
                    if time_obj:
                        birth_date = datetime.combine(birth_date.date(), time_obj)
                except ValueError:
                    pass  # Use date only if time parsing fails
                    
        except Exception:
            return None
        
        # Parse gender
        gender = ShopifyDataParser._parse_gender(gender_str)
        
        result = {
            "name": name,
            "gender": gender,
            "birth_date": birth_date,
            "birth_place": place,
            "latitude": latitude,
            "longitude": longitude
        }
        
        # Add birthday location data if present (for Solar Return)
        if birthday_location:
            result["birthday_location"] = birthday_location
        if birthday_latitude is not None:
            result["birthday_latitude"] = birthday_latitude
        if birthday_longitude is not None:
            result["birthday_longitude"] = birthday_longitude
        # Add solar return year if present (for Solar Return)
        if solar_year_str:
            try:
                solar_year = int(solar_year_str.strip())
                if 2000 <= solar_year <= 2100:  # Validate reasonable year range
                    result["solar_return_year"] = solar_year
            except ValueError:
                pass  # Ignore if year can't be parsed
        
        
        return result
    
    @staticmethod
    def _get_value(props: Dict[str, str], keys: List[str]) -> Optional[str]:
        """Get value from dictionary trying multiple keys"""
        for key in keys:
            if key in props and props[key]:
                return props[key].strip()
        return None
    
    @staticmethod
    def _parse_gender(gender_str: Optional[str]) -> Optional[Gender]:
        """Parse gender string to Gender enum"""
        if not gender_str:
            return None
        
        gender_lower = gender_str.lower()
        
        # Male variations
        if any(word in gender_lower for word in ["male", "мъж", "м", "m"]):
            return Gender.MALE
        
        # Female variations
        if any(word in gender_lower for word in ["female", "жена", "ж", "f"]):
            return Gender.FEMALE
        
        return Gender.OTHER
    
    @staticmethod
    async def enrich_with_timezone(person_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add timezone information to person data
        
        Args:
            person_data: Dictionary with person data including latitude/longitude
            
        Returns:
            Updated dictionary with timezone information
        """
        latitude = person_data.get("latitude")
        longitude = person_data.get("longitude")
        birth_date = person_data.get("birth_date")
        
        if latitude and longitude:
            timestamp = int(birth_date.timestamp()) if birth_date else None
            timezone_name, timezone_offset = await timezone_service.get_timezone_from_coordinates(
                latitude, longitude, timestamp
            )
            
            person_data["timezone"] = timezone_name
            person_data["timezone_offset"] = timezone_offset
        
        return person_data


shopify_parser = ShopifyDataParser()
