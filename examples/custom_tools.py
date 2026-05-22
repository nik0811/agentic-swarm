"""
Custom Tools Example
====================

Demonstrates how to create and use custom tools with the Agentic Swarm SDK.

Features shown:
- Creating tools with @tool decorator
- Sync and async tools
- Tools with complex return types
- Tool schema auto-generation
- Combining built-in and custom tools
- Tool validation and error handling
"""

import asyncio
import json
from typing import Optional
from datetime import datetime

from agentic_swarm import Agent, tool, Tool


# =============================================================================
# 1. BASIC TOOLS - Using @tool decorator
# =============================================================================

@tool
def calculate_total(items: list, tax_rate: float = 0.1) -> dict:
    """Calculate total price with tax.
    
    Args:
        items: List of items with 'price' and 'quantity' keys
        tax_rate: Tax rate as decimal (default 10%)
    
    Returns:
        Dictionary with subtotal, tax, and total
    """
    subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
    tax = subtotal * tax_rate
    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "total": round(subtotal + tax, 2)
    }


@tool
def search_products(query: str, category: Optional[str] = None, limit: int = 5) -> list:
    """Search product catalog.
    
    Args:
        query: Search query string
        category: Optional category filter
        limit: Maximum results to return
    
    Returns:
        List of matching products
    """
    # Simulated product database
    products = [
        {"id": "P001", "name": "Laptop Pro", "category": "electronics", "price": 1299.99},
        {"id": "P002", "name": "Wireless Mouse", "category": "electronics", "price": 29.99},
        {"id": "P003", "name": "USB-C Cable", "category": "electronics", "price": 14.99},
        {"id": "P004", "name": "Desk Chair", "category": "furniture", "price": 249.99},
        {"id": "P005", "name": "Standing Desk", "category": "furniture", "price": 599.99},
        {"id": "P006", "name": "Monitor Arm", "category": "accessories", "price": 89.99},
    ]
    
    results = []
    query_lower = query.lower()
    
    for product in products:
        if query_lower in product["name"].lower():
            if category is None or product["category"] == category:
                results.append(product)
                if len(results) >= limit:
                    break
    
    return results


@tool
def check_inventory(product_id: str) -> dict:
    """Check inventory status for a product.
    
    Args:
        product_id: The product ID to check
    
    Returns:
        Inventory status with stock level and availability
    """
    # Simulated inventory
    inventory = {
        "P001": {"stock": 15, "warehouse": "A"},
        "P002": {"stock": 150, "warehouse": "B"},
        "P003": {"stock": 500, "warehouse": "B"},
        "P004": {"stock": 8, "warehouse": "C"},
        "P005": {"stock": 3, "warehouse": "C"},
        "P006": {"stock": 45, "warehouse": "A"},
    }
    
    if product_id in inventory:
        inv = inventory[product_id]
        return {
            "product_id": product_id,
            "in_stock": inv["stock"] > 0,
            "quantity": inv["stock"],
            "warehouse": inv["warehouse"],
            "low_stock": inv["stock"] < 10
        }
    
    return {"product_id": product_id, "error": "Product not found"}


# =============================================================================
# 2. ASYNC TOOLS - For I/O operations
# =============================================================================

@tool
async def fetch_exchange_rate(from_currency: str, to_currency: str) -> dict:
    """Fetch current exchange rate between currencies.
    
    Args:
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., EUR)
    
    Returns:
        Exchange rate information
    """
    # Simulated API call (would be real HTTP request in production)
    await asyncio.sleep(0.1)  # Simulate network latency
    
    rates = {
        ("USD", "EUR"): 0.92,
        ("USD", "GBP"): 0.79,
        ("USD", "JPY"): 149.50,
        ("EUR", "USD"): 1.09,
        ("GBP", "USD"): 1.27,
    }
    
    key = (from_currency.upper(), to_currency.upper())
    if key in rates:
        return {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "rate": rates[key],
            "timestamp": datetime.now().isoformat()
        }
    
    return {"error": f"Rate not available for {from_currency} to {to_currency}"}


@tool
async def send_notification(user_id: str, message: str, channel: str = "email") -> dict:
    """Send notification to a user.
    
    Args:
        user_id: Target user ID
        message: Notification message
        channel: Delivery channel (email, sms, push)
    
    Returns:
        Notification status
    """
    await asyncio.sleep(0.05)  # Simulate sending
    
    return {
        "status": "sent",
        "user_id": user_id,
        "channel": channel,
        "message_preview": message[:50] + "..." if len(message) > 50 else message,
        "sent_at": datetime.now().isoformat()
    }


# =============================================================================
# 3. COMPLEX TOOLS - With validation and business logic
# =============================================================================

@tool
def place_order(
    customer_id: str,
    items: list,
    shipping_address: dict,
    payment_method: str = "credit_card"
) -> dict:
    """Place a new order.
    
    Args:
        customer_id: Customer identifier
        items: List of items with product_id and quantity
        shipping_address: Address with street, city, zip, country
        payment_method: Payment method (credit_card, paypal, bank_transfer)
    
    Returns:
        Order confirmation with order ID and estimated delivery
    """
    # Validate items
    if not items:
        return {"error": "No items in order"}
    
    # Validate address
    required_fields = ["street", "city", "zip", "country"]
    missing = [f for f in required_fields if f not in shipping_address]
    if missing:
        return {"error": f"Missing address fields: {missing}"}
    
    # Calculate order total (simplified)
    order_total = sum(item.get("quantity", 1) * 50 for item in items)  # Placeholder pricing
    
    # Generate order
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "status": "confirmed",
        "items_count": len(items),
        "total": order_total,
        "payment_method": payment_method,
        "shipping_address": shipping_address,
        "estimated_delivery": "3-5 business days",
        "created_at": datetime.now().isoformat()
    }


@tool
def generate_report(
    report_type: str,
    start_date: str,
    end_date: str,
    format: str = "summary"
) -> dict:
    """Generate a business report.
    
    Args:
        report_type: Type of report (sales, inventory, customers)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        format: Output format (summary, detailed, csv)
    
    Returns:
        Report data based on type and date range
    """
    valid_types = ["sales", "inventory", "customers"]
    if report_type not in valid_types:
        return {"error": f"Invalid report type. Choose from: {valid_types}"}
    
    # Simulated report data
    reports = {
        "sales": {
            "total_revenue": 125000,
            "orders_count": 450,
            "average_order": 277.78,
            "top_products": ["Laptop Pro", "Standing Desk", "Wireless Mouse"]
        },
        "inventory": {
            "total_products": 156,
            "low_stock_items": 12,
            "out_of_stock": 3,
            "warehouse_utilization": "78%"
        },
        "customers": {
            "total_customers": 1250,
            "new_customers": 89,
            "returning_rate": "67%",
            "top_segments": ["Enterprise", "SMB", "Individual"]
        }
    }
    
    return {
        "report_type": report_type,
        "period": f"{start_date} to {end_date}",
        "format": format,
        "data": reports[report_type],
        "generated_at": datetime.now().isoformat()
    }


# =============================================================================
# 4. CREATING TOOLS PROGRAMMATICALLY
# =============================================================================

def create_validator_tool(field_name: str, pattern: str):
    """Factory function to create validation tools."""
    import re
    
    def validate(value: str) -> dict:
        f"""Validate {field_name} format."""
        is_valid = bool(re.match(pattern, value))
        return {
            "field": field_name,
            "value": value,
            "valid": is_valid,
            "pattern": pattern
        }
    
    return Tool(
        name=f"validate_{field_name}",
        description=f"Validate {field_name} against pattern: {pattern}",
        func=validate
    )

# Create specific validators
validate_email = create_validator_tool("email", r"^[\w\.-]+@[\w\.-]+\.\w+$")
validate_phone = create_validator_tool("phone", r"^\+?[\d\s-]{10,}$")


# =============================================================================
# 5. DEMONSTRATION
# =============================================================================

async def main():
    print("=" * 60)
    print("  CUSTOM TOOLS EXAMPLE")
    print("=" * 60)
    
    # --- Demo 1: Tool Schema Generation ---
    print("\n[1] Auto-Generated Tool Schemas\n")
    
    tools = [calculate_total, search_products, check_inventory, place_order]
    
    for t in tools:
        schema = t.to_openai_schema()
        print(f"  {t.name}:")
        print(f"    Description: {schema['function']['description'][:60]}...")
        params = schema['function']['parameters']['properties']
        print(f"    Parameters: {list(params.keys())}")
        print()
    
    # --- Demo 2: Direct Tool Execution ---
    print("\n[2] Direct Tool Execution\n")
    
    # Search products
    print("  Searching for 'desk'...")
    results = search_products.func("desk")
    print(f"  Found: {json.dumps(results, indent=4)}")
    
    # Check inventory
    print("\n  Checking inventory for P005...")
    inv = check_inventory.func("P005")
    print(f"  Inventory: {json.dumps(inv, indent=4)}")
    
    # Calculate total
    print("\n  Calculating order total...")
    items = [
        {"price": 599.99, "quantity": 1},
        {"price": 29.99, "quantity": 2}
    ]
    total = calculate_total.func(items, tax_rate=0.08)
    print(f"  Total: {json.dumps(total, indent=4)}")
    
    # --- Demo 3: Async Tool Execution ---
    print("\n[3] Async Tool Execution\n")
    
    print("  Fetching exchange rate USD → EUR...")
    rate = await fetch_exchange_rate.func("USD", "EUR")
    print(f"  Rate: {json.dumps(rate, indent=4)}")
    
    print("\n  Sending notification...")
    notif = await send_notification.func("user123", "Your order has shipped!", "push")
    print(f"  Result: {json.dumps(notif, indent=4)}")
    
    # --- Demo 4: Complex Tool with Validation ---
    print("\n[4] Complex Tool with Validation\n")
    
    print("  Placing order...")
    order = place_order.func(
        customer_id="CUST-001",
        items=[
            {"product_id": "P001", "quantity": 1},
            {"product_id": "P002", "quantity": 2}
        ],
        shipping_address={
            "street": "123 Main St",
            "city": "San Francisco",
            "zip": "94102",
            "country": "USA"
        },
        payment_method="credit_card"
    )
    print(f"  Order: {json.dumps(order, indent=4)}")
    
    # --- Demo 5: Programmatic Tool Creation ---
    print("\n[5] Programmatically Created Tools\n")
    
    print("  Validating email...")
    email_result = validate_email.func("user@example.com")
    print(f"  Result: {json.dumps(email_result, indent=4)}")
    
    print("\n  Validating phone...")
    phone_result = validate_phone.func("+1 555-123-4567")
    print(f"  Result: {json.dumps(phone_result, indent=4)}")
    
    # --- Demo 6: Agent with Custom Tools ---
    print("\n[6] Agent with Custom Tools (Mock LLM)\n")
    
    # Create agent with all custom tools
    all_tools = [
        calculate_total,
        search_products,
        check_inventory,
        fetch_exchange_rate,
        send_notification,
        place_order,
        generate_report,
        validate_email,
        validate_phone,
    ]
    
    agent = Agent(
        name="commerce_assistant",
        role="E-commerce assistant that helps with products, orders, and reports",
        tools=all_tools,
        max_iterations=5
    )
    
    print(f"  Agent: {agent.name}")
    print(f"  Role: {agent.role}")
    print(f"  Tools available: {len(all_tools)}")
    for t in all_tools:
        name = t.name if hasattr(t, 'name') else t.__name__
        print(f"    - {name}")
    
    # --- Demo 7: Generate Report ---
    print("\n[7] Generate Business Report\n")
    
    report = generate_report.func(
        report_type="sales",
        start_date="2024-01-01",
        end_date="2024-03-31",
        format="summary"
    )
    print(f"  Report: {json.dumps(report, indent=4)}")
    
    print("\n" + "=" * 60)
    print("  CUSTOM TOOLS EXAMPLE COMPLETE")
    print("=" * 60)
    print("""
    Key Takeaways:
    
    1. Use @tool decorator for simple tool creation
    2. Add type hints and docstrings for auto-schema generation
    3. Support both sync and async tools
    4. Use Tool class for programmatic creation
    5. Tools can have complex validation logic
    6. Combine custom tools with built-in tools
    7. Pass tools to Agent via the 'tools' parameter
    """)


if __name__ == "__main__":
    asyncio.run(main())
