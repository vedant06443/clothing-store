"""
Notification service for simulating WhatsApp, SMS, and Email customer updates.
"""
from typing import Dict, Any


def generate_order_notifications(order_data: Dict[str, Any], status: str) -> Dict[str, str]:
    """Generate simulated WhatsApp, SMS, and Email notification texts."""
    order_num = order_data.get("order_number", "SC-ORDER")
    customer_name = order_data.get("shipping_name", "Customer")
    total = order_data.get("total", 0)

    messages = {}

    if status == "PENDING" or status == "CONFIRMED":
        messages["whatsapp"] = (
            f"🪷 *Suyog Collection Order Confirmation*\n\n"
            f"Namaste {customer_name}! Your order *#{order_num}* for ₹{total:,.0f} has been confirmed.\n"
            f"We are preparing your items with love.\n\n"
            f"Track your order here: https://suyogcollection.com/orders/{order_data.get('id', '')}"
        )
        messages["sms"] = (
            f"Suyog Collection: Order #{order_num} confirmed! Amount: INR {total:,.0f}. "
            f"Track status at suyogcollection.com/orders/{order_data.get('id', '')}"
        )
        messages["email"] = (
            f"Subject: Order Confirmation - #{order_num}\n\n"
            f"Dear {customer_name},\n\n"
            f"Thank you for shopping at Suyog Collection! Your order #{order_num} is confirmed.\n"
            f"Order Total: ₹{total:,.0f}\n\n"
            f"Warm Regards,\nSuyog Collection Team"
        )
    elif status == "SHIPPED":
        tracking = order_data.get("tracking_number", "TRK98234710")
        courier = order_data.get("courier_name", "BlueDart")
        messages["whatsapp"] = (
            f"🚚 *Your Suyog Collection Order is On Its Way!*\n\n"
            f"Order *#{order_num}* has been dispatched via *{courier}* (AWB: {tracking}).\n"
            f"Expected delivery: Within 3-4 business days.\n\n"
            f"Live Tracking: https://suyogcollection.com/orders/{order_data.get('id', '')}"
        )
        messages["sms"] = (
            f"Suyog Collection: Order #{order_num} shipped via {courier} (AWB: {tracking}). "
            f"Track: suyogcollection.com/orders/{order_data.get('id', '')}"
        )
        messages["email"] = (
            f"Subject: Your Order #{order_num} Has Shipped!\n\n"
            f"Dear {customer_name},\n\n"
            f"Your package has been dispatched via {courier} with tracking number {tracking}."
        )
    elif status == "DELIVERED":
        messages["whatsapp"] = (
            f"🎉 *Delivered! How did we do?*\n\n"
            f"Your Suyog Collection order *#{order_num}* has been delivered.\n"
            f"We hope you love your new outfit! Share a photo review and get 15% off your next purchase."
        )
        messages["sms"] = (
            f"Suyog Collection: Order #{order_num} delivered. Thank you for shopping with us! Share a review on suyogcollection.com"
        )
        messages["email"] = (
            f"Subject: Your Order #{order_num} Has Been Delivered!\n\n"
            f"Dear {customer_name},\n\nYour order has been delivered successfully. Enjoy your new look!"
        )
    else:
        messages["whatsapp"] = f"Suyog Collection: Order #{order_num} status updated to {status}."
        messages["sms"] = f"Suyog Collection: Order #{order_num} status: {status}."
        messages["email"] = f"Subject: Order #{order_num} Status Update\n\nStatus: {status}"

    return messages
