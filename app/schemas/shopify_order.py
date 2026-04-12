"""
Pydantic schemas for Shopify orders and analyses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProductTypeEnum(str, Enum):
    """Product types"""
    LOVE_SYNASTRY = "love_synastry"
    DETAILED_ANALYSIS = "detailed_analysis"
    SOLAR_RETURN = "solar_return"


class GenderEnum(str, Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class PersonData(BaseModel):
    """Data for one person in an analysis"""
    name: str
    gender: Optional[GenderEnum] = None
    birth_date: datetime
    birth_place: str
    latitude: float
    longitude: float
    timezone: Optional[str] = None
    timezone_offset: Optional[str] = None
    birthday_location: Optional[str] = None  # For Solar Return
    birthday_latitude: Optional[float] = None  # For Solar Return
    birthday_longitude: Optional[float] = None  # For Solar Return
    solar_return_year: Optional[int] = None  # For Solar Return (e.g., 2025, 2026)


class AnalysisCreate(BaseModel):
    """Schema for creating an analysis"""
    product_type: ProductTypeEnum
    product_title: str
    variant_title: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = 1
    price: str
    person1: PersonData
    person2: Optional[PersonData] = None
    notes: Optional[str] = None


class AnalysisUpdate(BaseModel):
    """Schema for updating an analysis"""
    person1_name: Optional[str] = None
    person1_gender: Optional[str] = None
    person1_birth_date: Optional[str] = None
    person1_birth_place: Optional[str] = None
    person1_latitude: Optional[float] = None
    person1_longitude: Optional[float] = None
    person1_birthday_location: Optional[str] = None  # For Solar Return
    person1_birthday_latitude: Optional[float] = None  # For Solar Return
    person1_birthday_longitude: Optional[float] = None  # For Solar Return
    solar_return_year: Optional[int] = None  # For Solar Return
    person2_name: Optional[str] = None
    person2_gender: Optional[str] = None
    person2_birth_date: Optional[str] = None
    person2_birth_place: Optional[str] = None
    person2_latitude: Optional[float] = None
    person2_longitude: Optional[float] = None
    notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Schema for analysis response"""
    id: int
    order_id: int
    shopify_line_item_id: Optional[str]
    product_type: ProductTypeEnum
    product_title: str
    variant_title: Optional[str]
    sku: Optional[str]
    quantity: int
    price: str
    
    person1_name: str
    person1_gender: Optional[GenderEnum]
    person1_birth_date: datetime
    person1_birth_place: str
    person1_latitude: float
    person1_longitude: float
    person1_timezone: Optional[str]
    person1_timezone_offset: Optional[str]
    person1_birthday_location: Optional[str]
    person1_birthday_latitude: Optional[float]
    person1_birthday_longitude: Optional[float]
    solar_return_year: Optional[int]
    
    person2_name: Optional[str]
    person2_gender: Optional[GenderEnum]
    person2_birth_date: Optional[datetime]
    person2_birth_place: Optional[str]
    person2_latitude: Optional[float]
    person2_longitude: Optional[float]
    person2_timezone: Optional[str]
    person2_timezone_offset: Optional[str]
    
    is_processed: bool
    notes: Optional[str]
    drive_link: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    has_solar_chart: Optional[bool] = None  # True if chart is already cached in DB
    has_solar_report: Optional[bool] = None  # True if AI report has been generated

    class Config:
        from_attributes = True


class SolarReportSave(BaseModel):
    """Schema for saving a single report section"""
    section: str   # yearly_summary | planetary_positions | life_structure | main_theme | yearly_details
    content: str   # HTML content from the editor


class SolarReportRefine(BaseModel):
    """Schema for refining a section with a custom ChatGPT instruction"""
    user_instruction: str   # The astrologer's custom instruction
    existing_content: str   # Current HTML content from the editor


class SolarReportResponse(BaseModel):
    """Schema for reading a saved solar return report"""
    id: int
    analysis_id: int
    yearly_summary: Optional[str] = None
    planetary_positions: Optional[str] = None
    life_structure: Optional[str] = None
    main_theme: Optional[str] = None
    yearly_details: Optional[str] = None
    generated_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShopifyOrderResponse(BaseModel):
    """Schema for Shopify order response"""
    id: int
    shopify_order_id: str
    order_number: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    total_price: str
    currency: str
    financial_status: str
    fulfillment_status: Optional[str]
    order_created_at: Optional[datetime]
    synced_at: Optional[datetime]
    updated_at: Optional[datetime]
    analyses: List[AnalysisResponse] = []
    
    class Config:
        from_attributes = True
