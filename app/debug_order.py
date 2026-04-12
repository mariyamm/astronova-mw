"""
Debug script to inspect order 1062's raw data and re-process it
"""
import asyncio
import json
from db.database import SessionLocal
from models.shopify_order import ShopifyOrder
from services.shopify_sync import shopify_sync_service


async def debug_order():
    db = SessionLocal()
    try:
        # Get order 1062
        order = db.query(ShopifyOrder).filter(ShopifyOrder.order_number == "1062").first()
        
        if not order:
            print("❌ Order 1062 not found in database!")
            return
        
        print(f"\n✅ Found order: #{order.order_number}")
        print(f"   Customer: {order.customer_name}")
        print(f"   Total: {order.total_price} {order.currency}")
        print(f"   Current analyses count: {len(order.analyses)}")
        
        # Parse raw data
        if not order.raw_data:
            print("\n❌ No raw_data found for this order!")
            return
        
        raw_json = json.loads(order.raw_data)
        line_items = raw_json.get("line_items", [])
        
        print(f"\n📦 Raw data contains {len(line_items)} line items")
        
        for idx, item in enumerate(line_items, 1):
            print(f"\n--- LINE ITEM {idx} ---")
            print(f"ID: {item.get('id')}")
            print(f"Title: {item.get('title')}")
            print(f"SKU: {item.get('sku')}")
            print(f"Variant Title: {item.get('variant_title')}")
            print(f"Price: {item.get('price')}")
            print(f"Quantity: {item.get('quantity')}")
            
            properties = item.get("properties", [])
            print(f"\nProperties ({len(properties)} found):")
            if properties:
                for prop in properties:
                    print(f"  • {prop.get('name')}: {prop.get('value')}")
            else:
                print("  (no properties)")
        
        # Try to re-process
        print(f"\n{'='*80}")
        print("🔄 Attempting to re-process line items...")
        print(f"{'='*80}\n")
        
        await shopify_sync_service._process_line_items(order, line_items, db)
        
        db.commit()
        print(f"\n✅ Re-processing complete!")
        print(f"   New analyses count: {len(order.analyses)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(debug_order())
