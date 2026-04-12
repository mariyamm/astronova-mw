"""
Shopify sync service

This service syncs orders from Shopify and creates analyses in the database
"""

import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from models.shopify_order import ShopifyOrder, Analysis, ProductType
from services.shopify_client import shopify_client
from services.shopify_parser import shopify_parser


class ShopifySyncService:
    """Service for syncing Shopify orders to database"""
    
    @staticmethod
    async def sync_order(order_data: Dict[str, Any], db: Session) -> ShopifyOrder:
        """
        Sync a single order from Shopify to database
        
        Args:
            order_data: Raw order data from Shopify API
            db: Database session
            
        Returns:
            Created or updated ShopifyOrder
        """
        shopify_order_id = str(order_data.get("id"))
        
        # Check if order already exists
        existing_order = db.query(ShopifyOrder).filter(
            ShopifyOrder.shopify_order_id == shopify_order_id
        ).first()
        
        if existing_order:
            # Update existing order
            order = existing_order
            order.updated_at = datetime.now()
        else:
            # Create new order
            order = ShopifyOrder(shopify_order_id=shopify_order_id)
            db.add(order)
        
        # Update order fields
        order.order_number = str(order_data.get("order_number", ""))
        order.total_price = str(order_data.get("total_price", "0"))
        order.currency = order_data.get("currency", "BGN")
        order.financial_status = order_data.get("financial_status", "")
        order.fulfillment_status = order_data.get("fulfillment_status")
        
        # Customer data
        customer = order_data.get("customer", {})
        if customer:
            order.customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            order.customer_email = customer.get("email")
            order.customer_phone = customer.get("phone")
        
        # Parse order date
        order_created_at = order_data.get("created_at")
        if order_created_at:
            order.order_created_at = datetime.fromisoformat(order_created_at.replace('Z', '+00:00'))
        
        # Store raw JSON
        order.raw_data = json.dumps(order_data)
        
        db.flush()  # Get order ID
        
        # Process line items and create analyses
        line_items = order_data.get("line_items", [])
        await ShopifySyncService._process_line_items(order, line_items, db)
        
        db.commit()
        db.refresh(order)
        
        return order
    
    @staticmethod
    async def _process_line_items(order: ShopifyOrder, line_items: List[Dict], db: Session):
        """
        Process line items and create/update analyses
        
        Args:
            order: ShopifyOrder instance
            line_items: List of line item data from Shopify
            db: Database session
        """
        print(f"\n{'='*80}")
        print(f"🔍 PROCESSING LINE ITEMS FOR ORDER #{order.order_number}")
        print(f"   Total line items: {len(line_items)}")
        print(f"{'='*80}\n")
        
        existing_line_item_ids = {
            analysis.shopify_line_item_id 
            for analysis in order.analyses
        }
        
        for idx, item in enumerate(line_items, 1):
            line_item_id = str(item.get("id"))
            product_title = item.get("title", "")
            
            print(f"\n📦 LINE ITEM {idx}:")
            print(f"   ID: {line_item_id}")
            print(f"   Product: {product_title}")
            print(f"   SKU: {item.get('sku')}")
            print(f"   Variant: {item.get('variant_title')}")
            print(f"   Price: {item.get('price')}")
            
            # Delete existing analyses for this line item if they exist (allow reprocessing)
            # This handles both single analyses and multiple analyses from quantity > 1
            existing_analyses = db.query(Analysis).filter(
                Analysis.order_id == order.id
            ).filter(
                (Analysis.shopify_line_item_id == line_item_id) |
                (Analysis.shopify_line_item_id.like(f"{line_item_id}_%"))
            ).all()
            
            if existing_analyses:
                print(f"   🔄 REPROCESSING - Deleting {len(existing_analyses)} existing analysis/analyses")
                for existing in existing_analyses:
                    db.delete(existing)
                db.flush()  # Flush to avoid conflicts
            
            # Detect product type
            sku = item.get("sku")
            product_type = shopify_parser.detect_product_type(product_title, sku)
            print(f"   ✅ Detected product type: {product_type}")
            
            # Parse properties to extract person data
            properties = item.get("properties", [])
            quantity = item.get("quantity", 1)
            print(f"   📋 Properties found: {len(properties)}")
            print(f"   🔢 Quantity: {quantity}")
            
            if properties:
                print(f"   Property details:")
                for prop in properties:
                    print(f"      - {prop.get('name')}: {prop.get('value')}")
            else:
                print(f"   ⚠️  NO PROPERTIES in line item!")
            
            # ========================================================================
            # PRODUCT TYPE SPECIFIC LOGIC
            # ========================================================================
            
            if product_type == ProductType.LOVE_SYNASTRY:
                # SYNASTRY: Always 1 analysis with 2 partners (couple)
                # Ignore quantity - synastry is for a couple (2 people in 1 analysis)
                print(f"   💕 SYNASTRY: Creating 1 couple analysis (2 partners)")
                
                parsed_data = shopify_parser.parse_properties(properties)
                
                if not parsed_data.get("person1"):
                    print(f"   ❌ ERROR: Missing Partner 1 data!")
                    continue
                
                if not parsed_data.get("person2"):
                    print(f"   ❌ ERROR: Missing Partner 2 data! Synastry requires 2 people.")
                    continue
                
                print(f"   ✅ Partner 1: {parsed_data['person1'].get('name')}")
                print(f"   ✅ Partner 2: {parsed_data['person2'].get('name')}")
                
                # Enrich both partners with timezone
                person1_data = await shopify_parser.enrich_with_timezone(parsed_data["person1"])
                person2_data = await shopify_parser.enrich_with_timezone(parsed_data["person2"])
                
                # Create 1 synastry analysis with both partners
                analysis = Analysis(
                    order_id=order.id,
                    shopify_line_item_id=line_item_id,
                    product_type=product_type,
                    product_title=product_title,
                    variant_title=item.get("variant_title"),
                    sku=sku,
                    quantity=quantity,
                    price=str(item.get("price", "0")),
                    
                    # Partner 1
                    person1_name=person1_data["name"],
                    person1_gender=person1_data.get("gender"),
                    person1_birth_date=person1_data["birth_date"],
                    person1_birth_place=person1_data["birth_place"],
                    person1_latitude=person1_data["latitude"],
                    person1_longitude=person1_data["longitude"],
                    person1_timezone=person1_data.get("timezone"),
                    person1_timezone_offset=person1_data.get("timezone_offset"),
                    person1_birthday_location=person1_data.get("birthday_location"),
                    person1_birthday_latitude=person1_data.get("birthday_latitude"),
                    person1_birthday_longitude=person1_data.get("birthday_longitude"),
                    
                    # Partner 2
                    person2_name=person2_data["name"],
                    person2_gender=person2_data.get("gender"),
                    person2_birth_date=person2_data["birth_date"],
                    person2_birth_place=person2_data["birth_place"],
                    person2_latitude=person2_data["latitude"],
                    person2_longitude=person2_data["longitude"],
                    person2_timezone=person2_data.get("timezone"),
                    person2_timezone_offset=person2_data.get("timezone_offset")
                )
                
                print(f"   ✅ Synastry analysis created!")
                db.add(analysis)
                
            elif product_type == ProductType.DETAILED_ANALYSIS:
                # DETAILED ANALYSIS: Each person = 1 separate analysis
                # If quantity > 1, create multiple analyses (1 per person)
                print(f"   📊 DETAILED ANALYSIS: Creating {quantity} individual analysis/analyses")
                
                for person_index in range(1, quantity + 1):
                    print(f"\n   📝 Processing person {person_index} of {quantity}...")
                    
                    # Extract data for this specific person
                    person_data = shopify_parser.parse_person_by_number(properties, person_index)
                    
                    if not person_data:
                        print(f"      ❌ ERROR: Could not parse person {person_index} data!")
                        print(f"      ⚠️  Registering error for this line item")
                        # TODO: Store error in database
                        continue
                    
                    print(f"      ✅ Found: {person_data.get('name')}")
                    
                    # Enrich with timezone
                    person_data_enriched = await shopify_parser.enrich_with_timezone(person_data)
                    
                    # Create analysis for this person (person1 only, no person2)
                    analysis = Analysis(
                        order_id=order.id,
                        shopify_line_item_id=f"{line_item_id}_{person_index}" if quantity > 1 else line_item_id,
                        product_type=product_type,
                        product_title=product_title,
                        variant_title=item.get("variant_title"),
                        sku=sku,
                        quantity=1,  # Each analysis represents 1 person
                        price=str(item.get("price", "0")),
                        
                        # Person data (person1 only)
                        person1_name=person_data_enriched["name"],
                        person1_gender=person_data_enriched.get("gender"),
                        person1_birth_date=person_data_enriched["birth_date"],
                        person1_birth_place=person_data_enriched["birth_place"],
                        person1_latitude=person_data_enriched["latitude"],
                        person1_longitude=person_data_enriched["longitude"],
                        person1_timezone=person_data_enriched.get("timezone"),
                        person1_timezone_offset=person_data_enriched.get("timezone_offset"),
                        person1_birthday_location=person_data_enriched.get("birthday_location"),
                        person1_birthday_latitude=person_data_enriched.get("birthday_latitude"),
                        person1_birthday_longitude=person_data_enriched.get("birthday_longitude")
                        # person2 fields remain NULL
                    )
                    
                    print(f"      ✅ Analysis created for person {person_index}!")
                    db.add(analysis)
            
            elif product_type == ProductType.SOLAR_RETURN:
                # SOLAR RETURN: Each person = 1 separate analysis with birthday location
                # If quantity > 1, create multiple analyses (1 per person)
                print(f"   🌞 SOLAR RETURN: Creating {quantity} individual solar return analysis/analyses")
                
                for person_index in range(1, quantity + 1):
                    print(f"\n   📝 Processing person {person_index} of {quantity}...")
                    
                    # Extract data for this specific person
                    person_data = shopify_parser.parse_person_by_number(properties, person_index)
                    
                    if not person_data:
                        print(f"      ❌ ERROR: Could not parse person {person_index} data!")
                        print(f"      ⚠️  Registering error for this line item")
                        continue
                    
                    print(f"      ✅ Found: {person_data.get('name')}")
                    
                    # Check for birthday location data
                    if person_data.get("birthday_location"):
                        print(f"      🎂 Birthday Location: {person_data.get('birthday_location')}")
                        print(f"      📍 Birthday Coords: {person_data.get('birthday_latitude')}, {person_data.get('birthday_longitude')}")
                    
                    # Enrich with timezone
                    person_data_enriched = await shopify_parser.enrich_with_timezone(person_data)
                    
                    # Create analysis for this person (person1 only, no person2)
                    analysis = Analysis(
                        order_id=order.id,
                        shopify_line_item_id=f"{line_item_id}_{person_index}" if quantity > 1 else line_item_id,
                        product_type=product_type,
                        product_title=product_title,
                        variant_title=item.get("variant_title"),
                        sku=sku,
                        quantity=1,  # Each analysis represents 1 person
                        price=str(item.get("price", "0")),
                        
                        # Person data (person1 only)
                        person1_name=person_data_enriched["name"],
                        person1_gender=person_data_enriched.get("gender"),
                        person1_birth_date=person_data_enriched["birth_date"],
                        person1_birth_place=person_data_enriched["birth_place"],
                        person1_latitude=person_data_enriched["latitude"],
                        person1_longitude=person_data_enriched["longitude"],
                        person1_timezone=person_data_enriched.get("timezone"),
                        person1_timezone_offset=person_data_enriched.get("timezone_offset"),
                        
                        # Birthday location data (Solar Return specific)
                        person1_birthday_location=person_data_enriched.get("birthday_location"),
                        person1_birthday_latitude=person_data_enriched.get("birthday_latitude"),
                        person1_birthday_longitude=person_data_enriched.get("birthday_longitude"),
                        
                        # Solar Return year
                        solar_return_year=person_data_enriched.get("solar_return_year")
                        # person2 fields remain NULL
                    )
                    
                    print(f"      ✅ Solar Return analysis created for person {person_index}!")
                    db.add(analysis)
            
            continue  # Move to next line item
        
        print(f"\n{'='*80}")
        print(f"✅ FINISHED PROCESSING LINE ITEMS")
        print(f"{'='*80}\n")
    
    @staticmethod
    async def sync_orders_from_shopify(
        db: Session,
        status: str = "any",
        limit: int = 50
    ) -> List[ShopifyOrder]:
        """
        Fetch orders from Shopify and sync to database
        
        Args:
            db: Database session
            status: Order status filter
            limit: Number of orders to fetch
            
        Returns:
            List of synced ShopifyOrder objects
        """
        # Fetch orders from Shopify
        orders_data = await shopify_client.get_orders(status=status, limit=limit)
        
        synced_orders = []
        for order_data in orders_data:
            try:
                order = await ShopifySyncService.sync_order(order_data, db)
                synced_orders.append(order)
            except Exception as e:
                print(f"Error syncing order {order_data.get('id')}: {e}")
                db.rollback()
                continue
        
        return synced_orders


shopify_sync_service = ShopifySyncService()
