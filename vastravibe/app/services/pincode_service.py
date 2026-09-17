"""
Pincode and logistics service for Indian delivery estimation.
"""
from typing import Dict, Any
from datetime import datetime, timedelta

# Major city express zones
METRO_PINCODES = {
    "11": ("Delhi NCR", 2, True),
    "12": ("Haryana / NCR", 2, True),
    "20": ("UP / Noida / Ghaziabad", 2, True),
    "40": ("Mumbai & Thane", 2, True),
    "41": ("Pune", 2, True),
    "56": ("Bengaluru", 2, True),
    "50": ("Hyderabad", 2, True),
    "60": ("Chennai", 3, True),
    "70": ("Kolkata", 3, True),
    "38": ("Ahmedabad", 3, True),
    "30": ("Jaipur", 3, True),
}


def check_pincode_delivery(pincode: str) -> Dict[str, Any]:
    """Check serviceability and estimated delivery date for a 6-digit Indian PIN code."""
    pincode = str(pincode).strip()
    if len(pincode) != 6 or not pincode.isdigit():
        return {
            "serviceable": False,
            "message": "Please enter a valid 6-digit Indian PIN code."
        }

    prefix = pincode[:2]
    if prefix in METRO_PINCODES:
        region, days, cod = METRO_PINCODES[prefix]
    else:
        region = "Rest of India"
        days = 4
        cod = True

    est_date = datetime.now() + timedelta(days=days)
    formatted_date = est_date.strftime("%A, %d %B")

    return {
        "serviceable": True,
        "pincode": pincode,
        "region": region,
        "estimated_days": days,
        "estimated_date": formatted_date,
        "cod_available": cod,
        "shipping_fee": 0,  # Free standard delivery
        "express_available": days <= 2,
        "message": f"Delivery by {formatted_date} | FREE Delivery & COD available"
    }
