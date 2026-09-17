import hmac
import hashlib
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.order import Order, PaymentStatus
from app.models.payment import Payment
from app.config import settings


def create_razorpay_order(amount_rupees: float, order_id: int) -> dict:
    """Create a Razorpay order and return order data."""
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        # Demo mode: return a fake order for testing
        return {
            "id": f"order_demo_{order_id}",
            "amount": int(amount_rupees * 100),
            "currency": "INR",
            "demo_mode": True
        }

    import razorpay
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    rzp_order = client.order.create({
        "amount": int(amount_rupees * 100),  # in paise
        "currency": "INR",
        "receipt": f"order_{order_id}",
        "notes": {"order_id": str(order_id)}
    })
    return rzp_order


def verify_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> bool:
    """Verify Razorpay payment signature."""
    if not settings.RAZORPAY_KEY_SECRET:
        return True  # demo mode

    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def confirm_payment(
    db: Session,
    order_id: int,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> Order:
    """Verify and confirm payment, update order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Create payment record
    payment = Payment(
        order_id=order.id,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
        amount=order.total_amount,
        status="success"
    )
    db.add(payment)

    # Update order
    order.payment_status = PaymentStatus.PAID
    order.status = "Confirmed"
    order.razorpay_order_id = razorpay_order_id

    db.commit()
    db.refresh(order)
    return order
