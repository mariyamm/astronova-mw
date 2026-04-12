"""
Models for Shopify orders and astrological analyses
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import enum


class ProductType(str, enum.Enum):
    """Product types for astrological analyses"""
    LOVE_SYNASTRY = "love_synastry"  # Любовна синастрия
    DETAILED_ANALYSIS = "detailed_analysis"  # Подробен анализ
    SOLAR_RETURN = "solar_return"  # Соларна карта


class Gender(str, enum.Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ShopifyOrder(Base):
    """Shopify order stored locally"""
    __tablename__ = "shopify_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    shopify_order_id = Column(String(100), unique=True, index=True, nullable=False)
    order_number = Column(String(50), nullable=False)
    customer_name = Column(String(200))
    customer_email = Column(String(200))
    customer_phone = Column(String(50))
    total_price = Column(String(50))
    currency = Column(String(10))
    financial_status = Column(String(50))
    fulfillment_status = Column(String(50))
    order_created_at = Column(DateTime(timezone=True))
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Raw JSON data from Shopify
    raw_data = Column(Text)
    
    # Relationships
    analyses = relationship(
        "Analysis",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="Analysis.id"
    )
    
    def __repr__(self):
        return f"<ShopifyOrder #{self.order_number}>"


class Analysis(Base):
    """Individual analysis for a person or couple"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to Shopify order
    order_id = Column(Integer, ForeignKey("shopify_orders.id", ondelete="CASCADE"), nullable=False)
    shopify_line_item_id = Column(String(100), unique=True, index=True)
    
    # Product information
    product_type = Column(Enum(ProductType), nullable=False)
    product_title = Column(String(300))
    variant_title = Column(String(300))
    sku = Column(String(100))
    quantity = Column(Integer, default=1)
    price = Column(String(50))
    
    # Person 1 data (primary person or first person in couple)
    person1_name = Column(String(200), nullable=False)
    person1_gender = Column(Enum(Gender))
    person1_birth_date = Column(DateTime(timezone=True), nullable=False)
    person1_birth_place = Column(String(300), nullable=False)
    person1_latitude = Column(Float, nullable=False)
    person1_longitude = Column(Float, nullable=False)
    person1_timezone = Column(String(100))  # e.g., "Europe/Sofia"
    person1_timezone_offset = Column(String(20))  # e.g., "+02:00"
    
    # Birthday location data (for Solar Return only)
    person1_birthday_location = Column(String(300))  # Where birthday is celebrated
    person1_birthday_latitude = Column(Float)  # Birthday location coordinates
    person1_birthday_longitude = Column(Float)
    
    # Solar Return year (for Solar Return only)
    solar_return_year = Column(Integer)  # The year for the solar return (e.g. 2025, 2026)
    
    # Person 2 data (for couples only - love synastry)
    person2_name = Column(String(200))
    person2_gender = Column(Enum(Gender))
    person2_birth_date = Column(DateTime(timezone=True))
    person2_birth_place = Column(String(300))
    person2_latitude = Column(Float)
    person2_longitude = Column(Float)
    person2_timezone = Column(String(100))
    person2_timezone_offset = Column(String(20))
    
    # Status tracking
    is_processed = Column(Boolean, default=False)
    notes = Column(Text)

    # Google Drive link (persisted from latest PDF generation)
    drive_link = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("ShopifyOrder", back_populates="analyses")
    solar_return_chart = relationship(
        "SolarReturnChart",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan"
    )
    solar_return_report = relationship(
        "SolarReturnReport",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Analysis {self.product_type.value} - {self.person1_name}>"
    
    def is_couple_analysis(self) -> bool:
        """Check if this is a couple analysis"""
        return self.product_type == ProductType.LOVE_SYNASTRY and self.person2_name is not None

    @property
    def has_solar_chart(self) -> bool:
        """True if a cached solar return chart exists for this analysis"""
        return self.solar_return_chart is not None

    @property
    def has_solar_report(self) -> bool:
        """True if an AI-generated solar report exists for this analysis"""
        return self.solar_return_report is not None


class SolarReturnChart(Base):
    """Cached solar return chart data from the Astrology API"""
    __tablename__ = "solar_return_charts"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    chart_data = Column(Text, nullable=False)  # JSON stored as text
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    analysis = relationship("Analysis", back_populates="solar_return_chart")

    def __repr__(self):
        return f"<SolarReturnChart analysis_id={self.analysis_id}>"


class SolarReturnReport(Base):
    """AI-generated solar return report sections (one row per analysis)"""
    __tablename__ = "solar_return_reports"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Report sections (HTML content)
    yearly_summary = Column(Text)        # Годината на кратко
    planetary_positions = Column(Text)   # Планетарни позиции и акценти
    life_structure = Column(Text)        # Как да структурираш живота си
    main_theme = Column(Text)            # Главната тема на годината
    yearly_details = Column(Text)        # Годината в детайли (Подробен/VIP only)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    analysis = relationship("Analysis", back_populates="solar_return_report")

    def __repr__(self):
        return f"<SolarReturnReport analysis_id={self.analysis_id}>"


class PdfJobStatus(str, enum.Enum):
    """Status of a background PDF generation job"""
    PENDING    = "pending"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"


class PdfJob(Base):
    """Tracks a background PDF generation request (one row per requested PDF)"""
    __tablename__ = "pdf_jobs"

    id             = Column(Integer, primary_key=True, index=True)
    analysis_id    = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    celery_task_id = Column(String(200), unique=True, nullable=True, index=True)
    status         = Column(Enum(PdfJobStatus), default=PdfJobStatus.PENDING, nullable=False)
    file_path      = Column(String(500), nullable=True)
    drive_file_id  = Column(String(200), nullable=True)
    drive_link     = Column(String(500), nullable=True)
    error_message  = Column(Text, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

    analysis = relationship("Analysis", backref="pdf_jobs")

    def __repr__(self):
        return f"<PdfJob id={self.id} analysis_id={self.analysis_id} status={self.status}>"

