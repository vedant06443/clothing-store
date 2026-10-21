import logging
from typing import Optional
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.utils.dependencies import get_current_user
from app.config import settings
from app.services.payment_service import (
    process_razorpay_webhook,
    handle_payment_failure,
    is_mock_mode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature")
):
    """
    Inbound webhook endpoint for Razorpay.
    Verifies the HMAC SHA-256 signature against RAZORPAY_WEBHOOK_SECRET.
    Guarantees idempotent processing for order.paid, payment.captured, and payment.failed.
    """
    raw_body = await request.body()
    signature = x_razorpay_signature or request.headers.get("x-razorpay-signature", "")

    if not signature and not is_mock_mode():
        logger.error("Missing X-Razorpay-Signature header on webhook request")
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature header")

    result = process_razorpay_webhook(db=db, raw_body=raw_body, signature=signature)
    return result


@router.post("/{order_id}/failed")
async def report_payment_failed(
    order_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record payment failure or cancellation triggered from the client Razorpay modal.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    rzp_order_id = payload.get("razorpay_order_id")
    rzp_payment_id = payload.get("razorpay_payment_id")
    error_description = payload.get("error_description", "Payment was cancelled or failed by user")
    method = payload.get("method")

    handle_payment_failure(
        db=db,
        order=order,
        razorpay_order_id=rzp_order_id,
        razorpay_payment_id=rzp_payment_id,
        error_description=error_description,
        method=method
    )

    return {
        "status": "failure_recorded",
        "order_id": order.id,
        "payment_status": order.payment_status
    }


@router.get("/config")
async def payment_config():
    """
    Provide public, non-secret client configuration for Razorpay checkout.
    Secret keys and webhook secrets are NEVER exposed here.
    """
    return {
        "key_id": settings.RAZORPAY_KEY_ID,
        "currency": "INR",
        "company_name": settings.APP_NAME,
        "is_test_mode": settings.RAZORPAY_KEY_ID.startswith("rzp_test_"),
        "is_mock_mode": is_mock_mode()
    }
