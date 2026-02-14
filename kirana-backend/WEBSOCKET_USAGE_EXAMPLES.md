# WebSocket Event Usage Examples

## How to Send Real-time Updates

### 1. Send Udhaar (Credit) Update

```python
from services.websocket_service import get_websocket_manager
from datetime import datetime

ws_manager = get_websocket_manager()

# When a customer makes a credit purchase or payment
await ws_manager.send_udhaar_update(
    store_id="sharma_general_store",
    customer_name="Sharma ji",
    old_amount=2340.0,
    new_amount=2540.0,  # Added 200 rupees credit
    transaction_date=datetime.now().isoformat(),
    transaction_type="credit_given",  # or "payment_received"
    total_outstanding=8940.0  # Total across all customers
)
```

**Frontend receives:**
```json
{
  "event": "udhaar_update",
  "data": {
    "customer": "Sharma ji",
    "old_amount": 2340.0,
    "new_amount": 2540.0,
    "change": 200.0,
    "transaction_type": "credit_given",
    "transaction": {
      "date": "2026-02-14T15:30:00Z",
      "type": "credit_given",
      "amount": 200.0
    },
    "total_outstanding": 8940.0,
    "timestamp": "2026-02-14T15:30:00Z"
  },
  "timestamp": "2026-02-14T15:30:00Z"
}
```

### 2. Send P&L Update

```python
from services.websocket_service import get_websocket_manager

ws_manager = get_websocket_manager()

# When P&L changes (e.g., after a sale)
await ws_manager.send_pnl_update(
    store_id="sharma_general_store",
    pnl_data={
        "date": "2026-02-14",
        "total_revenue": 5020.0,  # Updated from 4820
        "total_cogs": 3263.0,
        "gross_profit": 1757.0,
        "margin_pct": 35.0,
        "cash_collected": 3880.0,
        "upi_collected": 980.0,
        "credit_given": 160.0,
        "total_transactions": 24,  # Incremented
        "items_sold": 49  # Incremented
    }
)
```

**Frontend receives:**
```json
{
  "event": "pnl_update",
  "data": {
    "date": "2026-02-14",
    "total_revenue": 5020.0,
    "total_cogs": 3263.0,
    "gross_profit": 1757.0,
    "margin_pct": 35.0,
    "cash_collected": 3880.0,
    "upi_collected": 980.0,
    "credit_given": 160.0,
    "total_transactions": 24,
    "items_sold": 49,
    "timestamp": "2026-02-14T15:30:00Z"
  },
  "timestamp": "2026-02-14T15:30:00Z"
}
```

## Integration with Business Logic

### Example: Credit Sale Flow

```python
async def process_credit_sale(
    store_id: str,
    customer_name: str,
    items: list,
    total_amount: float
):
    """Process a credit sale and send all relevant updates"""
    ws_manager = get_websocket_manager()

    # 1. Update inventory for each item
    for item in items:
        await ws_manager.send_inventory_update(
            store_id=store_id,
            product_id=item["sku_id"],
            product_name=item["name"],
            old_stock=item["old_stock"],
            new_stock=item["new_stock"],
            change=-item["quantity"],
            transaction_type="sale",
            reason=f"Credit sale to {customer_name}"
        )

    # 2. Update udhaar ledger
    await ws_manager.send_udhaar_update(
        store_id=store_id,
        customer_name=customer_name,
        old_amount=old_udhaar_amount,
        new_amount=old_udhaar_amount + total_amount,
        transaction_date=datetime.now().isoformat(),
        transaction_type="credit_given",
        total_outstanding=new_total_outstanding
    )

    # 3. Update P&L
    await ws_manager.send_pnl_update(
        store_id=store_id,
        pnl_data={
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_revenue": updated_revenue,
            "total_cogs": updated_cogs,
            "gross_profit": updated_profit,
            "margin_pct": (updated_profit / updated_revenue * 100),
            "cash_collected": cash_total,
            "upi_collected": upi_total,
            "credit_given": credit_total + total_amount,
            "total_transactions": transaction_count + 1,
            "items_sold": items_sold_count + len(items)
        }
    )

    # 4. Send chat confirmation
    await ws_manager.send_chat_message(
        store_id=store_id,
        message=f"✅ Credit sale recorded for {customer_name}. "
                f"Total: ₹{total_amount}. Updated udhaar balance: ₹{old_udhaar_amount + total_amount}",
        sender="ai",
        message_type="text",
        language="hinglish"
    )
```

### Example: Payment Received Flow

```python
async def process_payment_received(
    store_id: str,
    customer_name: str,
    payment_amount: float,
    payment_method: str  # "cash" or "upi"
):
    """Process a payment and send updates"""
    ws_manager = get_websocket_manager()

    # 1. Update udhaar ledger
    await ws_manager.send_udhaar_update(
        store_id=store_id,
        customer_name=customer_name,
        old_amount=old_udhaar_amount,
        new_amount=old_udhaar_amount - payment_amount,
        transaction_date=datetime.now().isoformat(),
        transaction_type="payment_received",
        total_outstanding=new_total_outstanding
    )

    # 2. Update P&L (cash/UPI collected increased)
    await ws_manager.send_pnl_update(
        store_id=store_id,
        pnl_data={
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_revenue": revenue,
            "total_cogs": cogs,
            "gross_profit": profit,
            "margin_pct": margin,
            "cash_collected": cash_total + (payment_amount if payment_method == "cash" else 0),
            "upi_collected": upi_total + (payment_amount if payment_method == "upi" else 0),
            "credit_given": credit_total - payment_amount,  # Reduced
            "total_transactions": transaction_count + 1,
            "items_sold": items_sold_count
        }
    )

    # 3. Send confirmation
    await ws_manager.send_chat_message(
        store_id=store_id,
        message=f"💰 Payment received from {customer_name}: ₹{payment_amount} via {payment_method.upper()}. "
                f"Remaining udhaar: ₹{old_udhaar_amount - payment_amount}",
        sender="ai",
        message_type="text",
        language="hinglish"
    )
```

## Testing

### Manual Test via Python

```python
import asyncio
from services.websocket_service import get_websocket_manager

async def test_udhaar_update():
    ws_manager = get_websocket_manager()

    await ws_manager.send_udhaar_update(
        store_id="sharma_general_store",
        customer_name="Test Customer",
        old_amount=1000.0,
        new_amount=1500.0,
        transaction_date="2026-02-14T15:30:00Z",
        transaction_type="credit_given",
        total_outstanding=8000.0
    )
    print("✅ Udhaar update sent!")

async def test_pnl_update():
    ws_manager = get_websocket_manager()

    await ws_manager.send_pnl_update(
        store_id="sharma_general_store",
        pnl_data={
            "date": "2026-02-14",
            "total_revenue": 5000.0,
            "total_cogs": 3250.0,
            "gross_profit": 1750.0,
            "margin_pct": 35.0,
            "cash_collected": 3000.0,
            "upi_collected": 1500.0,
            "credit_given": 500.0,
            "total_transactions": 25,
            "items_sold": 50
        }
    )
    print("✅ P&L update sent!")

# Run tests
asyncio.run(test_udhaar_update())
asyncio.run(test_pnl_update())
```

## Frontend Integration

The frontend is already configured to receive these events:

- **Udhaar updates**: Handled by `updateUdhaarFromWS()` in Zustand store
- **P&L updates**: Handled by `updatePnLFromWS()` in Zustand store

Both are wired up in `useWebSocket.ts` hooks:
```typescript
onUdhaarUpdate: (data) => {
  useStore.getState().updateUdhaarFromWS(data);
},

onPnLUpdate: (data) => {
  useStore.getState().updatePnLFromWS(data);
}
```

The UI will automatically update when these events are received!
