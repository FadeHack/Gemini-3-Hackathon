"""
Festival Calendar Utilities
Helpers for finding upcoming festivals and getting multipliers
"""

import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from config.constants import FESTIVAL_MULTIPLIERS


def load_festival_calendar(calendar_path: str = "./data/festivals.json") -> List[Dict]:
    """
    Load festival calendar from JSON

    Args:
        calendar_path: Path to festivals.json

    Returns:
        List of festival definitions
    """
    try:
        with open(calendar_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("festivals", [])
    except Exception as e:
        logger.error(f"Failed to load festival calendar: {e}")
        return []


def get_upcoming_festivals(
    current_date: Optional[datetime] = None,
    days_ahead: int = 30,
    calendar_path: str = "./data/festivals.json"
) -> List[Dict]:
    """
    Get upcoming festivals within specified period

    Args:
        current_date: Reference date (defaults to today)
        days_ahead: How many days to look ahead
        calendar_path: Path to festivals data

    Returns:
        List of upcoming festivals with start dates
    """
    if current_date is None:
        current_date = datetime.now()

    festivals = load_festival_calendar(calendar_path)
    upcoming = []

    for festival in festivals:
        # Get typical months when festival occurs
        typical_months = festival.get("typical_months", [])

        if not typical_months:
            continue

        # For simplicity, use current year or next year
        for month in typical_months:
            # Estimate festival date (middle of month for simplicity)
            # In production, you'd use actual dates or a proper calendar
            try:
                fest_date = datetime(current_date.year, month, 15)

                # If festival already passed this year, try next year
                if fest_date < current_date:
                    fest_date = datetime(current_date.year + 1, month, 15)

                # Check if within our lookahead window
                days_until = (fest_date - current_date).days
                if 0 <= days_until <= days_ahead:
                    upcoming.append({
                        **festival,
                        "starts": fest_date.isoformat(),
                        "start_date": fest_date.date().isoformat(),
                        "days_until": days_until
                    })
                    break  # Only add once per festival

            except ValueError:
                continue

    # Sort by start date
    upcoming.sort(key=lambda x: x["days_until"])

    logger.info(f"Found {len(upcoming)} upcoming festivals in next {days_ahead} days")
    return upcoming


def get_festival_multiplier(
    festival_id: str,
    category: str
) -> float:
    """
    Get demand multiplier for a category during a festival

    Args:
        festival_id: Festival identifier (e.g., "diwali", "navratri")
        category: Product category

    Returns:
        Multiplier (1.0 = no change)
    """
    fest_multipliers = FESTIVAL_MULTIPLIERS.get(festival_id, {})
    return fest_multipliers.get(category, 1.0)


def is_festival_active(
    festival: Dict,
    check_date: Optional[datetime] = None
) -> bool:
    """
    Check if a festival is currently active

    Args:
        festival: Festival data with start date and duration
        check_date: Date to check (defaults to today)

    Returns:
        True if festival is active on check_date
    """
    if check_date is None:
        check_date = datetime.now()

    try:
        start_date_str = festival.get("starts") or festival.get("start_date", "")
        if not start_date_str:
            return False

        start_date = datetime.fromisoformat(start_date_str.replace("Z", ""))
        duration = festival.get("duration_days", 1)
        end_date = start_date + timedelta(days=duration)

        return start_date.date() <= check_date.date() <= end_date.date()

    except Exception as e:
        logger.error(f"Error checking festival active status: {e}")
        return False


def get_active_festivals(
    check_date: Optional[datetime] = None,
    calendar_path: str = "./data/festivals.json"
) -> List[Dict]:
    """
    Get all currently active festivals

    Args:
        check_date: Date to check (defaults to today)
        calendar_path: Path to festivals data

    Returns:
        List of active festivals
    """
    if check_date is None:
        check_date = datetime.now()

    # Get festivals happening soon
    upcoming = get_upcoming_festivals(
        current_date=check_date,
        days_ahead=60,  # Look ahead 2 months
        calendar_path=calendar_path
    )

    # Filter to only those currently active
    active = [f for f in upcoming if is_festival_active(f, check_date)]

    logger.info(f"Found {len(active)} active festivals on {check_date.date()}")
    return active


def get_festival_prep_days(festival_id: str) -> int:
    """
    Get number of days before festival to start extra ordering

    Args:
        festival_id: Festival identifier

    Returns:
        Number of prep days
    """
    # Load festivals to get prep days
    festivals = load_festival_calendar()

    for fest in festivals:
        if fest.get("id") == festival_id:
            return fest.get("prep_days_before", 3)

    return 3  # Default prep days
