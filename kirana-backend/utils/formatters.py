"""
Response formatting utilities
Hinglish text formatting, number formatting, date/time helpers
"""

from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta


def format_currency(amount: float, symbol: str = "₹") -> str:
    """
    Format amount as Indian currency

    Args:
        amount: Amount to format
        symbol: Currency symbol

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1500)
        '₹1,500'
        >>> format_currency(150000)
        '₹1,50,000'
    """
    # Convert to string with 2 decimal places
    amount_str = f"{amount:.2f}"

    # Split into integer and decimal parts
    if '.' in amount_str:
        int_part, dec_part = amount_str.split('.')
    else:
        int_part = amount_str
        dec_part = "00"

    # Format integer part in Indian numbering system
    formatted_int = format_indian_number(int(int_part))

    # Remove trailing .00 for whole numbers
    if dec_part == "00":
        return f"{symbol}{formatted_int}"
    else:
        return f"{symbol}{formatted_int}.{dec_part}"


def format_indian_number(number: int) -> str:
    """
    Format number in Indian numbering system

    Args:
        number: Number to format

    Returns:
        Formatted number string

    Examples:
        >>> format_indian_number(100000)
        '1,00,000'
        >>> format_indian_number(10000000)
        '1,00,00,000'
    """
    s = str(number)
    if len(s) <= 3:
        return s

    # Indian system: last 3 digits, then groups of 2
    result = s[-3:]
    s = s[:-3]

    while s:
        result = s[-2:] + "," + result
        s = s[:-2]

    return result


def format_date_hinglish(dt: datetime, include_time: bool = False) -> str:
    """
    Format date in Hinglish style

    Args:
        dt: Datetime to format
        include_time: Whether to include time

    Returns:
        Formatted date string

    Examples:
        >>> format_date_hinglish(datetime(2026, 2, 14))
        '14 Feb 2026'
        >>> format_date_hinglish(datetime(2026, 2, 14, 15, 30), include_time=True)
        '14 Feb 2026, 3:30 PM'
    """
    # Month names
    months = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    date_str = f"{dt.day} {months[dt.month]} {dt.year}"

    if include_time:
        hour = dt.hour
        meridiem = "AM" if hour < 12 else "PM"
        if hour > 12:
            hour -= 12
        elif hour == 0:
            hour = 12

        date_str += f", {hour}:{dt.minute:02d} {meridiem}"

    return date_str


def format_relative_time_hinglish(dt: datetime) -> str:
    """
    Format relative time in Hinglish

    Args:
        dt: Datetime to format

    Returns:
        Relative time string

    Examples:
        >>> format_relative_time_hinglish(datetime.now() - timedelta(minutes=5))
        '5 minutes pehle'
        >>> format_relative_time_hinglish(datetime.now() - timedelta(hours=2))
        '2 hours pehle'
    """
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "abhi abhi"
    elif seconds < 3600:  # Less than 1 hour
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} pehle"
    elif seconds < 86400:  # Less than 1 day
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} pehle"
    elif seconds < 604800:  # Less than 1 week
        days = int(seconds / 86400)
        if days == 1:
            return "kal"
        return f"{days} din pehle"
    else:
        return format_date_hinglish(dt)


def format_days_until_hinglish(days: int) -> str:
    """
    Format days until event in Hinglish

    Args:
        days: Number of days until event

    Returns:
        Formatted string

    Examples:
        >>> format_days_until_hinglish(0)
        'aaj'
        >>> format_days_until_hinglish(1)
        'kal'
        >>> format_days_until_hinglish(5)
        '5 din mein'
    """
    if days == 0:
        return "aaj"
    elif days == 1:
        return "kal"
    elif days == 2:
        return "parson"
    else:
        return f"{days} din mein"


def format_stock_status_hinglish(days_of_stock: float, product_name: str) -> str:
    """
    Format stock status message in Hinglish

    Args:
        days_of_stock: Days of stock remaining
        product_name: Product name

    Returns:
        Formatted status message
    """
    if days_of_stock < 0.5:
        return f"⚠️ {product_name} khatam hone wala hai! Turant mangana padega."
    elif days_of_stock < 1.0:
        return f"🔴 {product_name} ka stock critically low hai - aaj hi khatam ho jayega!"
    elif days_of_stock < 2.0:
        return f"🟡 {product_name} ka stock low hai - kal tak khatam ho jayega."
    elif days_of_stock < 3.0:
        return f"🟠 {product_name} reorder karna padega - 2-3 din mein khatam hoga."
    elif days_of_stock < 7.0:
        return f"✅ {product_name} ka stock theek hai - {int(days_of_stock)} din chalega."
    else:
        return f"✅ {product_name} ka stock accha hai - {int(days_of_stock)} din chalega."


def format_urgency_hinglish(urgency: str) -> str:
    """
    Format urgency level in Hinglish

    Args:
        urgency: Urgency level (critical, high, medium, low)

    Returns:
        Formatted urgency string
    """
    urgency_map = {
        "critical": "🔴 Bahut urgent",
        "high": "🟠 Urgent",
        "medium": "🟡 Thoda urgent",
        "low": "🟢 Normal"
    }

    return urgency_map.get(urgency.lower(), urgency)


def format_payment_type_hinglish(payment_type: str) -> str:
    """
    Format payment type in Hinglish

    Args:
        payment_type: Payment type (cash, upi, credit)

    Returns:
        Formatted payment type
    """
    payment_map = {
        "cash": "💵 Nakad",
        "upi": "📱 UPI",
        "credit": "📒 Udhaar",
        "supplier_delivery": "🚚 Supplier se aaya"
    }

    return payment_map.get(payment_type.lower(), payment_type)


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Format percentage

    Args:
        value: Percentage value (e.g., 15.5 for 15.5%)
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimal_places}f}%"


def create_summary_message(
    total_revenue: float,
    items_sold: int,
    cash_sales: float,
    upi_sales: float,
    credit_sales: float
) -> str:
    """
    Create daily summary message in Hinglish

    Args:
        total_revenue: Total revenue
        items_sold: Number of items sold
        cash_sales: Cash sales amount
        upi_sales: UPI sales amount
        credit_sales: Credit sales amount

    Returns:
        Formatted summary message
    """
    msg = f"📊 **Aaj ka Business:**\n\n"
    msg += f"💰 Total: {format_currency(total_revenue)}\n"
    msg += f"📦 Items: {items_sold}\n\n"

    msg += f"**Payment Breakdown:**\n"
    if cash_sales > 0:
        msg += f"💵 Cash: {format_currency(cash_sales)}\n"
    if upi_sales > 0:
        msg += f"📱 UPI: {format_currency(upi_sales)}\n"
    if credit_sales > 0:
        msg += f"📒 Udhaar: {format_currency(credit_sales)}\n"

    return msg


def create_procurement_message(
    order_id: str,
    total_items: int,
    total_cost: float,
    savings: float,
    distributor_count: int,
    festival_name: Optional[str] = None
) -> str:
    """
    Create procurement order message in Hinglish

    Args:
        order_id: Order ID
        total_items: Number of items
        total_cost: Total order cost
        savings: Amount saved
        distributor_count: Number of distributors
        festival_name: Upcoming festival name

    Returns:
        Formatted procurement message
    """
    msg = f"🛒 **Procurement Order Ready!**\n\n"
    msg += f"Order ID: `{order_id}`\n\n"

    if festival_name:
        msg += f"🎊 {festival_name} ke liye special order\n\n"

    msg += f"📦 Items: {total_items}\n"
    msg += f"💰 Total: {format_currency(total_cost)}\n"

    if savings > 0:
        savings_pct = (savings / total_cost) * 100 if total_cost > 0 else 0
        msg += f"💸 Savings: {format_currency(savings)} ({format_percentage(savings_pct)})\n"

    msg += f"🏪 Distributors: {distributor_count}\n\n"
    msg += f"✅ Best prices automatically selected!"

    return msg


def create_alert_message(alerts: list) -> str:
    """
    Create alert message from list of alerts

    Args:
        alerts: List of alert dicts

    Returns:
        Formatted alert message
    """
    if not alerts:
        return "✅ Sab kuch theek hai! Koi alert nahi."

    msg = "⚠️ **Alerts:**\n\n"

    for alert in alerts:
        product = alert.get("product_name", "Unknown")
        urgency = alert.get("urgency", "medium")
        days_left = alert.get("days_of_stock", 0)

        icon = "🔴" if urgency == "critical" else "🟡"
        msg += f"{icon} {product}: {days_left:.1f} din ka stock\n"

    return msg
