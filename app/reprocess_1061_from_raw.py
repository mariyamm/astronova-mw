"""
Reprocess order #1061 using stored raw_data (no Shopify API needed)
"""
import asyncio
import json
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.shopify_order import ShopifyOrder
from services.shopify_sync import shopify_sync_service


async def reprocess_from_raw():
    db = SessionLocal()
    
    try:
        # Find order #1061
        order = db.query(ShopifyOrder).filter(ShopifyOrder.order_number == "1061").first()
        
        if not order:
            print("❌ Order #1061 not found")
            return
        
        if not order.raw_data:
            print("❌ No raw_data stored for order #1061")
            return
        
        print(f"✅ Found order: #{order.order_number}")
        print(f"   Current analyses: {len(order.analyses)}")
        
        # Parse stored raw data
        order_data = json.loads(order.raw_data)
        print(f"\n📦 Loaded raw_data with {len(order_data.get('line_items', []))} line items")
        
        # Delete existing analyses
        analyses_to_delete = list(order.analyses)
        for analysis in analyses_to_delete:
            db.delete(analysis)
        db.commit()
        print(f"🗑️  Deleted {len(analyses_to_delete)} existing analyses")
        
        # Re-sync with updated parser
        print(f"\n♻️  Re-processing with updated parser...")
        synced_order = await shopify_sync_service.sync_order(order_data, db)
        
        print(f"\n✅ Reprocessed successfully!")
        print(f"   New analyses: {len(synced_order.analyses)}\n")
        
        # Show detailed results
        for i, analysis in enumerate(synced_order.analyses, 1):
            print(f"Analysis {i}:")
            print(f"  Product: {analysis.product_title}")
            print(f"  Variant: {analysis.variant_title}")
            print(f"  Person 1: {analysis.person1_name}")
            print(f"    Birth Place: {analysis.person1_birth_place}")
            print(f"    Coordinates: ({analysis.person1_latitude}, {analysis.person1_longitude})")
            if analysis.person2_name:
                print(f"  Person 2: {analysis.person2_name}")
                print(f"    Birth Place: {analysis.person2_birth_place}")
                print(f"    Coordinates: ({analysis.person2_latitude}, {analysis.person2_longitude})")
            print()
            
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(reprocess_from_raw())
