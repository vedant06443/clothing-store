from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.address import Address
from app.models.coupon import Coupon, CouponUsage
from app.services.cart_service import get_cart, clear_cart
from app.utils.helpers import generate_order_number
from datetime import datetime, timezone


def apply_coupon(db: Session, code: str, user_id: int, order_amount: float) -> dict:
    """Validate and apply a coupon code."""
    coupon = db.query(Coupon).filter(
        Coupon.code == code.upper(),
        Coupon.is_active == True
    ).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="Invalid coupon code")

    now = datetime.now(timezone.utc)
    if coupon.valid_until and coupon.valid_until < now:
        raise HTTPException(status_code=400, detail="This coupon has expired")

    if order_amount < coupon.minimum_order:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order amount ₹{coupon.minimum_order:.0f} required for this coupon"
        )

    if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    # Check if user already used this coupon
    used = db.query(CouponUsage).filter(
        CouponUsage.coupon_id == coupon.id,
        CouponUsage.user_id == user_id
    ).first()
    if used:
        raise HTTPException(status_code=400, detail="You've already used this coupon")

    # Calculate discount
    if coupon.discount_type == "percent":
        discount = (order_amount * coupon.discount_value) / 100
        if coupon.maximum_discount:
            discount = min(discount, coupon.maximum_discount)
    else:
        discount = coupon.discount_value

    return {
        "coupon_id": coupon.id,
        "code": coupon.code,
        "discount": round(discount, 2),
        "description": coupon.description
    }


def create_order(
    db: Session,
    user_id: int,
    address_id: int,
    payment_method: str = "Online",
    coupon_code: Optional[str] = None
) -> Order:
    """Create order from cart items."""
    cart = get_cart(db, user_id)
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id
    ).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    subtotal = cart["subtotal"]
    shipping = cart["shipping"]
    discount = 0
    coupon_id = None

    # Apply coupon
    if coupon_code:
        coupon_result = apply_coupon(db, coupon_code, user_id, subtotal)
        discount = coupon_result["discount"]
        coupon_id = coupon_result["coupon_id"]

    total = max(subtotal + shipping - discount, 0)

    # Validate stock for all items
    for item in cart["items"]:
        product = item.product
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"'{product.name}' has only {product.stock} items left in stock"
            )

    # Create order
    order = Order(
        order_number=generate_order_number(),
        user_id=user_id,
        address_id=address_id,
        subtotal=subtotal,
        discount_amount=discount,
        shipping_amount=shipping,
        total_amount=total,
        coupon_code=coupon_code.upper() if coupon_code else None,
        payment_method=payment_method,
        payment_status=PaymentStatus.COD if payment_method == "COD" else PaymentStatus.PENDING,
        status=OrderStatus.CONFIRMED if payment_method == "COD" else OrderStatus.PENDING,
        shipping_name=address.full_name,
        shipping_phone=address.phone,
        shipping_address=f"{address.address_line1}, {address.address_line2 or ''}".strip(", "),
        shipping_city=address.city,
        shipping_state=address.state,
        shipping_pincode=address.pincode
    )
    db.add(order)
    db.flush()

    # Create order items and reduce stock
    for item in cart["items"]:
        product = item.product
        price = product.discount_price if product.discount_price else product.price
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            color=item.color,
            size=item.size,
            price=price,
            total=price * item.quantity,
            product_name=product.name,
            product_image=product.primary_image
        )
        db.add(order_item)
        # Reduce stock
        product.stock -= item.quantity
        product.sales_count += item.quantity

    # Track coupon usage
    if coupon_id:
        usage = CouponUsage(coupon_id=coupon_id, user_id=user_id, order_id=order.id)
        db.add(usage)
        db.query(Coupon).filter(Coupon.id == coupon_id).update(
            {"usage_count": Coupon.usage_count + 1}
        )

    db.commit()
    db.refresh(order)
    clear_cart(db, user_id)
    return order


def get_user_orders(db: Session, user_id: int):
    return db.query(Order).options(
        joinedload(Order.items)
    ).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


def get_order(db: Session, order_id: int, user_id: int) -> Order:
    order = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def admin_get_all_orders(db: Session, status: Optional[str] = None, page: int = 1, per_page: int = 20):
    query = db.query(Order).options(joinedload(Order.user), joinedload(Order.items))
    if status:
        query = query.filter(Order.status == status)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    return orders, total


def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = new_status
    if new_status == OrderStatus.DELIVERED:
        order.payment_status = PaymentStatus.PAID
        order.delivered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order
