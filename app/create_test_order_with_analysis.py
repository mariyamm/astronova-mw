"""
Create a test order with analysis data for testing the UI
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from db.database import SessionLocal
from models.shopify_order import ShopifyOrder, Analysis, ProductType, Gender

def create_test_order():
    """Create a test order with analyses"""
    db = SessionLocal()
    
    try:
        # Create order
        order = ShopifyOrder(
            shopify_order_id="TEST_ORDER_WITH_ANALYSES",
            order_number="TEST-001",
            customer_name="Мария Иванова",
            customer_email="maria@example.com",
            customer_phone="+359888123456",
            total_price="150.00",
            currency="BGN",
            financial_status="paid",
            fulfillment_status="unfulfilled",
            order_created_at=datetime.now(),
            raw_data='{"test": true}'
        )
        
        db.add(order)
        db.flush()
        
        # Create analysis 1 - Individual detailed analysis
        analysis1 = Analysis(
            order_id=order.id,
            shopify_line_item_id="TEST_LINE_ITEM_1",
            product_type=ProductType.DETAILED_ANALYSIS,
            product_title="Подробен астрологичен анализ",
            variant_title="Стандартен пакет",
            sku="ASTRO-DETAILED-001",
            quantity=1,
            price="75.00",
            person1_name="Мария Петрова Иванова",
            person1_gender=Gender.FEMALE,
            person1_birth_date=datetime(1990, 5, 15, 14, 30),
            person1_birth_place="София, България",
            person1_latitude=42.6977,
            person1_longitude=23.3219,
            person1_timezone="Europe/Sofia",
            person1_timezone_offset="+02:00",
            is_processed=False,
            notes=None
        )
        
        # Create analysis 2 - Love synastry
        analysis2 = Analysis(
            order_id=order.id,
            shopify_line_item_id="TEST_LINE_ITEM_2",
            product_type=ProductType.LOVE_SYNASTRY,
            product_title="Любовна синастрия за двойки",
            variant_title="Премиум анализ",
            sku="ASTRO-SYNASTRY-001",
            quantity=1,
            price="75.00",
            person1_name="Георги Димитров",
            person1_gender=Gender.MALE,
            person1_birth_date=datetime(1988, 3, 20, 10, 15),
            person1_birth_place="Пловдив, България",
            person1_latitude=42.1354,
            person1_longitude=24.7453,
            person1_timezone="Europe/Sofia",
            person1_timezone_offset="+02:00",
            person2_name="Елена Георгиева",
            person2_gender=Gender.FEMALE,
            person2_birth_date=datetime(1992, 7, 8, 18, 45),
            person2_birth_place="Варна, България",
            person2_latitude=43.2141,
            person2_longitude=27.9147,
            person2_timezone="Europe/Sofia",
            person2_timezone_offset="+02:00",
            is_processed=False,
            notes=None
        )
        
        db.add(analysis1)
        db.add(analysis2)
        
        db.commit()
        
        print("✅ Test order created successfully!")
        print(f"   Order: #{order.order_number}")
        print(f"   Customer: {order.customer_name}")
        print(f"   Analyses: 2")
        print(f"   - {analysis1.product_title} (Person: {analysis1.person1_name})")
        print(f"   - {analysis2.product_title} (Couple: {analysis2.person1_name} & {analysis2.person2_name})")
        print("\n🌐 Now refresh the admin panel to see it!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_order()
