import hmac
import hashlib
import json
import logging
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.order import Order, PaymentStatus, OrderStatus
from app.models.payment import Payment
from app.config import settings

logger = logging.getLogger(__name__)


def is_mock_mode() -> bool:
    """Check if Razorpay is configured with mock/dummy keys for local development."""
    return (
        not settings.RAZORPAY_KEY_ID
        or not settings.RAZORPAY_KEY_SECRET
        or settings.RAZORPAY_KEY_ID.startswith("rzp_test_mock")
    )


def create_razorpay_order(amount_rupees: float, order_id: int) -> dict:
    """
    Create a Razorpay order on the server using trusted pricing data.
    Amount is calculated on the server and converted to paise (INR 1 = 100 paise).
    """
    amount_paise = int(round(amount_rupees * 100))

    if is_mock_mode():
        logger.info(f"Using demo mode for Razorpay order creation (Order #{order_id}, Amount: ₹{amount_rupees})")
        return {
            "id": f"order_demo_{order_id}",
            "amount": amount_paise,
            "currency": "INR",
            "demo_mode": True
        }

    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rzp_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"order_{order_id}",
            "notes": {
                "order_id": str(order_id),
                "store": settings.APP_NAME
            }
        })
        rzp_order["demo_mode"] = False
        return rzp_order
    except Exception as e:
        logger.error(f"Razorpay order creation failed for Order #{order_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to initiate payment with Razorpay: {str(e)}")


def verify_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> bool:
    """Verify standard Razorpay payment checkout signature."""
    if is_mock_mode():
        return True

    if not settings.RAZORPAY_KEY_SECRET or not razorpay_signature:
        return False

    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """
    Verify the cryptographic HMAC-SHA256 signature sent by Razorpay in X-Razorpay-Signature.
    Requires the webhook secret configured in Razorpay Dashboard.
    """
    if is_mock_mode():
        if signature == "mock_signature" or not settings.RAZORPAY_WEBHOOK_SECRET:
            return True

    if not settings.RAZORPAY_WEBHOOK_SECRET or not signature:
        logger.warning("Webhook verification failed: RAZORPAY_WEBHOOK_SECRET or signature missing.")
        return False

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def handle_payment_success(
    db: Session,
    order: Order,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: Optional[str] = None,
    method: Optional[str] = None
) -> Order:
    """
    Idempotently mark an order as paid and record/update payment details.
    Guarantees no duplicate order fulfillment, double inventory deductions, or repeat notifications.
    """
    # If order is already paid, return early (idempotent fulfillment)
    if order.payment_status == PaymentStatus.PAID:
        logger.info(f"Order #{order.id} is already marked PAID. Skipping duplicate fulfillment.")
        return order

    # Check if a payment record already exists for this transaction
    payment = None
    if razorpay_payment_id:
        payment = db.query(Payment).filter(Payment.razorpay_payment_id == razorpay_payment_id).first()

    if not payment:
        payment = Payment(
            order_id=order.id,
            razorpay_order_id=razorpay_order_id or order.razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            amount=order.total_amount,
            currency="INR",
            status="success",
            method=method or "online"
        )
        db.add(payment)
    else:
        payment.status = "success"
        if razorpay_signature:
            payment.razorpay_signature = razorpay_signature
        if method:
            payment.method = method

    # Update order status
    order.payment_status = PaymentStatus.PAID
    order.status = OrderStatus.CONFIRMED
    if razorpay_order_id:
        order.razorpay_order_id = razorpay_order_id

    db.commit()
    db.refresh(order)

    # Trigger admin order notification idempotently
    try:
        from app.services.notification_service import create_admin_order_notification
        create_admin_order_notification(db, order)
    except Exception as e:
        logger.warning(f"Admin notification failed for order #{order.id}: {e}")

    return order


def handle_payment_failure(
    db: Session,
    order: Order,
    razorpay_order_id: Optional[str] = None,
    razorpay_payment_id: Optional[str] = None,
    error_description: Optional[str] = None,
    method: Optional[str] = None
) -> Order:
    """Record a failed payment attempt without cancelling an already paid order."""
    if order.payment_status == PaymentStatus.PAID:
        logger.warning(f"Received failure for already PAID order #{order.id}. Ignoring failure.")
        return order

    # Create or update payment record
    payment = None
    if razorpay_payment_id:
        payment = db.query(Payment).filter(Payment.razorpay_payment_id == razorpay_payment_id).first()

    if not payment and razorpay_payment_id:
        payment = Payment(
            order_id=order.id,
            razorpay_order_id=razorpay_order_id or order.razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            amount=order.total_amount,
            currency="INR",
            status="failed",
            method=method
        )
        db.add(payment)
    elif payment:
        payment.status = "failed"

    order.payment_status = PaymentStatus.FAILED
    if error_description:
        order.notes = f"Payment failure: {error_description}"

    db.commit()
    db.refresh(order)
    return order


def confirm_payment(
    db: Session,
    order_id: int,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> Order:
    """Verify standard client checkout redirect and confirm payment."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment verification failed: Invalid signature")

    return handle_payment_success(
        db=db,
        order=order,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature
    )


def process_razorpay_webhook(db: Session, raw_body: bytes, signature: str) -> dict:
    """
    Process inbound signed Razorpay webhooks.
    Supported events:
    - order.paid: Razorpay marks the order as fully paid
    - payment.captured: Individual payment capture confirmation
    - payment.failed: Payment transaction failed or card declined
    """
    if not verify_webhook_signature(raw_body, signature):
        logger.error("Razorpay webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event_payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Could not parse webhook JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_name = event_payload.get("event")
    payload = event_payload.get("payload", {})
    logger.info(f"Processing Razorpay webhook event: {event_name}")

    if event_name in ("order.paid", "payment.captured", "payment.authorized"):
        payment_entity = payload.get("payment", {}).get("entity", {})
        order_entity = payload.get("order", {}).get("entity", {})

        rzp_order_id = payment_entity.get("order_id") or order_entity.get("id")
        rzp_payment_id = payment_entity.get("id")
        method = payment_entity.get("method")
        notes = payment_entity.get("notes") or order_entity.get("notes") or {}

        # Look up order in DB
        order = None
        if rzp_order_id:
            order = db.query(Order).filter(Order.razorpay_order_id == rzp_order_id).first()

        if not order and "order_id" in notes:
            try:
                local_order_id = int(notes["order_id"])
                order = db.query(Order).filter(Order.id == local_order_id).first()
            except (ValueError, TypeError):
                pass

        if not order:
            logger.warning(f"Webhook received for unknown order. Rzp Order ID: {rzp_order_id}, Notes: {notes}")
            return {"status": "ignored", "reason": "Order not found in database", "event": event_name}

        handle_payment_success(
            db=db,
            order=order,
            razorpay_order_id=rzp_order_id,
            razorpay_payment_id=rzp_payment_id,
            method=method
        )
        return {"status": "success", "event": event_name, "order_id": order.id, "order_number": order.order_number}

    elif event_name == "payment.failed":
        payment_entity = payload.get("payment", {}).get("entity", {})
        rzp_order_id = payment_entity.get("order_id")
        rzp_payment_id = payment_entity.get("id")
        error_desc = payment_entity.get("error_description") or payment_entity.get("error_reason") or "Payment failed"
        method = payment_entity.get("method")
        notes = payment_entity.get("notes") or {}

        order = None
        if rzp_order_id:
            order = db.query(Order).filter(Order.razorpay_order_id == rzp_order_id).first()

        if not order and "order_id" in notes:
            try:
                order = db.query(Order).filter(Order.id == int(notes["order_id"])).first()
            except (ValueError, TypeError):
                pass

        if order:
            handle_payment_failure(
                db=db,
                order=order,
                razorpay_order_id=rzp_order_id,
                razorpay_payment_id=rzp_payment_id,
                error_description=error_desc,
                method=method
            )
            return {"status": "failed_recorded", "event": event_name, "order_id": order.id}

        return {"status": "ignored", "reason": "Order not found for failed payment", "event": event_name}

    # Acknowledge any other events from Razorpay without error
    return {"status": "acknowledged", "event": event_name}

