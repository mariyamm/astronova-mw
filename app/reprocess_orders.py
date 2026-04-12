"""
Re-process existing orders to create analyses that were missed
"""
import asyncio
from db.database import SessionLocal
from models.shopify_order import ShopifyOrder
from services.shopify_client import shopify_client
from services.shopify_sync import shopify_sync_service


async def reprocess_order(order_number: str):
    """Re-process a specific order by fetching full data from Shopify"""
    db = SessionLocal()
    try:
        # Find the order in our database
        order = db.query(ShopifyOrder).filter(ShopifyOrder.order_number == order_number).first()
        
        if not order:
            print(f"❌ Order #{order_number} not found in database!")
            return
        
        print(f"\n✅ Found order: #{order.order_number}")
        print(f"   Customer: {order.customer_name}")
        print(f"   Shopify ID: {order.shopify_order_id}")
        print(f"   Current analyses count: {len(order.analyses)}")
        
        # Fetch full order data from Shopify API
        print(f"\n🔄 Fetching full order data from Shopify API...")
        
        try:
            full_order_data = await shopify_client.get_order(int(order.shopify_order_id))
            
            line_items = full_order_data.get("line_items", [])
            print(f"✅ Retrieved full order with {len(line_items)} line items")
            
            # Show what properties exist
            for idx, item in enumerate(line_items, 1):
                properties = item.get("properties", [])
                print(f"\n   Line Item {idx}: {item.get('title')}")
                print(f"      Properties: {len(properties)}")
                for prop in properties[:3]:  # Show first 3 properties
                    print(f"         - {prop.get('name')}: {prop.get('value')}")
            
            # Re-process line items to create analyses
            print(f"\n{'='*80}")
            print("🔄 Re-processing line items to create analyses...")
            print(f"{'='*80}\n")
            
            await shopify_sync_service._process_line_items(order, line_items, db)
            
            db.commit()
            db.refresh(order)
            
            print(f"\n✅ Re-processing complete!")
            print(f"   New analyses count: {len(order.analyses)}")
            
            return True
            
        except Exception as api_error:
            print(f"❌ Error fetching from Shopify API: {api_error}")
            import traceback
            traceback.print_exc()
            return False
        
    finally:
        db.close()


async def reprocess_all_orders_without_analyses():
    """Re-process all orders that have 0 analyses"""
    db = SessionLocal()
    try:
        # Find all orders with 0 analyses
        from sqlalchemy import func
        from models.shopify_order import Analysis
        
        orders_without_analyses = db.query(ShopifyOrder).outerjoin(Analysis).group_by(ShopifyOrder.id).having(func.count(Analysis.id) == 0).all()
        
        print(f"\n🔍 Found {len(orders_without_analyses)} orders without analyses:")
        for order in orders_without_analyses:
            print(f"   - Order #{order.order_number} ({order.customer_name})")
        
        if not orders_without_analyses:
            print("\n✅ All orders have analyses!")
            return
        
        print(f"\n🔄 Re-processing {len(orders_without_analyses)} orders...")
        
        for order in orders_without_analyses:
            print(f"\n{'='*80}")
            success = await reprocess_order(order.order_number)
            if success:
                print(f"✅ Order #{order.order_number} re-processed successfully")
            else:
                print(f"❌ Failed to re-process order #{order.order_number}")
        
        print(f"\n{'='*80}")
        print("✅ Batch re-processing complete!")
        print(f"{'='*80}\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Re-process specific order
        order_number = sys.argv[1]
        asyncio.run(reprocess_order(order_number))
    else:
        # Re-process all orders without analyses
        asyncio.run(reprocess_all_orders_without_analyses())
