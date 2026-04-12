"""
Shopify API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import json
import hmac
import hashlib
import base64
import os
import re

from db.database import get_db
from services.shopify_client import shopify_client
from services.shopify_sync import shopify_sync_service
from models.user import User
from models.shopify_order import ShopifyOrder, Analysis, SolarReturnChart, SolarReturnReport, PdfJob, PdfJobStatus
from schemas.shopify_order import ShopifyOrderResponse, AnalysisResponse, AnalysisUpdate, SolarReportSave, SolarReportRefine, SolarReportResponse
from auth.dependencies import get_current_user
from permissions.codes import SHOPIFY_ORDERS_VIEW
from core.config import settings


router = APIRouter(prefix="/api/shopify", tags=["Shopify"])


@router.get("/orders")
async def get_shopify_orders(
    status: str = Query(default="any", description="Order status: any, open, closed, cancelled"),
    limit: int = Query(default=50, le=250, description="Number of orders to fetch"),
    created_at_min: Optional[str] = Query(default=None, description="Minimum creation date (ISO 8601)"),
    created_at_max: Optional[str] = Query(default=None, description="Maximum creation date (ISO 8601)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch orders from Shopify
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на поръчки от Shopify"
        )
    
    try:
        orders = await shopify_client.get_orders(
            status=status,
            limit=limit,
            created_at_min=created_at_min,
            created_at_max=created_at_max
        )
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при извличане на поръчки: {str(e)}"
        )


@router.get("/orders/{order_id}")
async def get_shopify_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch a single order by ID from Shopify
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на поръчки от Shopify"
        )
    
    try:
        order = await shopify_client.get_order(order_id)
        return {"order": order}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при извличане на поръчка: {str(e)}"
        )


@router.get("/orders/{order_id}/line-items")
async def get_order_line_items(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get line items for a specific order
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на поръчки от Shopify"
        )
    
    try:
        order = await shopify_client.get_order(order_id)
        line_items = shopify_client.extract_line_items(order)
        return {
            "order_id": order_id,
            "order_number": order.get("order_number"),
            "line_items": line_items,
            "count": len(line_items)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при извличане на артикули: {str(e)}"
        )


@router.get("/orders/count")
async def get_orders_count(
    status: str = Query(default="any", description="Order status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get count of orders in Shopify
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на поръчки от Shopify"
        )
    
    try:
        count = await shopify_client.get_order_count(status=status)
        return {"count": count, "status": status}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при броене на поръчки: {str(e)}"
        )


@router.post("/sync")
async def sync_shopify_orders(
    status: str = Query(default="any", description="Order status"),
    limit: int = Query(default=50, le=250, description="Number of orders to sync"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync orders from Shopify to local database
    
    This will fetch orders from Shopify and create/update them in the local database,
    including parsing line items to extract analysis data
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за синхронизиране на поръчки"
        )
    
    try:
        synced_orders = await shopify_sync_service.sync_orders_from_shopify(
            db=db,
            status=status,
            limit=limit
        )
        return {
            "message": "Синхронизацията завърши успешно",
            "synced_count": len(synced_orders),
            "synced_order_numbers": [order.order_number for order in synced_orders]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при синхронизиране: {str(e)}"
        )


@router.get("/local/orders", response_model=List[ShopifyOrderResponse])
async def get_local_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=250),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get orders from local database with analyses
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на поръчки"
        )
    
    try:
        orders = db.query(ShopifyOrder).order_by(
            ShopifyOrder.order_created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при извличане на поръчки: {str(e)}"
        )


@router.get("/local/orders/{order_id}", response_model=ShopifyOrderResponse)
async def get_local_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single order with analyses from local database
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на поръчки"
        )
    
    try:
        order = db.query(ShopifyOrder).filter(ShopifyOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Поръчката не е намерена")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при извличане на поръчка: {str(e)}"
        )


@router.delete("/local/orders/{order_id}")
async def delete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an order and all its analyses
    
    **Admin only** - Only administrators can delete orders
    """
    # Check if user is admin
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="Само администратори могат да изтриват поръчки"
        )
    
    try:
        order = db.query(ShopifyOrder).filter(ShopifyOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Поръчката не е намерена")
        
        order_number = order.order_number
        analyses_count = len(order.analyses)
        
        # Delete order (analyses will be deleted automatically due to cascade)
        db.delete(order)
        db.commit()
        
        return {
            "message": f"Поръчка #{order_number} е изтрита успешно",
            "order_id": order_id,
            "order_number": order_number,
            "deleted_analyses": analyses_count
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при изтриване на поръчка: {str(e)}"
        )


@router.put("/local/orders/{order_id}")
async def update_order(
    order_id: int,
    order_number: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    financial_status: Optional[str] = None,
    fulfillment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update order details
    
    **Admin only** - Only administrators can modify orders
    """
    # Check if user is admin
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="Само администратори могат да редактират поръчки"
        )
    
    try:
        order = db.query(ShopifyOrder).filter(ShopifyOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Поръчката не е намерена")
        
        # Update fields if provided
        if order_number is not None:
            order.order_number = order_number
        if customer_name is not None:
            order.customer_name = customer_name
        if customer_email is not None:
            order.customer_email = customer_email
        if customer_phone is not None:
            order.customer_phone = customer_phone
        if financial_status is not None:
            order.financial_status = financial_status
        if fulfillment_status is not None:
            order.fulfillment_status = fulfillment_status
        
        db.commit()
        db.refresh(order)
        
        return {
            "message": f"Поръчка #{order.order_number} е обновена успешно",
            "order": order
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при обновяване на поръчка: {str(e)}"
        )


@router.get("/local/analyses", response_model=List[AnalysisResponse])
async def get_all_analyses(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=500),
    product_type: Optional[str] = Query(default=None, description="Filter by product type"),
    is_processed: Optional[bool] = Query(default=None, description="Filter by processed status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all analyses from database with filters
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за преглед на анализи"
        )
    
    try:
        query = db.query(Analysis)
        
        if product_type:
            query = query.filter(Analysis.product_type == product_type)
        
        if is_processed is not None:
            query = query.filter(Analysis.is_processed == is_processed)
        
        analyses = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()
        
        return analyses
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при извличане на анализи: {str(e)}"
        )


@router.put("/local/analyses/{analysis_id}/mark-processed")
async def mark_analysis_processed(
    analysis_id: int,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark an analysis as processed
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за управление на анализи"
        )
    
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Анализът не е намерен")
        
        analysis.is_processed = True
        if notes:
            analysis.notes = notes
        
        db.commit()
        db.refresh(analysis)
        
        return {"message": "Анализът е маркиран като обработен", "analysis_id": analysis_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при обновяване на анализ: {str(e)}"
        )


@router.put("/local/analyses/{analysis_id}/mark-unprocessed")
async def mark_analysis_unprocessed(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark an analysis as unprocessed (reset to start over)
    
    Requires SHOPIFY_ORDERS_VIEW permission
    """
    # Check permission
    if not current_user.is_admin() and not current_user.has_permission(SHOPIFY_ORDERS_VIEW):
        raise HTTPException(
            status_code=403,
            detail="Нямате права за управление на анализи"
        )
    
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Анализът не е намерен")
        
        analysis.is_processed = False
        
        db.commit()
        db.refresh(analysis)
        
        return {"message": "Анализът е маркиран за повторна обработка", "analysis_id": analysis_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при обновяване на анализ: {str(e)}"
        )


@router.put("/local/analyses/{analysis_id}")
async def update_analysis(
    analysis_id: int,
    update_data: AnalysisUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update analysis data (admin only)

    Allows editing person data for an analysis.
    For solar return analyses, the cached chart is automatically recalculated
    in the background after any edit.
    """
    # Only admins can update analyses
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="Само администратори могат да редактират анализи"
        )

    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Анализът не е намерен")

        # Update person 1 data
        if update_data.person1_name is not None:
            analysis.person1_name = update_data.person1_name
        if update_data.person1_gender is not None:
            analysis.person1_gender = update_data.person1_gender
        if update_data.person1_birth_date is not None:
            from datetime import datetime
            analysis.person1_birth_date = datetime.fromisoformat(update_data.person1_birth_date.replace('Z', '+00:00'))
        if update_data.person1_birth_place is not None:
            analysis.person1_birth_place = update_data.person1_birth_place
        if update_data.person1_latitude is not None:
            analysis.person1_latitude = update_data.person1_latitude
        if update_data.person1_longitude is not None:
            analysis.person1_longitude = update_data.person1_longitude

        # Update birthday location data (for Solar Return)
        if update_data.person1_birthday_location is not None:
            analysis.person1_birthday_location = update_data.person1_birthday_location
        if update_data.person1_birthday_latitude is not None:
            analysis.person1_birthday_latitude = update_data.person1_birthday_latitude
        if update_data.person1_birthday_longitude is not None:
            analysis.person1_birthday_longitude = update_data.person1_birthday_longitude

        # Update solar return year
        if update_data.solar_return_year is not None:
            analysis.solar_return_year = update_data.solar_return_year

        # Update person 2 data (for couple analyses)
        if update_data.person2_name is not None:
            analysis.person2_name = update_data.person2_name
        if update_data.person2_gender is not None:
            analysis.person2_gender = update_data.person2_gender
        if update_data.person2_birth_date is not None:
            from datetime import datetime
            analysis.person2_birth_date = datetime.fromisoformat(update_data.person2_birth_date.replace('Z', '+00:00'))
        if update_data.person2_birth_place is not None:
            analysis.person2_birth_place = update_data.person2_birth_place
        if update_data.person2_latitude is not None:
            analysis.person2_latitude = update_data.person2_latitude
        if update_data.person2_longitude is not None:
            analysis.person2_longitude = update_data.person2_longitude

        if update_data.notes is not None:
            analysis.notes = update_data.notes

        is_solar_return = analysis.product_type == "solar_return"

        db.commit()
        db.refresh(analysis)

        # Recalculate solar return chart in the background after any edit
        if is_solar_return:
            background_tasks.add_task(_regenerate_solar_chart, analysis_id)

        return {
            "message": f"Анализ #{analysis_id} е обновен успешно",
            "analysis_id": analysis_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при обновяване на анализ: {str(e)}"
        )


@router.get("/local/analyses/{analysis_id}/solar-return-chart")
async def get_solar_return_chart(
    analysis_id: int,
    regenerate: bool = Query(default=False, description="Force regeneration even if cached"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Solar Return chart for an analysis.

    Returns the cached chart from the database if available (unless regenerate=true).
    If no cached chart exists, generates one via the Astrology API and saves it.
    Only available for solar_return product type.
    """
    from services.astrology_api import astrology_api

    # Get analysis
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")

    # Verify this is a solar return analysis
    if analysis.product_type != "solar_return":
        raise HTTPException(
            status_code=400,
            detail="Този анализ не е соларна карта"
        )

    # Check required fields
    if not all([
        analysis.person1_birth_date,
        analysis.person1_latitude is not None,
        analysis.person1_longitude is not None,
        analysis.solar_return_year
    ]):
        raise HTTPException(
            status_code=400,
            detail="Липсват необходими данни за раждане или година на соларната карта"
        )

    # Check birthday location data
    if not all([
        analysis.person1_birthday_location,
        analysis.person1_birthday_latitude is not None,
        analysis.person1_birthday_longitude is not None
    ]):
        raise HTTPException(
            status_code=400,
            detail="Липсват данни за мястото на празнуване на рождения ден"
        )

    # --- Return cached chart if available and regeneration not requested ---
    existing = db.query(SolarReturnChart).filter(
        SolarReturnChart.analysis_id == analysis_id
    ).first()

    if existing and not regenerate:
        return {
            "success": True,
            "analysis_id": analysis_id,
            "person_name": analysis.person1_name,
            "return_year": analysis.solar_return_year,
            "chart_data": json.loads(existing.chart_data),
            "cached": True,
            "generated_at": existing.generated_at.isoformat() if existing.generated_at else None,
        }

    try:
        # Create birthday datetime for the return year
        birthday_date = analysis.person1_birth_date.replace(year=analysis.solar_return_year)

        # Call Astrology API
        chart_data = await astrology_api.get_solar_return_chart(
            name=analysis.person1_name,
            birth_date=analysis.person1_birth_date,
            birth_latitude=analysis.person1_latitude,
            birth_longitude=analysis.person1_longitude,
            return_year=analysis.solar_return_year,
            birthday_date=birthday_date,
            birthday_latitude=analysis.person1_birthday_latitude,
            birthday_longitude=analysis.person1_birthday_longitude
        )

        # --- Persist to database ---
        chart_json = json.dumps(chart_data)
        if existing:
            existing.chart_data = chart_json
            existing.updated_at = datetime.utcnow()
        else:
            existing = SolarReturnChart(
                analysis_id=analysis_id,
                chart_data=chart_json
            )
            db.add(existing)
        db.commit()
        db.refresh(existing)

        return {
            "success": True,
            "analysis_id": analysis_id,
            "person_name": analysis.person1_name,
            "return_year": analysis.solar_return_year,
            "chart_data": chart_data,
            "cached": False,
            "generated_at": existing.generated_at.isoformat() if existing.generated_at else None,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при генериране на соларна карта: {str(e)}"
        )


@router.put("/local/analyses/{analysis_id}/solar-return-chart")
async def update_solar_return_chart(
    analysis_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually overwrite the cached solar return chart data.
    Accepts the full chart_data JSON and persists it to the database.
    Subsequent ChatGPT requests will use this updated chart.
    """
    body = await request.json()
    chart_data = body.get("chart_data")
    if chart_data is None:
        raise HTTPException(status_code=422, detail="Полето 'chart_data' е задължително")

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")

    if analysis.product_type != "solar_return":
        raise HTTPException(status_code=400, detail="Този анализ не е соларна карта")

    try:
        chart_json = json.dumps(chart_data)
        existing = db.query(SolarReturnChart).filter(
            SolarReturnChart.analysis_id == analysis_id
        ).first()
        if existing:
            existing.chart_data = chart_json
            existing.updated_at = datetime.utcnow()
        else:
            existing = SolarReturnChart(
                analysis_id=analysis_id,
                chart_data=chart_json
            )
            db.add(existing)
        db.commit()
        db.refresh(existing)

        ts = existing.updated_at or existing.generated_at
        return {
            "success": True,
            "analysis_id": analysis_id,
            "person_name": analysis.person1_name,
            "return_year": analysis.solar_return_year,
            "chart_data": chart_data,
            "cached": True,
            "generated_at": ts.isoformat() if ts else None,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при запазване на соларна карта: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Solar Return Report helpers (ChatGPT / OpenAI)
# ---------------------------------------------------------------------------

_SIGN_BG = {
    "Ari": "Овен", "Tau": "Телец", "Gem": "Близнаци",
    "Can": "Рак", "Leo": "Лъв", "Vir": "Дева",
    "Lib": "Везни", "Sco": "Скорпион", "Sag": "Стрелец",
    "Cap": "Козирог", "Aqu": "Водолей", "Pis": "Риби",
}
_HOUSE_BG = {
    "First_House": "1-ва", "Second_House": "2-ра", "Third_House": "3-та",
    "Fourth_House": "4-та", "Fifth_House": "5-та", "Sixth_House": "6-та",
    "Seventh_House": "7-ма", "Eighth_House": "8-ма", "Ninth_House": "9-та",
    "Tenth_House": "10-та", "Eleventh_House": "11-та", "Twelfth_House": "12-та",
}
_PLANET_BG = {
    "Sun": "Слънце", "Moon": "Луна", "Mercury": "Меркурий",
    "Venus": "Венера", "Mars": "Марс", "Jupiter": "Юпитер",
    "Saturn": "Сатурн", "Uranus": "Уран", "Neptune": "Нептун",
    "Pluto": "Плутон", "Ascendant": "Асцендент", "Medium_Coeli": "МС (Среднонебие)",
    "Imum_Coeli": "IC", "Descendant": "Десцендент",
    "Chiron": "Хирон", "Mean_Lilith": "Лилит",
    "Mean_Node": "Северен Възел", "True_Node": "Истински Възел",
    "Mean_South_Node": "Южен Възел",
}
_VALID_SECTIONS = {"yearly_summary", "planetary_positions", "life_structure", "main_theme", "yearly_details"}

# Canonical generation order — earlier sections feed into later ones
_SECTION_ORDER = ["yearly_summary", "planetary_positions", "main_theme", "life_structure", "yearly_details"]

_SECTION_LABELS = {
    "yearly_summary":      "Годината на кратко",
    "planetary_positions": "Планетарни позиции и акценти",
    "life_structure":      "Как да структурираш живота си",
    "main_theme":          "Главната тема на годината",
    "yearly_details":      "Годината в детайли",
}


def _chart_summary(chart_json: str, detailed: bool = False) -> str:
    """Build a readable Bulgarian planet-position string for OpenAI prompts."""
    try:
        sd = json.loads(chart_json).get("subject_data", {})
    except Exception:
        return "Данните за картата не са достъпни."

    priority = ["ascendant", "sun", "moon", "mercury", "venus", "mars",
                "jupiter", "saturn", "medium_coeli", "chiron"]
    extra    = ["uranus", "neptune", "pluto", "mean_lilith", "mean_node", "mean_south_node"]
    keys = priority + (extra if detailed else [])

    lines = []
    for key in keys:
        obj = sd.get(key)
        if not obj:
            continue
        name  = _PLANET_BG.get(obj.get("name", ""), obj.get("name", ""))
        sign  = _SIGN_BG.get(obj.get("sign", ""), obj.get("sign", ""))
        house = _HOUSE_BG.get(obj.get("house", ""), obj.get("house", "").replace("_House", ""))
        pos   = obj.get("position", 0)
        retro = " (ретроградна)" if obj.get("retrograde") else ""
        lines.append(f"  • {name}: {sign} {pos:.1f}°, {house} астрологична къща{retro}")
    return "\n".join(lines) or "Позициите не са достъпни."


def _build_section_prompt(section: str, analysis, chart_json: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the given section."""
    raw_gender = analysis.person1_gender
    gender = raw_gender.value if raw_gender else "other"
    name   = analysis.person1_name
    year   = analysis.solar_return_year
    bd     = analysis.person1_birth_date.strftime("%d.%m.%Y %H:%M") if analysis.person1_birth_date else "?"
    place  = analysis.person1_birth_place or "?"
    bloc   = analysis.person1_birthday_location or "неизвестно"

    if gender == "male":
        gender_label  = "мъж (мъжки род)"
        gender_rule   = (
            "ПОЛ НА КЛИЕНТА: МЪЖ. "
            "ЗАДЪЛЖИТЕЛНО: Използвай САМО И ЕДИНСТВЕНО мъжки род за ВСИЧКИ думи, свързани с клиента. "
            "ПРАВИЛНО (мъжки): роден, дисциплиниран, готов, вдъхновен, насочен, щастлив, призован, фокусиран, уморен, зает. "
            "ГРЕШНО (НИКОГА не пиши): родена, дисциплинирана, готова, вдъхновена, насочена, щастлива, призована. "
            "ЗАБРАНЕНО: НЕ пиши никога двете форми с наклонена черта като 'дисциплиниран/дисциплинирана' или 'роден/родена' — "
            "само мъжката форма без наклонена черта."
        )
    elif gender == "female":
        gender_label  = "жена (женски род)"
        gender_rule   = (
            "ПОЛ НА КЛИЕНТА: ЖЕНА. "
            "ЗАДЪЛЖИТЕЛНО: Използвай САМО И ЕДИНСТВЕНО женски род за ВСИЧКИ думи, свързани с клиентката. "
            "ПРАВИЛНО (женски): родена, дисциплинирана, готова, вдъхновена, насочена, щастлива, призована, фокусирана, уморена, заета. "
            "ГРЕШНО (НИКОГА не пиши): роден, дисциплиниран, готов, вдъхновен, насочен, щастлив, призован. "
            "ЗАБРАНЕНО: НЕ пиши никога двете форми с наклонена черта като 'дисциплиниран/дисциплинирана' или 'роден/родена' — "
            "само женската форма без наклонена черта."
        )
    else:
        gender_label  = "човек"
        gender_rule   = (
            "Полът на клиента не е уточнен. Използвай неутрални изрази когато е възможно."
        )

    system = (
        f"{gender_rule} "
        "Ти си опитен и вдъхновяващ астролог с дълбоко разбиране за човешката психология, специализиран в солар карти (Solar Return). "
        "Пишеш персонализирани астрологични доклади изключително на БЪЛГАРСКИ ЕЗИК. "
        "Тонът ти е топъл, личен, вдъхновяващ и дълбоко човечен — пишеш така, сякаш седиш срещу клиента и му разказваш за годината му с грижа и мъдрост. "
        "СТИЛ НА ПИСАНЕ: Пиши като опитен астролог-психолог, не като учебник. "
        "Използвай метафори, образен език и психологическа дълбочина. "
        "НЕ претоварвай текста с астрологична терминология — когато споменаваш планета или аспект, "
        "веднага обясни какво означава това за живота, емоциите и решенията на клиента на разбираем, човешки език. "
        "Вместо да изреждаш позиции една след друга, вплитай ги естествено в разказа за живота на човека. "
        "Фокусирай се върху ПРАКТИЧЕСКОТО ЗНАЧЕНИЕ: как клиентът ще се чувства, какви вътрешни процеси ще преживява, "
        "какви възможности се отварят и какви предизвикателства може да срещне. "
        "Целта е клиентът да се почувства разбран, вдъхновен и с по-ясна представа за годината си. "
        "ПРАВИЛО ЗА СОЛАРНА ГОДИНА: Соларната година винаги обхваща ДВЕ календарни години. "
        "Ако соларната година е напр. 2025, в текста ВИНАГИ я изписвай като '2025-2026'. "
        "Ако е 2026, пиши '2026-2027'. Формулата е: [година]-[година+1]. НИКОГА не пиши само една година. "
        "Обръщаш се към клиента ДИРЕКТНО с второ лице единствено число (ти, теб, твоят, твоята, твоето). "
        "НИКОГА не използвай трето лице (той/тя/му/й) за клиента. "
        "НИКОГА не пиши двете родови форми с наклонена черта (пример за ГРЕШНО: 'дисциплиниран/дисциплинирана', 'роден/родена') — "
        "пиши САМО формата, съответстваща на пола на клиента. "
        "Астрологичните ДОМОВЕ винаги се назовават като 'астрологичен дом' (напр. 'първи астрологичен дом', 'десети астрологичен дом') — НИКОГА като 'къща' или 'къщи'. "
        "Пишеш в свързан прозаичен текст — без номерация, без вградени заглавия. "
        "Не превеждаш астрологичните термини буквално — давай смислени обяснения."
    )

    person_block = (
        f"Лице: {name} ({gender_label})\n"
        f"Дата и час на раждане: {bd}\n"
        f"Място на раждане: {place}\n"
        f"Соларна година: {year} г., отпразнувана в: {bloc}"
    )

    # Full raw chart JSON for GPT to interpret directly
    raw_chart = chart_json

    if section == "yearly_summary":
        year_range = f"{year}-{year + 1}"
        user = f"""{gender_rule}

Напиши раздел „Годината на кратко" за соларната карта на следното лице:

{person_block}

Пълни данни от соларната карта (JSON):
{raw_chart}

Напиши цялостен преглед (около 700 думи) на соларната година {year_range} за {name}.
НЕ СПОМЕНАВАЙ конкретни планети, астрологични домове, знаци или аспекти по име. Този раздел трябва да звучи като мъдро писмо от личен съветник, НЕ като астрологичен анализ.
Винаги използвай "{year_range}" когато споменаваш годината — НИКОГА само "{year}".

Разделът ТРЯБВА да съдържа следните теми, вплетени естествено в разказа:

1. ОБЩ ДУХ НА ГОДИНАТА — какво е настроението и посланието на {year_range}, какъв вътрешен процес предстои.

2. ОСНОВНИ ОБЛАСТИ НА УСПЕХ — къде {name} ще има най-силен потенциал за постижения и напредък тази година.

3. ОСНОВНИ ПРЕДИЗВИКАТЕЛСТВА — какви трудности или изпитания може да срещне и как да се справи с тях.

4. КАРМИЧНИ УРОЦИ — какви дълбоки житейски уроци носи тази година, какво трябва да осъзнае или да пусне.

5. КРАТЪК ПРЕГЛЕД НА КЛЮЧОВИ СФЕРИ:
   - Работа и бизнес — накратко какво предстои професионално
   - Финанси — накратко за материалното състояние
   - Любов и взаимоотношения — накратко за личния живот
   - Здраве — накратко за физическото и емоционалното здраве

Пиши образно, с метафори и психологическа дълбочина — сякаш разказваш история за годината, която предстои.
НЕ използвай номерация, подзаглавия или списъци — всичко трябва да е свързан, плавен текст.
Обръщай се директно към {name} с ти/теб. Отговори само на БЪЛГАРСКИ."""

    elif section == "planetary_positions":
        user = f"""{gender_rule}

Напиши раздел \u201eПланетарни позиции и акценти\u201c за соларната карта на:

{person_block}

Пълни данни от соларната карта (JSON):
{raw_chart}

Избери 5-6 от НАЙ-ЗНАЧИМИТЕ планетарни позиции за {year} г. и обясни ПРАКТИЧЕСКИ какво означава всяка за живота на {name}.
НЕ изброявай позиции като списък — вплети всяка в жив, образен разказ за това как ще се прояви в ежедневието.
Дай нова, различна информация от раздела \u201eГодината на кратко\u201c — не повтаряй вече казаното.
Обръщай се директно с ти/теб. Около 500 думи. Отговори само на БЪЛГАРСКИ."""

    elif section == "main_theme":
        user = f"""{gender_rule}

Напиши раздел \u201eГлавната тема на годината\u201c за соларната карта на:

{person_block}

Пълни данни от соларната карта (JSON):
{raw_chart}

Напиши този раздел като история — плавен, топъл разказ без никаква астрологична терминология. ЗАБРАНЕНО е да се споменават планети, домове, знаци, аспекти или каквито и да е астрологични понятия. Пиши така, сякаш разказваш на {name} на разбираем, човешки език какво носи тази конкретна година.
Целта на раздела е да покаже ФОКУСА НА ГОДИНАТА — какво я прави различна от всички останали години в живота на {name}, върху какво животът ще насочи вниманието и енергията му/й, и за какво го/я подготвя тази година. Какъв е главният урок или посока, към която всичко клони?
Не давай съвети и не изреждай препоръки — разказвай. Помогни на {name} да усети смисъла и посланието на годината като цяло.
Обръщай се директно с ти/теб. Около 500 думи. Отговори само на БЪЛГАРСКИ."""

    elif section == "life_structure":
        user = f"""{gender_rule}

Напиши раздел \u201eКак да структурираш живота си\u201c за соларната карта на:

{person_block}

Пълни данни от соларната карта (JSON):
{raw_chart}

Въз основа на соларната карта на {name}, напиши ясен и добре структуриран списък с практически съвети как да използва тази година по най-добрия начин.

Това е ЧИСТО ПРАКТИЧЕСКИ раздел. Фокусът е върху действията: какво е най-важно да направи {name} тази година, за да успее и да се развие. Съветите трябва да произтичат директно от картата — не давай общи клишета, а конкретни насоки, специфични за тази соларна година.

Форматирай раздела като номериран списък от 6 до 8 съвета. Всеки съвет трябва да има:
- Кратко, ясно заглавие (1 изречение)
- Обяснение от 2-4 изречения защо точно това е важно тази година и как да го приложи на практика

Минимум астрологичен жаргон — ако споменаваш планета или дом, веднага обяснявай какво означава за живота му/й.
Не повтаряй анализи от предишните раздели — тук говорим само за ДЕЙСТВИЯ и ПРИОРИТЕТИ.
Обръщай се директно с ти/теб. Отговори само на БЪЛГАРСКИ."""

    elif section == "yearly_details":
        user = f"""{gender_rule}

Напиши раздел \u201eГодината в детайли\u201c за соларната карта на:

{person_block}

Пълни данни от соларната карта (JSON):
{raw_chart}

Направи подробен анализ на следните жизнени сфери за {name} тази година:
кариера и призвание, любов и взаимоотношения, финанси и материално, здраве и тяло, семейство и дом, лично развитие и духовност.
За всяка сфера дай НОВА информация, която не е казана в предишните раздели.
НЕ повтаряй вече споменати планети и домове в същия контекст — ако ги засягаш, дай различен ъгъл.
Фокусирай се на конкретиката: какво да очаква, какви решения предстоят, какви емоции ще преживее.
Обръщай се директно с ти/теб. Около 1000 думи. Отговори само на БЪЛГАРСКИ."""

    else:
        raise ValueError(f"Unknown section: {section}")

    return system, user


async def _call_openai(messages: list[dict], max_tokens: int = 2000) -> str:
    """Call the OpenAI ChatGPT API with a full conversation and return the text response."""
    from openai import AsyncOpenAI
    import os, datetime as _dt

    # Write the prompt to a shared log file so it can be watched externally
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt_log.txt")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"OPENAI REQUEST  [{_dt.datetime.now().strftime('%H:%M:%S')}]\n")
            f.write("=" * 80 + "\n")
            for i, msg in enumerate(messages):
                role = msg["role"].upper()
                content = msg["content"]
                f.write(f"\n--- [{i+1}] {role} ---\n")
                if msg["role"] == "assistant" and len(content) > 500:
                    f.write(content[:500] + f"\n... [{len(content)} chars total]\n")
                else:
                    f.write(content + "\n")
            f.write("\n" + "=" * 80 + "\n")
    except Exception:
        pass

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.75,
    )
    return response.choices[0].message.content


def _build_conversation_history(
    section: str,
    analysis,
    chart_json: str,
    report: "SolarReturnReport | None",
) -> list[dict]:
    """Build a multi-turn conversation including previously generated sections.

    This keeps GPT aware of what it already wrote so each new section
    adds genuinely new information instead of repeating itself.
    """
    import re, html as _html

    system_prompt, user_prompt = _build_section_prompt(section, analysis, chart_json)
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Inject previously-generated sections as conversation turns
    prior_sections = []
    for s in _SECTION_ORDER:
        if s == section:
            break
        content = getattr(report, s, None) if report else None
        if content:
            prior_sections.append(s)
            plain = _html.unescape(re.sub(r'<[^>]+>', ' ', content)).strip()
            messages.append({"role": "user",      "content": f"Напиши раздел \"{_SECTION_LABELS[s]}\"."})
            messages.append({"role": "assistant", "content": plain})

    # Add a no-repeat instruction if there are prior sections
    if prior_sections:
        prior_names = ", ".join(f'"{_SECTION_LABELS[s]}"' for s in prior_sections)
        no_repeat = (
            f"\n\nВАЖНО: Вече написа следните раздели: {prior_names}. "
            "Този нов раздел е ДОПЪЛНЕНИЕ към тях — трябва да дава НОВА, РАЗЛИЧНА информация. "
            "ЗАБРАНЕНО е да повтаряш:"
            "\n- Същите планети и домове в същия контекст"
            "\n- Същите изводи или съвети, казани по-рано"
            "\n- Общи фрази, които вече са използвани"
            "\nАко се налага да споменеш планета от по-ранен раздел, дай НАПЪЛНО РАЗЛИЧЕН ъгъл — "
            "нов аспект от живота, нова емоция, нова практическа ситуация."
        )
        user_prompt += no_repeat

    messages.append({"role": "user", "content": user_prompt})
    return messages


# ---------------------------------------------------------------------------
# Solar Return Report endpoints
# ---------------------------------------------------------------------------

@router.get("/local/analyses/{analysis_id}/solar-report", response_model=SolarReportResponse)
async def get_solar_report(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the existing saved solar return report for an analysis, or 404."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")

    report = db.query(SolarReturnReport).filter(
        SolarReturnReport.analysis_id == analysis_id
    ).first()

    if not report:
        # Return an empty stub so the frontend can pre-populate blank editors
        return SolarReportResponse(
            id=0,
            analysis_id=analysis_id,
        )

    return report


@router.post("/local/analyses/{analysis_id}/solar-report/generate/{section}")
async def generate_report_section(
    analysis_id: int,
    section: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Call ChatGPT to generate a single report section.  Returns the text — does not save."""
    if section not in _VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Невалидна секция: {section}")

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")
    if analysis.product_type != "solar_return":
        raise HTTPException(status_code=400, detail="Анализът не е соларна карта")
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API ключът не е конфигуриран")

    # Require chart data for context
    chart = db.query(SolarReturnChart).filter(
        SolarReturnChart.analysis_id == analysis_id
    ).first()
    chart_json = chart.chart_data if chart else "{}"

    # Load existing report so we can build conversation history
    report = db.query(SolarReturnReport).filter(
        SolarReturnReport.analysis_id == analysis_id
    ).first()

    try:
        messages = _build_conversation_history(section, analysis, chart_json, report)
        max_tok = 3000 if section == "yearly_details" else 2000
        text = await _call_openai(messages, max_tokens=max_tok)
        return {"section": section, "content": text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Грешка при генериране на секция '{section}': {str(e)}"
        )


@router.post("/local/analyses/{analysis_id}/solar-report/refine/{section}")
async def refine_report_section(
    analysis_id: int,
    section: str,
    body: SolarReportRefine,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Refine an existing section using a custom user instruction + the solar chart context."""
    import re, html as _html
    if section not in _VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Невалидна секция: {section}")
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API ключът не е конфигуриран")

    chart = db.query(SolarReturnChart).filter(
        SolarReturnChart.analysis_id == analysis_id
    ).first()
    chart_json = chart.chart_data if chart else "{}"

    # Strip HTML tags and decode entities for the GPT context
    existing_text = _html.unescape(re.sub(r'<[^>]+>', ' ', body.existing_content)).strip()

    # Reuse system prompt (persona + language + gender rules)
    system_prompt, _ = _build_section_prompt(section, analysis, chart_json)
    label = _SECTION_LABELS.get(section, section)
    name = analysis.person1_name

    user_prompt = f"""Имаш следния текст от соларния доклад, раздел {label}:\n\n{existing_text}\n\nПълни данни от соларната карта на {name} (JSON):\n{chart_json}\n\nИнструкция: {body.user_instruction}\n\nПриложи инструкцията и върни САМО подобрения текст. Не добавяй заглавие. Запази тона, стила и обръщането с ти/теб. Отговори само на БЪЛГАРСКИ."""

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        text = await _call_openai(messages)
        return {"section": section, "content": text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"\u0413\u0440\u0435\u0448\u043a\u0430 \u043f\u0440\u0438 \u0440\u0435\u0434\u0430\u043a\u0446\u0438\u044f \u043d\u0430 \u0441\u0435\u043a\u0446\u0438\u044f '{section}': {str(e)}"
        )


@router.put("/local/analyses/{analysis_id}/solar-report")
async def save_report_section(
    analysis_id: int,
    body: SolarReportSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save (upsert) a single section of the solar return report."""
    if body.section not in _VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Невалидна секция: {body.section}")

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")

    report = db.query(SolarReturnReport).filter(
        SolarReturnReport.analysis_id == analysis_id
    ).first()
    if not report:
        report = SolarReturnReport(analysis_id=analysis_id)
        db.add(report)

    setattr(report, body.section, body.content)
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)

    return {"message": f"Секция '{body.section}' е запазена успешно", "analysis_id": analysis_id}


async def _regenerate_solar_chart(analysis_id: int):
    """
    Background task: recalculate and overwrite the cached solar return chart
    for a single analysis after it has been edited.
    """
    from db.database import SessionLocal
    from services.astrology_api import astrology_api

    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return

        if not all([
            analysis.person1_birth_date,
            analysis.person1_latitude is not None,
            analysis.person1_longitude is not None,
            analysis.solar_return_year,
            analysis.person1_birthday_location,
            analysis.person1_birthday_latitude is not None,
            analysis.person1_birthday_longitude is not None,
        ]):
            print(f"⚠️  Regen-chart: skipping analysis {analysis_id} — missing required fields")
            return

        birthday_date = analysis.person1_birth_date.replace(year=analysis.solar_return_year)
        chart_data = await astrology_api.get_solar_return_chart(
            name=analysis.person1_name,
            birth_date=analysis.person1_birth_date,
            birth_latitude=analysis.person1_latitude,
            birth_longitude=analysis.person1_longitude,
            return_year=analysis.solar_return_year,
            birthday_date=birthday_date,
            birthday_latitude=analysis.person1_birthday_latitude,
            birthday_longitude=analysis.person1_birthday_longitude,
        )

        existing = db.query(SolarReturnChart).filter(
            SolarReturnChart.analysis_id == analysis_id
        ).first()

        if existing:
            existing.chart_data = json.dumps(chart_data)
            existing.updated_at = datetime.utcnow()
        else:
            existing = SolarReturnChart(
                analysis_id=analysis_id,
                chart_data=json.dumps(chart_data),
            )
            db.add(existing)

        db.commit()
        print(f"✅ Regen-chart: updated for analysis {analysis_id} ({analysis.person1_name})")
    except Exception as e:
        db.rollback()
        print(f"❌ Regen-chart: failed for analysis {analysis_id}: {e}")
    finally:
        db.close()


async def _auto_generate_solar_charts(order_id: int):
    """
    Background task: automatically generate and cache solar return charts
    for every solar-return analysis in the given order that doesn't have one yet.
    """
    from db.database import SessionLocal
    from services.astrology_api import astrology_api

    db = SessionLocal()
    try:
        analyses = (
            db.query(Analysis)
            .filter(
                Analysis.order_id == order_id,
                Analysis.product_type == "solar_return",
            )
            .all()
        )

        for analysis in analyses:
            # Skip if already cached
            existing = db.query(SolarReturnChart).filter(
                SolarReturnChart.analysis_id == analysis.id
            ).first()
            if existing:
                continue

            # Skip if required fields are missing
            if not all([
                analysis.person1_birth_date,
                analysis.person1_latitude is not None,
                analysis.person1_longitude is not None,
                analysis.solar_return_year,
                analysis.person1_birthday_location,
                analysis.person1_birthday_latitude is not None,
                analysis.person1_birthday_longitude is not None,
            ]):
                print(f"⚠️  Auto-chart: skipping analysis {analysis.id} — missing required fields")
                continue

            try:
                birthday_date = analysis.person1_birth_date.replace(year=analysis.solar_return_year)
                chart_data = await astrology_api.get_solar_return_chart(
                    name=analysis.person1_name,
                    birth_date=analysis.person1_birth_date,
                    birth_latitude=analysis.person1_latitude,
                    birth_longitude=analysis.person1_longitude,
                    return_year=analysis.solar_return_year,
                    birthday_date=birthday_date,
                    birthday_latitude=analysis.person1_birthday_latitude,
                    birthday_longitude=analysis.person1_birthday_longitude,
                )
                chart = SolarReturnChart(
                    analysis_id=analysis.id,
                    chart_data=json.dumps(chart_data),
                )
                db.add(chart)
                db.commit()
                print(f"✅ Auto-chart: generated for analysis {analysis.id} ({analysis.person1_name})")
            except Exception as e:
                db.rollback()
                print(f"❌ Auto-chart: failed for analysis {analysis.id}: {e}")
    finally:
        db.close()


@router.post("/webhooks/orders/create")
async def shopify_order_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_topic: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Webhook endpoint for Shopify order creation
    
    This endpoint receives order data from Shopify when a new order is created.
    No authentication required - Shopify webhooks are verified via HMAC signature.
    """
    
    print("\n" + "="*80)
    print("🚀 WEBHOOK ENDPOINT HIT!")
    print("="*80)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print(f"📍 Path: {request.url.path}")
    print(f"🌐 Method: {request.method}")
    print(f"📨 Headers:")
    print(f"   - X-Shopify-Topic: {x_shopify_topic}")
    print(f"   - X-Shopify-Shop-Domain: {x_shopify_shop_domain}")
    print(f"   - X-Shopify-Hmac-SHA256: {x_shopify_hmac_sha256[:20] + '...' if x_shopify_hmac_sha256 else 'None'}")
    print(f"   - Content-Type: {request.headers.get('content-type')}")
    print(f"   - User-Agent: {request.headers.get('user-agent')}")
    print("="*80)
    
    # Get raw body for HMAC verification
    body = await request.body()
    print(f"📦 Body size: {len(body)} bytes")
    print("="*80 + "\n")
    
    # Verify HMAC signature if webhook secret is configured
    if hasattr(settings, 'SHOPIFY_WEBHOOK_SECRET') and settings.SHOPIFY_WEBHOOK_SECRET:
        if not x_shopify_hmac_sha256:
            raise HTTPException(status_code=401, detail="Missing HMAC signature")
        
        computed_hmac = base64.b64encode(
            hmac.new(
                settings.SHOPIFY_WEBHOOK_SECRET.encode(),
                body,
                hashlib.sha256
            ).digest()
        ).decode()
        
        if not hmac.compare_digest(computed_hmac, x_shopify_hmac_sha256):
            raise HTTPException(status_code=401, detail="Invalid HMAC signature")
    
    try:
        # Parse order data from webhook
        order_data = json.loads(body)
        
        print(f"📦 Received Shopify webhook")
        print(f"   Topic: {x_shopify_topic}")
        print(f"   Shop: {x_shopify_shop_domain}")
        print(f"   Order ID: {order_data.get('id')}")
        print(f"   Order Number: {order_data.get('order_number')}")
        
        # ⚠️ IMPORTANT: Webhook payloads don't include line item properties!
        # We need to fetch the full order from Shopify API to get customer data
        shopify_order_id = order_data.get('id')
        
        if shopify_order_id:
            print(f"\n🔄 Fetching full order details from Shopify API...")
            try:
                # Fetch complete order data with line item properties
                full_order_data = await shopify_client.get_order(shopify_order_id)
                print(f"✅ Retrieved full order data with {len(full_order_data.get('line_items', []))} line items")
                
                # Use the full order data instead of webhook payload
                order_data = full_order_data
            except Exception as api_error:
                print(f"⚠️  Warning: Could not fetch full order from API: {api_error}")
                print(f"   Proceeding with webhook data (may not have line item properties)")
        
        # Process and save the order using the sync service
        synced_order = await shopify_sync_service.sync_order(order_data, db)

        # Auto-generate solar return charts in the background
        background_tasks.add_task(_auto_generate_solar_charts, synced_order.id)

        return {
            "status": "success",
            "message": "Order received and processed",
            "order_id": synced_order.id,
            "order_number": synced_order.order_number
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        print(f"❌ Error processing webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return 200 to prevent Shopify from retrying
        # Log the error for investigation
        return {
            "status": "error",
            "message": f"Error processing order: {str(e)}"
        }


# ===========================================================================
# PDF generation endpoints
# ===========================================================================

@router.post("/local/analyses/{analysis_id}/pdf")
async def request_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enqueue a background PDF generation job for the given analysis."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализът не е намерен")

    job = PdfJob(analysis_id=analysis_id, status=PdfJobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        from services.pdf_tasks import generate_pdf_task
        task = generate_pdf_task.apply_async(args=[job.id], queue="pdf")
        job.celery_task_id = task.id
        db.commit()
    except Exception as e:
        job.status = PdfJobStatus.FAILED
        job.error_message = f"Грешка при изпращане към опашката: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=job.error_message)

    return {
        "job_id": job.id,
        "status": job.status,
        "analysis_id": analysis_id,
        "person_name": analysis.person1_name,
    }


@router.get("/local/pdf-jobs/{job_id}")
async def get_pdf_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll the status of a PDF generation job."""
    job = db.query(PdfJob).filter(PdfJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Заявката не е намерена")

    analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
    return {
        "job_id": job.id,
        "status": job.status,
        "analysis_id": job.analysis_id,
        "person_name": analysis.person1_name if analysis else None,
        "solar_return_year": analysis.solar_return_year if analysis else None,
        "error_message": job.error_message,
        "drive_link": job.drive_link,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/local/pdf-jobs/{job_id}/download")
async def download_pdf(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the generated PDF file."""
    job = db.query(PdfJob).filter(PdfJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Заявката не е намерена")
    if job.status != PdfJobStatus.DONE:
        raise HTTPException(status_code=409, detail=f"PDF не е готов (статус: {job.status})")
    if not job.file_path or not os.path.exists(job.file_path):
        raise HTTPException(status_code=404, detail="PDF файлът не е намерен на диска")

    analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
    safe_name = re.sub(r"[^\w\-]", "_", analysis.person1_name or "report") if analysis else "report"
    order = db.query(ShopifyOrder).filter(ShopifyOrder.id == analysis.order_id).first() if analysis else None
    order_num = re.sub(r"[^\w\-]", "_", str(order.order_number)) if order else str(job.id)
    filename = f"Astronova_{safe_name}_{order_num}.pdf"

    return FileResponse(
        path=job.file_path,
        media_type="application/pdf",
        filename=filename,
    )

