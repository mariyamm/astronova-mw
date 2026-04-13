"""
Shopify API Client

This service handles all interactions with the Shopify API
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import settings


class ShopifyClient:
    """Client for interacting with Shopify Admin API"""
    
    def __init__(self):
        self.shop_url = settings.SHOPIFY_SHOP_URL
        self.access_token = settings.SHOPIFY_ACCESS_TOKEN
        self.api_version = settings.SHOPIFY_API_VERSION
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Shopify API requests"""
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    async def get_orders(
        self, 
        status: str = "any",
        limit: int = 50,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from Shopify
        
        Args:
            status: Order status (any, open, closed, cancelled)
            limit: Number of orders to fetch (max 250)
            created_at_min: Minimum creation date (ISO 8601 format)
            created_at_max: Maximum creation date (ISO 8601 format)
            
        Returns:
            List of orders with line items
        """
        params = {
            "status": status,
            "limit": min(limit, 250)
        }
        
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/orders.json",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("orders", [])
        except httpx.HTTPError as e:
            print(f"Error fetching orders from Shopify: {e}")
            raise
    
    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        Fetch a single order by ID
        
        Args:
            order_id: Shopify order ID
            
        Returns:
            Order details with line items
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/orders/{order_id}.json",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("order", {})
        except httpx.HTTPError as e:
            print(f"Error fetching order {order_id} from Shopify: {e}")
            raise
    
    async def get_order_count(self, status: str = "any") -> int:
        """
        Get count of orders
        
        Args:
            status: Order status
            
        Returns:
            Number of orders
        """
        params = {"status": status}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/orders/count.json",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("count", 0)
        except httpx.HTTPError as e:
            print(f"Error fetching order count from Shopify: {e}")
            raise
    
    def extract_line_items(self, order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and format line items from an order
        
        Args:
            order: Shopify order object
            
        Returns:
            List of formatted line items
        """
        line_items = []
        
        for item in order.get("line_items", []):
            line_items.append({
                "id": item.get("id"),
                "variant_id": item.get("variant_id"),
                "product_id": item.get("product_id"),
                "title": item.get("title"),
                "variant_title": item.get("variant_title"),
                "sku": item.get("sku"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
                "total_discount": item.get("total_discount"),
                "fulfillment_status": item.get("fulfillment_status"),
                "properties": item.get("properties", [])
            })
        
        return line_items


# Singleton instance
shopify_client = ShopifyClient()
