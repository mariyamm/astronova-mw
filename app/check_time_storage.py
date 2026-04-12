from db.database import SessionLocal
from models.shopify_order import ShopifyOrder
import json

db = SessionLocal()

# Get the most recent order
order = db.query(ShopifyOrder).order_by(ShopifyOrder.order_created_at.desc()).first()

if order:
    print(f'ORDER #{order.order_number}')
    print(f'Analyses: {len(order.analyses)}\n')
    
    for i, analysis in enumerate(order.analyses, 1):
        print(f'[{i}] {analysis.product_type}')
        print(f'    Person 1:')
        print(f'      Name: {analysis.person1_name}')
        print(f'      Birth Date/Time: {analysis.person1_birth_date}')
        print(f'      Birth Place: {analysis.person1_birth_place}')
        print(f'      Timezone: {analysis.person1_timezone} ({analysis.person1_timezone_offset})')
        
        if analysis.person2_name:
            print(f'    Person 2:')
            print(f'      Name: {analysis.person2_name}')
            print(f'      Birth Date/Time: {analysis.person2_birth_date}')
            print(f'      Birth Place: {analysis.person2_birth_place}')
            print(f'      Timezone: {analysis.person2_timezone} ({analysis.person2_timezone_offset})')
        print()
    
    # Check raw data
    if order.raw_data:
        raw = json.loads(order.raw_data) if isinstance(order.raw_data, str) else order.raw_data
        print('RAW SHOPIFY DATA:')
        for item in raw.get('line_items', []):
            print(f'\nProduct: {item.get("title")}')
            for prop in item.get('properties', []):
                if 'DOB' in prop.get('name', '') or 'TOB' in prop.get('name', ''):
                    print(f'  {prop.get("name")}: {prop.get("value")}')

db.close()
