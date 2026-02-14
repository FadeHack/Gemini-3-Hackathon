"""
Inventory Engine - Core inventory state management
Handles transactions, stock tracking, alerts, and daily summaries
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger
from config.constants import StockStatus, TransactionType


class InventoryEngine:
    """
    Core inventory management engine
    Tracks stock levels, processes transactions, generates alerts
    """

    def __init__(self, store_id: str, initial_inventory: Dict[str, Dict]):
        """
        Initialize inventory engine

        Args:
            store_id: Store identifier
            initial_inventory: Current inventory state from store profile
        """
        self.store_id = store_id
        self.inventory = initial_inventory.copy()
        self.transactions: List[Dict] = []
        self.daily_cash = 0.0
        self.daily_upi = 0.0
        self.daily_credit = 0.0

        logger.info(f"InventoryEngine initialized for {store_id} with {len(self.inventory)} products")

    def apply_transaction(
        self,
        product_id: str,
        quantity_change: int,
        transaction_type: str,
        price: Optional[float] = None,
        customer_name: Optional[str] = None,
        source: str = "manual"
    ) -> Dict:
        """
        Apply a transaction to inventory

        Args:
            product_id: Product SKU ID
            quantity_change: Change in quantity (negative=sold, positive=received)
            transaction_type: cash, upi, credit, or supplier_delivery
            price: Transaction price (optional)
            customer_name: Customer name for credit sales
            source: Source of transaction (kacchi_parchi, voice, manual, etc.)

        Returns:
            Transaction result with updated stock info and alerts
        """
        if product_id not in self.inventory:
            logger.warning(f"Product {product_id} not found in inventory")
            return {
                "status": "error",
                "message": f"Product {product_id} not in inventory"
            }

        item = self.inventory[product_id]
        old_stock = item.get("current_stock", 0)
        new_stock = old_stock + quantity_change

        # Validate stock levels
        if new_stock < 0:
            logger.error(f"Insufficient stock for {product_id}: {old_stock} available, {abs(quantity_change)} requested")
            return {
                "status": "error",
                "message": f"Insufficient stock: only {old_stock} available"
            }

        # Update stock
        item["current_stock"] = new_stock

        # Update daily counters
        if quantity_change < 0:  # Sale
            item["today_sold"] = item.get("today_sold", 0) + abs(quantity_change)
            if price:
                revenue = price
                item["today_revenue"] = item.get("today_revenue", 0) + revenue

                # Track payment type
                if transaction_type == "cash":
                    self.daily_cash += revenue
                elif transaction_type == "upi":
                    self.daily_upi += revenue
                elif transaction_type == "credit":
                    self.daily_credit += revenue

        elif quantity_change > 0:  # Received
            item["today_received"] = item.get("today_received", 0) + quantity_change

        # Recalculate days of stock
        avg_daily_sales = item.get("avg_daily_sales", 1) or 1  # Avoid division by zero
        days_of_stock = new_stock / avg_daily_sales if avg_daily_sales > 0 else 999

        # Determine status
        status = self._get_stock_status(days_of_stock, item.get("reorder_point", 10))
        item["status"] = status
        item["days_of_stock"] = days_of_stock

        # Generate alerts if needed
        alerts = self._generate_alerts(product_id, item, days_of_stock, status)

        # Record transaction
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "product_id": product_id,
            "quantity_change": quantity_change,
            "transaction_type": transaction_type,
            "customer_name": customer_name,
            "price": price,
            "source": source,
            "new_stock": new_stock
        }
        self.transactions.append(transaction)

        logger.info(
            f"Transaction applied: {product_id} "
            f"{quantity_change:+d} → {new_stock} stock "
            f"({days_of_stock:.1f} days)"
        )

        return {
            "status": "ok",
            "product_id": product_id,
            "old_stock": old_stock,
            "new_stock": new_stock,
            "change": quantity_change,
            "days_of_stock": days_of_stock,
            "stock_status": status,
            "alerts": alerts,
            "transaction": transaction
        }

    def calibrate_from_shelf_photo(
        self,
        visual_counts: Dict[str, int],
        confidence_threshold: float = 0.7
    ) -> Tuple[List[Dict], bool]:
        """
        Calibrate inventory based on shelf photo visual counts

        Args:
            visual_counts: {product_id: visual_count, ...}
            confidence_threshold: Minimum confidence to auto-accept

        Returns:
            (discrepancies, needs_confirmation)
        """
        discrepancies = []
        needs_confirmation = False

        for product_id, visual_count in visual_counts.items():
            if product_id not in self.inventory:
                continue

            ledger_count = self.inventory[product_id].get("current_stock", 0)
            difference = visual_count - ledger_count

            if difference != 0:
                discrepancy = {
                    "product_id": product_id,
                    "visual_count": visual_count,
                    "ledger_count": ledger_count,
                    "difference": difference,
                    "difference_pct": (abs(difference) / max(ledger_count, 1)) * 100
                }
                discrepancies.append(discrepancy)

                # Large discrepancies need confirmation
                if abs(difference) > 5 or discrepancy["difference_pct"] > 20:
                    needs_confirmation = True
                    logger.warning(
                        f"Large discrepancy for {product_id}: "
                        f"visual={visual_count}, ledger={ledger_count}"
                    )

        logger.info(f"Shelf calibration: {len(discrepancies)} discrepancies found")
        return discrepancies, needs_confirmation

    def get_daily_summary(self) -> Dict:
        """
        Generate daily P&L summary

        Returns:
            Daily summary with revenue, profit, transactions
        """
        total_revenue = self.daily_cash + self.daily_upi + self.daily_credit
        total_sold = sum(item.get("today_sold", 0) for item in self.inventory.values())
        total_received = sum(item.get("today_received", 0) for item in self.inventory.values())

        # Calculate COGS (simplified - using average purchase price)
        total_cogs = 0.0
        for item in self.inventory.values():
            sold_qty = item.get("today_sold", 0)
            purchase_price = item.get("purchase_price", 0)
            total_cogs += sold_qty * purchase_price

        gross_profit = total_revenue - total_cogs
        margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Top sellers
        top_sellers = []
        for product_id, item in self.inventory.items():
            sold = item.get("today_sold", 0)
            if sold > 0:
                top_sellers.append({
                    "product_id": product_id,
                    "name": item.get("product_name", product_id),
                    "qty": sold,
                    "revenue": item.get("today_revenue", 0)
                })
        top_sellers.sort(key=lambda x: x["revenue"], reverse=True)

        return {
            "date": datetime.now().date().isoformat(),
            "total_revenue": round(total_revenue, 2),
            "total_cogs": round(total_cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "margin_pct": round(margin_pct, 1),
            "cash_collected": round(self.daily_cash, 2),
            "upi_collected": round(self.daily_upi, 2),
            "credit_given": round(self.daily_credit, 2),
            "total_transactions": len(self.transactions),
            "items_sold": total_sold,
            "items_received": total_received,
            "top_sellers": top_sellers[:5]
        }

    def get_low_stock_items(self, threshold_days: float = 3.0) -> List[Dict]:
        """
        Get products with low stock

        Args:
            threshold_days: Days of stock threshold

        Returns:
            List of low stock items with details
        """
        low_stock = []

        for product_id, item in self.inventory.items():
            days_of_stock = item.get("days_of_stock", 999)
            status = item.get("status", "healthy")

            if status in ["critical", "warning"] or days_of_stock < threshold_days:
                low_stock.append({
                    "product_id": product_id,
                    "product_name": item.get("product_name", product_id),
                    "current_stock": item.get("current_stock", 0),
                    "days_of_stock": days_of_stock,
                    "status": status,
                    "avg_daily_sales": item.get("avg_daily_sales", 0),
                    "reorder_point": item.get("reorder_point", 0)
                })

        low_stock.sort(key=lambda x: x["days_of_stock"])
        return low_stock

    def _get_stock_status(self, days_of_stock: float, reorder_point: int) -> str:
        """Determine stock status based on days remaining"""
        if days_of_stock < 1.0:
            return StockStatus.CRITICAL
        elif days_of_stock < 3.0:
            return StockStatus.WARNING
        else:
            return StockStatus.HEALTHY

    def _generate_alerts(
        self,
        product_id: str,
        item: Dict,
        days_of_stock: float,
        status: str
    ) -> List[Dict]:
        """Generate inventory alerts for low stock"""
        alerts = []

        if status == StockStatus.CRITICAL:
            alerts.append({
                "type": "low_stock",
                "severity": "critical",
                "message": f"{item.get('product_name', product_id)} critically low - only {days_of_stock:.1f} days remaining",
                "action_required": True
            })
        elif status == StockStatus.WARNING:
            alerts.append({
                "type": "low_stock",
                "severity": "warning",
                "message": f"{item.get('product_name', product_id)} running low - {days_of_stock:.1f} days remaining",
                "action_required": False
            })

        return alerts
