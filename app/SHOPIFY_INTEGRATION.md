# Shopify Integration Setup

## Overview
The AstroNova admin panel now includes Shopify integration to fetch and display orders with their line items.

## Features
- ✅ Fetch orders from Shopify
- ✅ View order details and line items
- ✅ Filter orders by status (any, open, closed, cancelled)
- ✅ View customer information and shipping addresses
- ✅ Permission-based access control

## Setup Instructions

### 1. Create a Shopify Private App

1. Log in to your Shopify admin panel
2. Go to **Settings** → **Apps and sales channels** 
3. Click **Develop apps**
4. Click **Create an app**
5. Give it a name (e.g., "AstroNova Integration")
6. Click **Configure Admin API scopes**
7. Enable the following scopes:
   - `read_orders` - Required to fetch orders
   - `read_products` - Optional, for product details
   - `read_customers` - Optional, for customer details

8. Click **Save**
9. Click **Install app**
10. Copy the **Admin API access token** (you'll only see this once!)

### 2. Configure Environment Variables

Update your `.env` file in the `app/` directory:

```env
# Shopify Configuration
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shppa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2024-01
```

Replace:
- `your-store.myshopify.com` with your actual Shopify store URL
- `shppa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with your Admin API access token

### 3. Add Permissions to Admin User

The new Shopify permissions have been added to the database:
- **Преглед на Shopify поръчки** (shopify_orders_view) - View orders
- **Управление на Shopify поръчки** (shopify_orders_manage) - Manage orders

Admin users automatically have all permissions. For other users, assign the permissions through the admin panel.

### 4. Restart the Application

After updating the `.env` file, restart your application:

```powershell
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Using the Shopify Orders Page

1. Log in to the admin panel
2. Navigate to **Shopify Поръчки** in the sidebar
3. Use the filters to select:
   - **Status**: any, open, closed, cancelled
   - **Limit**: Number of orders to fetch (10-250)
4. Click **Обнови** to refresh the orders
5. Click the **👁️** icon to view order details and line items

## API Endpoints

### Get Orders
```
GET /api/shopify/orders?status=any&limit=50
```

Query Parameters:
- `status`: Order status (any, open, closed, cancelled)
- `limit`: Number of orders (max 250)
- `created_at_min`: Minimum creation date (ISO 8601)
- `created_at_max`: Maximum creation date (ISO 8601)

### Get Single Order
```
GET /api/shopify/orders/{order_id}
```

### Get Order Line Items
```
GET /api/shopify/orders/{order_id}/line-items
```

### Get Order Count
```
GET /api/shopify/orders/count?status=any
```

## Security

- All endpoints require authentication (JWT token)
- Users need the `shopify_orders_view` permission
- Admin users have access by default
- API tokens are stored securely in environment variables

## Troubleshooting

### "Грешка при зареждане на поръчки"
1. Check that your `SHOPIFY_SHOP_URL` is correct (format: `store-name.myshopify.com`)
2. Verify your `SHOPIFY_ACCESS_TOKEN` is valid
3. Ensure the app has the required API scopes (`read_orders`)
4. Check that the token hasn't expired

### Orders Not Loading
1. Verify your Shopify store has orders
2. Try different status filters
3. Check server logs for API errors
4. Ensure your IP isn't rate-limited by Shopify

### Permission Denied
1. Make sure the user has the `shopify_orders_view` permission
2. Check that permissions were added to the database (run `add_shopify_permissions.py`)
3. Admins should have access automatically

## Rate Limits

Shopify has API rate limits:
- **REST Admin API**: 2 requests per second per app
- The client includes timeout handling (30 seconds)
- Consider implementing caching for frequently accessed data

## Future Enhancements

Potential features to add:
- [ ] Cache orders in local database
- [ ] Sync orders automatically on schedule
- [ ] Export orders to CSV/Excel
- [ ] Filter by date range
- [ ] Search orders by customer name/email
- [ ] Order fulfillment management
- [ ] Webhook integration for real-time updates
