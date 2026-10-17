"""
Notification service for real-time admin alerts, WebSockets, email notifications,
and customer update simulations.
"""
import logging
import smtplib
import asyncio
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem
from app.models.notification import Notification
from app.config import settings

logger = logging.getLogger(__name__)


# ──────────────── WebSocket Connection Manager ────────────────

class NotificationConnectionManager:
    """Manages real-time WebSocket connections for active admin dashboards."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"[WS] Admin connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"[WS] Admin disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        """Asynchronously broadcast data to all active admin WebSocket clients."""
        with self._lock:
            connections = list(self.active_connections)

        stale_connections = []
        for connection in connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.warning(f"[WS] Error broadcasting to connection: {e}")
                stale_connections.append(connection)

        if stale_connections:
            with self._lock:
                for stale in stale_connections:
                    if stale in self.active_connections:
                        self.active_connections.remove(stale)


notification_manager = NotificationConnectionManager()


def broadcast_sync(data: dict):
    """
    Safely trigger an asynchronous broadcast from synchronous or background code.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notification_manager.broadcast(data))
    except RuntimeError:
        # No running event loop in current thread; run in fresh loop in background thread
        def _run_in_thread():
            asyncio.run(notification_manager.broadcast(data))
        t = threading.Thread(target=_run_in_thread, daemon=True)
        t.start()


# ──────────────── Optional Email Notification ────────────────

def send_admin_order_email_sync(order: Order, customer_name: str, product_name: str, quantity: int):
    """Send order notification email to the store admin if SMTP is configured."""
    if not settings.SMTP_HOST or not settings.ADMIN_EMAIL:
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New Order Received - #{order.order_number}"
        msg["From"] = settings.SMTP_USERNAME or settings.ADMIN_EMAIL
        msg["To"] = settings.ADMIN_EMAIL

        payment_status_str = order.payment_status if isinstance(order.payment_status, str) else getattr(order.payment_status, "value", str(order.payment_status))
        order_status_str = order.status if isinstance(order.status, str) else getattr(order.status, "value", str(order.status))

        text_body = (
            f"New order received.\n\n"
            f"Order ID: #{order.order_number}\n"
            f"Customer: {customer_name}\n"
            f"Phone: {order.shipping_phone or 'N/A'}\n"
            f"Product: {product_name}\n"
            f"Quantity: {quantity}\n"
            f"Total: ₹{order.total_amount:,.0f}\n"
            f"Payment Method: {order.payment_method}\n"
            f"Payment Status: {payment_status_str}\n"
            f"Order Status: {order_status_str}\n\n"
            f"View Order in Admin Panel: /orders/{order.id}\n"
        )
        msg.attach(MIMEText(text_body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"[EMAIL] Sent new order notification email to {settings.ADMIN_EMAIL} for #{order.order_number}")
    except Exception as e:
        logger.warning(f"[EMAIL] Failed to send admin order email: {e}")


def send_admin_order_email_background(order: Order, customer_name: str, product_name: str, quantity: int):
    """Dispatch email in daemon thread to avoid blocking order completion."""
    thread = threading.Thread(
        target=send_admin_order_email_sync,
        args=(order, customer_name, product_name, quantity),
        daemon=True
    )
    thread.start()


# ──────────────── Core Notification Creation ────────────────

def create_admin_order_notification(db: Session, order: Order) -> Optional[Notification]:
    """
    Creates a new Notification record for a successfully confirmed order and
    broadcasts it immediately via WebSocket and optional email.
    Guarantees idempotency (no duplicate notifications for the same order).
    """
    try:
        # 1. Prevent duplicate notifications for the same order
        existing = db.query(Notification).filter(Notification.order_id == order.id).first()
        if existing:
            return existing

        # Ensure order items and user details are loaded
        if not order.items:
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        else:
            items = order.items

        # Extract product details
        if items:
            first_item = items[0]
            first_product_name = first_item.product_name or (first_item.product.name if first_item.product else "Handcrafted Saree")
            total_qty = sum(item.quantity for item in items)
            if len(items) > 1:
                product_display = f"{first_product_name} (+{len(items)-1} more)"
            else:
                product_display = first_product_name
        else:
            first_product_name = "Handcrafted Saree"
            product_display = first_product_name
            total_qty = 1

        customer_name = order.shipping_name or (order.user.full_name if order.user else "Customer")
        formatted_amount = f"₹{order.total_amount:,.0f}"

        title = "🔔 New Order Received!"
        message = (
            f"Order #{order.order_number}\n"
            f"Customer: {customer_name}\n"
            f"Product: {product_display}\n"
            f"Quantity: {total_qty}\n"
            f"Amount: {formatted_amount}"
        )

        # 2. Persist notification in database
        notification = Notification(
            order_id=order.id,
            title=title,
            message=message,
            is_read=False
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        unread_count = db.query(Notification).filter(Notification.is_read == False).count()

        # 3. Broadcast real-time WebSocket event
        event_payload = {
            "type": "new_order",
            "notification": {
                "id": notification.id,
                "order_id": order.id,
                "order_number": order.order_number,
                "customer_name": customer_name,
                "product_name": product_display,
                "quantity": total_qty,
                "amount": order.total_amount,
                "formatted_amount": formatted_amount,
                "status": order.status if isinstance(order.status, str) else getattr(order.status, "value", str(order.status)),
                "payment_status": order.payment_status if isinstance(order.payment_status, str) else getattr(order.payment_status, "value", str(order.payment_status)),
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                "is_read": False
            },
            "unread_count": unread_count
        }
        broadcast_sync(event_payload)

        # 4. Trigger optional store admin email in background
        send_admin_order_email_background(order, customer_name, product_display, total_qty)

        return notification
    except Exception as e:
        logger.error(f"[NOTIFICATION] Error creating admin order notification for order {order.id}: {e}")
        # Never break the order flow if notification creation encounters an unexpected error
        return None


# ──────────────── Customer Notification Simulation Helpers ────────────────

def generate_order_notifications(order_data: Dict[str, Any], status: str) -> Dict[str, str]:
    """Generate simulated WhatsApp, SMS, and Email notification texts for customers."""
    order_num = order_data.get("order_number", "SC-ORDER")
    customer_name = order_data.get("shipping_name", "Customer")
    total = order_data.get("total", 0)

    messages = {}

    if status in ("PENDING", "CONFIRMED"):
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
