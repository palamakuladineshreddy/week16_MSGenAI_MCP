# -- SERVER SIDE --
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from fastmcp import FastMCP

# In-memory inventory database
inventory = {
    "LAPTOP001": {
        "name": "Dell Latitude 7420",
        "category": "Electronics",
        "quantity": 15,
        "min_threshold": 5,
        "price": 1200.00,
        "supplier": "Dell Technologies",
        "last_updated": "2025-01-15",
        "transactions": [
            {"date": "2025-01-10", "type": "purchase", "quantity": 20, "unit_cost": 1150.00},
            {"date": "2025-01-12", "type": "sale", "quantity": 5, "unit_price": 1200.00}
        ]
    },
    "CHAIR042": {
        "name": "Ergonomic Office Chair",
        "category": "Furniture",
        "quantity": 8,
        "min_threshold": 3,
        "price": 350.00,
        "supplier": "Office Depot",
        "last_updated": "2025-01-14",
        "transactions": [
            {"date": "2025-01-05", "type": "purchase", "quantity": 12, "unit_cost": 320.00},
            {"date": "2025-01-08", "type": "sale", "quantity": 4, "unit_price": 350.00}
        ]
    },
    "PAPER001": {
        "name": "A4 Copy Paper (500 sheets)",
        "category": "Office Supplies",
        "quantity": 2,
        "min_threshold": 10,
        "price": 8.99,
        "supplier": "Staples",
        "last_updated": "2025-01-13",
        "transactions": [
            {"date": "2025-01-01", "type": "purchase", "quantity": 50, "unit_cost": 7.50},
            {"date": "2025-01-10", "type": "sale", "quantity": 48, "unit_price": 8.99}
        ]
    },
    "MONITOR055": {
        "name": "Samsung 27\" 4K Monitor",
        "category": "Electronics",
        "quantity": 12,
        "min_threshold": 4,
        "price": 450.00,
        "supplier": "Samsung",
        "last_updated": "2025-01-16",
        "transactions": [
            {"date": "2025-01-15", "type": "purchase", "quantity": 15, "unit_cost": 400.00},
            {"date": "2025-01-16", "type": "sale", "quantity": 3, "unit_price": 450.00}
        ]
    }
}
# Create MCP server
mcp = FastMCP("InventoryManager")

# Tool: Check stock levels
@mcp.tool()
def check_stock(item_code: str) -> str:
    """
    Check current stock level, price, and status for a specific inventory item.

    Args:
        item_code: The unique identifier for the item (e.g., 'LAPTOP001', 'CHAIR042').
    """
    item = inventory.get(item_code)
    if not item:
        return f"Item code '{item_code}' not found in inventory."

    status_icon = "🔴" if item['quantity'] <= item['min_threshold'] else "🟡" if item['quantity'] <= item['min_threshold'] * 2 else "🟢"
    stock_status = "CRITICAL" if item['quantity'] <= item['min_threshold'] else "LOW" if item['quantity'] <= item['min_threshold'] * 2 else "GOOD"

    total_value = item['quantity'] * item['price']

    return f"""
{status_icon} Stock Report: {item['name']} ({item_code})
─────────────────────────────────────────────
Current Stock: {item['quantity']} units
Minimum Threshold: {item['min_threshold']} units
Status: {stock_status}
Unit Price: ${item['price']:.2f}
Total Value: ${total_value:.2f}
Supplier: {item['supplier']}
Last Updated: {item['last_updated']}
"""

# Tool: Add stock (purchase/restock)
@mcp.tool()
def add_stock(item_code: str, quantity: int, unit_cost: float = 0.0) -> str:
    """
    Restock an item by adding a specific quantity to the current inventory.

    Args:
        item_code: The unique identifier for the item to restock.
        quantity: The number of units to add (must be a positive integer).
        unit_cost: The cost per unit for this specific purchase. If 0.0, the default supplier cost is used.
    """
    if item_code not in inventory:
        return f"Item code '{item_code}' not found."

    if quantity <= 0:
        return "Quantity must be greater than 0."

    item = inventory[item_code]
    old_quantity = item['quantity']
    item['quantity'] += quantity
    item['last_updated'] = datetime.now().strftime("%Y-%m-%d")

    # Record transaction
    actual_cost = unit_cost if unit_cost > 0 else item['price'] * 0.85
    item['transactions'].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "purchase",
        "quantity": quantity,
        "unit_cost": actual_cost
    })

    return f"Added {quantity} units to {item['name']}. New level: {item['quantity']}."

# Tool: Remove stock (sale/usage)
@mcp.tool()
def remove_stock(item_code: str, quantity: int, unit_price: float = 0.0) -> str:
    """
    Record a sale or usage of an item by removing quantity from inventory.

    Args:
        item_code: The unique identifier for the item being removed.
        quantity: The number of units to remove from stock.
        unit_price: The selling price per unit. If 0.0, the standard list price is used.
    """
    if item_code not in inventory:
        return f"Item code '{item_code}' not found."

    item = inventory[item_code]
    if item['quantity'] < quantity:
        return f"Insufficient stock! Available: {item['quantity']}, Requested: {quantity}"

    old_quantity = item['quantity']
    item['quantity'] -= quantity
    item['last_updated'] = datetime.now().strftime("%Y-%m-%d")

    actual_price = unit_price if unit_price > 0 else item['price']
    item['transactions'].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "sale",
        "quantity": quantity,
        "unit_price": actual_price
    })

    return f"Removed {quantity} units from {item['name']}. New level: {item['quantity']}."

# Tool: Get low stock alerts
@mcp.tool()
def get_low_stock_alerts() -> str:
    """
    Retrieve a list of all items currently below their minimum stock threshold or at low levels.
    """
    low_stock_items = []
    critical_items = []

    for code, item in inventory.items():
        if item['quantity'] <= item['min_threshold']:
            critical_items.append((code, item))
        elif item['quantity'] <= item['min_threshold'] * 2:
            low_stock_items.append((code, item))

    if not low_stock_items and not critical_items:
        return "All items are well-stocked!"

    alert_msg = "Stock Alerts\n" + "="*50 + "\n"
    if critical_items:
        alert_msg += "\nCRITICAL - Reorder Immediately:\n"
        for code, item in critical_items:
            alert_msg += f"  • {item['name']} ({code}): {item['quantity']} units\n"
    
    return alert_msg

# Tool: Get inventory summary by category
@mcp.tool()
def get_inventory_summary(category: str = "") -> str:
    """
    Get a summary of inventory totals, unit counts, and values, optionally filtered by category.

    Args:
        category: Filter the summary by a specific category (e.g., 'Electronics', 'Furniture'). Leave empty for all categories.
    """
    filtered_items = inventory.items()
    if category:
        filtered_items = [(code, item) for code, item in inventory.items() if item['category'].lower() == category.lower()]
    
    if not filtered_items:
        return "No items found."

    total_value = sum(i['quantity'] * i['price'] for c, i in filtered_items)
    return f"Inventory contains {len(filtered_items)} types of items with a total value of ${total_value:,.2f}."

# Tool: Get transaction history
@mcp.tool()
def get_transaction_history(item_code: str, limit: int = 5) -> str:
    """
    Get the most recent purchase and sale transactions for a specific item.

    Args:
        item_code: The unique identifier for the item.
        limit: The maximum number of recent transactions to return.
    """
    if item_code not in inventory:
        return f"Item '{item_code}' not found."
    
    item = inventory[item_code]
    recent = sorted(item['transactions'], key=lambda x: x['date'], reverse=True)[:limit]
    
    res = f"History for {item['name']}:\n"
    for t in recent:
        res += f"- {t['date']}: {t['type']} of {t['quantity']} units\n"
    return res

# Tool: Create new item
@mcp.tool()
def create_item(item_code: str, name: str, category: str, initial_quantity: int, price: float, min_threshold: int, supplier: str) -> str:
    """
    Register a brand new product in the inventory system.

    Args:
        item_code: A new unique identifier for the item (e.g., 'DESK001').
        name: The descriptive name of the product.
        category: The group this item belongs to (e.g., 'Office Supplies').
        initial_quantity: Starting stock level.
        price: The standard selling price per unit.
        min_threshold: The stock level that triggers a reorder alert.
        supplier: The name of the primary vendor for this item.
    """
    if item_code in inventory:
        return "Item already exists."

    inventory[item_code] = {
        "name": name, "category": category, "quantity": initial_quantity,
        "min_threshold": min_threshold, "price": price, "supplier": supplier,
        "last_updated": datetime.now().strftime("%Y-%m-%d"), "transactions": []
    }
    return f"Item {name} created successfully."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)