"""
Test reprocessing order #1061 with updated parser
"""
import asyncio
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.shopify_order import ShopifyOrder
from services.shopify_client import shopify_client
from services.shopify_sync import shopify_sync_service


async def reprocess_order_1061():
    db = SessionLocal()
    
    try:
        # Find order #1061
        order = db.query(ShopifyOrder).filter(ShopifyOrder.order_number == "1061").first()
        
        if not order:
            print("❌ Order #1061 not found in database")
            return
        
        print(f"\n✅ Found order: #{order.order_number}")
        print(f"   Customer: {order.customer_name}")
        print(f"   Shopify ID: {order.shopify_order_id}")
        print(f"   Current analyses count: {len(order.analyses)}")
        
        # Fetch full order data from Shopify API
        print(f"\n🔄 Fetching full order data from Shopify API...")
        try:
            full_order_data = await shopify_client.get_order(int(order.shopify_order_id))
            print(f"✅ Retrieved full order data")
            print(f"   Line items: {len(full_order_data.get('line_items', []))}")
            
            # Delete existing analyses
            for analysis in order.analyses:
                db.delete(analysis)
            db.commit()
            print(f"\n🗑️  Deleted {len(order.analyses)} existing analyses")
            
            # Re-sync the order
            print(f"\n♻️  Re-processing order with updated parser...")
            synced_order = await shopify_sync_service.sync_order(full_order_data, db)
            
            print(f"\n✅ Order re-processed successfully!")
            print(f"   New analyses count: {len(synced_order.analyses)}")
            
            # Show analyses
            for i, analysis in enumerate(synced_order.analyses, 1):
                print(f"\n   Analysis {i}:")
                print(f"     Product: {analysis.product_title}")
                print(f"     Variant: {analysis.variant_title}")
                print(f"     Type: {analysis.product_type}")
                print(f"     Person 1: {analysis.person1_name} ({analysis.person1_birth_place})")
                if analysis.person2_name:
                    print(f"     Person 2: {analysis.person2_name} ({analysis.person2_birth_place})")
                
        except Exception as e:
            print(f"❌ Error fetching from Shopify API: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(reprocess_order_1061())
