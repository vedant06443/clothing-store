from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.cart import OrderCreate, CouponApply
from app.services.order_service import (
    create_order, get_user_orders, get_order, apply_coupon
)
from app.services.payment_service import create_razorpay_order
from app.utils.dependencies import get_current_user, get_current_user_optional
from app.config import settings

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/")
async def place_order(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = create_order(db, user.id, data.address_id, data.payment_method, data.coupon_code)

    result = {
        "message": "Order placed successfully",
        "order_id": order.id,
        "order_number": order.order_number,
        "total": order.total_amount,
        "payment_method": order.payment_method,
        "status": order.status
    }

    # If online payment, create Razorpay order
    if data.payment_method == "Online":
        rzp_order = create_razorpay_order(order.total_amount, order.id)
        order.razorpay_order_id = rzp_order.get("id", "")
        db.commit()
        result["razorpay_order_id"] = rzp_order.get("id", "")
        result["razorpay_key"] = settings.RAZORPAY_KEY_ID
        result["demo_mode"] = rzp_order.get("demo_mode", False)

    return result


@router.get("/")
async def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = get_user_orders(db, user.id)
    return {
        "orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "total_amount": o.total_amount,
                "status": o.status,
                "payment_status": o.payment_status,
                "payment_method": o.payment_method,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "item_count": sum(i.quantity for i in o.items)
            }
            for o in orders
        ]
    }


@router.get("/{order_id}")
async def order_detail(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = get_order(db, order_id, user.id)
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "shipping_amount": order.shipping_amount,
        "total_amount": order.total_amount,
        "coupon_code": order.coupon_code,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "shipping_name": order.shipping_name,
        "shipping_phone": order.shipping_phone,
        "shipping_address": order.shipping_address,
        "shipping_city": order.shipping_city,
        "shipping_state": order.shipping_state,
        "shipping_pincode": order.shipping_pincode,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_image": item.product_image,
                "quantity": item.quantity,
                "price": item.price,
                "total": item.total,
                "color": item.color,
                "size": item.size,
            }
            for item in order.items
        ]
    }


@router.post("/coupon/apply")
async def validate_coupon(
    data: CouponApply,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id = user.id if user else None
    result = apply_coupon(db, data.code, user_id, data.order_amount)
    return result


@router.post("/{order_id}/payment/verify")
async def verify_payment(
    order_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.payment_service import confirm_payment
    order = confirm_payment(
        db,
        order_id,
        payload.get("razorpay_order_id", ""),
        payload.get("razorpay_payment_id", ""),
        payload.get("razorpay_signature", "")
    )
    return {
        "message": "Payment confirmed",
        "order_number": order.order_number,
        "status": order.status
    }
