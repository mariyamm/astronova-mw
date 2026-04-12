# 🛍️ Shopify Integration Setup Guide

This guide will help you set up the Shopify integration for AstroNova Admin.

## Prerequisites

✅ You need a Shopify store
✅ Admin access to create private apps
✅ TimeZoneDB account (free tier is enough)

---

## Step 1: Create Shopify Private App

1. **Go to Shopify Admin:**
   ```
   https://your-store.myshopify.com/admin
   ```

2. **Navigate to Apps:**
   - Settings → Apps and sales channels
   - Click "Develop apps"
   - Click "Create an app"

3. **Name the app:**
   - Name: `AstroNova Admin Integration`
   - Click "Create app"

4. **Configure API scopes:**
   - Click "Configure Admin API scopes"
   - Select these scopes:
     - ✅ `read_orders` - Read orders
     - ✅ `read_products` - Read products (optional, for product info)
   - Click "Save"

5. **Install the app:**
   - Click "Install app"
   - Confirm installation

6. **Get your Access Token:**
   - Click "API credentials" tab
   - Under "Admin API access token", click "Reveal token once"
   - **⚠️ IMPORTANT:** Copy this token NOW - you won't be able to see it again!
   - It looks like: `shpat_xxxxxxxxxxxxxxxxxxxxx`

7. **Note your Shop URL:**
   - Your shop URL is: `your-store.myshopify.com`
   - Don't include `https://` or trailing slashes

---

## Step 2: Get TimeZoneDB API Key

1. **Sign up for free:**
   ```
   https://timezonedb.com/register
   ```

2. **Get your API key:**
   - After registration, go to: https://timezonedb.com/api
   - Copy your API key from the page
   - It looks like: `ABCDEF123456`

3. **Free tier limits:**
   - 1 request per second
   - 1 API key
   - Perfect for this use case!

---

## Step 3: Configure AstroNova Admin

1. **Open the `.env` file:**
   ```powershell
   cd c:\dev\AstroNova-f\app
   notepad .env
   ```

2. **Add your credentials:**
   ```env
   # Shopify Configuration
   SHOPIFY_SHOP_URL=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx
   SHOPIFY_API_VERSION=2024-01
   
   # TimeZoneDB API
   TIMEZONEDB_API_KEY=ABCDEF123456
   ```

3. **Save the file**

---

## Step 4: Initialize Shopify Tables

If you haven't already created the Shopify tables:

```powershell
cd c:\dev\AstroNova-f\app
.\.venv\Scripts\Activate.ps1
python create_shopify_tables.py
python add_shopify_permissions.py
```

Expected output:
```
✅ Shopify tables created successfully!
   - shopify_orders
   - analyses

✅ Added: Преглед на Shopify поръчки
✅ Added: Управление на Shopify поръчки

✅ Added 2 new permissions
```

---

## Step 5: Add Shopify Permissions to Admin User

1. **Log in to AstroNova Admin:**
   ```
   http://localhost:8000
   Username: admin
   Password: Admin@123
   ```

2. **Go to Users page**

3. **Edit your admin user:**
   - Click "Редактирай" on your admin user

4. **Enable Shopify permissions:**
   - Find "Преглед на Shopify поръчки"
   - Find "Управление на Shopify поръчки"
   - Check both boxes
   - Click "Запази"

---

## Step 6: Test the Integration

1. **Restart the server:**
   ```powershell
   # Stop the server (Ctrl+C)
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Go to Shopify Orders page:**
   - Navigate in the menu: **"Shopify Поръчки"**

3. **Click "Синхронизирай от Shopify"**
   - This will fetch the last 50 orders from your store
   - Processing may take a few seconds

4. **Verify the data:**
   - Orders should appear in the list
   - Click on an order to expand it
   - Check that person data is correctly extracted
   - Verify that timezones are calculated

---

## Step 7: Configure Product Properties in Shopify

For the system to extract person data, your Shopify products need custom properties in the line items.

### Required Properties Format

**For Individual Analysis (1 person):**
```
Име: [Name]
Пол: [Gender]
Дата на раждане: YYYY-MM-DD
Час на раждане: HH:MM
Място на раждане: [City]
Latitude: [Decimal latitude]
Longitude: [Decimal longitude]
```

**For Couple Analysis (2 people):**
```
Име 1: [Name 1]
Пол 1: [Gender 1]
Дата на раждане 1: YYYY-MM-DD
Час на раждане 1: HH:MM
Място на раждане 1: [City 1]
Latitude 1: [Decimal latitude 1]
Longitude 1: [Decimal longitude 1]

Име 2: [Name 2]
Пол 2: [Gender 2]
Дата на раждане 2: YYYY-MM-DD
Час на раждане 2: HH:MM
Място на раждане 2: [City 2]
Latitude 2: [Decimal latitude 2]
Longitude 2: [Decimal longitude 2]
```

### How to Add Properties to Products

1. **Edit your product in Shopify**
2. **Add custom fields** for customers to fill in
3. **Or** use an app like "Product Options by Bold" or "Infinite Options"
4. **Make sure** the property names match the expected format above

---

## Troubleshooting

### Problem: "Failed to sync orders"

**Solution:**
- Check that `SHOPIFY_SHOP_URL` doesn't include `https://` or trailing `/`
- Verify your access token is correct
- Make sure the app has `read_orders` scope

### Problem: "Person data not extracted"

**Solution:**
- Check the property names in your Shopify orders
- Compare with the expected format in `services/shopify_parser.py`
- Add debug logging to see what properties are being received

### Problem: "Timezone not calculated"

**Solution:**
- Verify TimeZoneDB API key is correct
- Check that latitude/longitude are valid numbers
- The system will use fallback calculation (longitude/15) if API fails

### Problem: "Orders appear but analyses are empty"

**Solution:**
- This means line items don't have the required properties
- Check your Shopify product configuration
- Make sure customers are filling in all required fields

---

## Product Type Detection

The system automatically detects product types by keywords:

| Product Type | Keywords | Color |
|--------------|----------|-------|
| **Любовна синастрия** | синастрия, synastry, love, couple, двойка | 🩷 Pink |
| **Подробен анализ** | анализ, analysis, natal, раждане | 💙 Sky Blue |

Make sure your product titles or SKUs contain these keywords.

---

## Next Steps

✅ Test with a real order
✅ Verify person data extraction
✅ Check timezone calculations
✅ Adjust parser if needed for your property names

---

**Need help?** Check the main README.md or the code in:
- `services/shopify_parser.py` - Property parsing logic
- `services/timezone_service.py` - Timezone calculation
- `services/shopify_sync.py` - Sync orchestration

🌟 Happy analyzing!
