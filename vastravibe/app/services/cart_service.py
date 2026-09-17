from typing import List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.cart import CartItem
from app.models.product import Product


def get_cart(db: Session, user_id: int) -> Dict[str, Any]:
    """Get cart items with totals for a user."""
    items = db.query(CartItem).options(
        joinedload(CartItem.product).joinedload(Product.images)
    ).filter(CartItem.user_id == user_id).all()

    subtotal = 0
    discount = 0
    for item in items:
        p = item.product
        item_price = p.discount_price if p.discount_price else p.price
        item_total = item_price * item.quantity
        subtotal += item_total
        if p.discount_price:
            discount += (p.price - p.discount_price) * item.quantity

    if not items or subtotal == 0:
        shipping = 0
        total = 0
    else:
        shipping = 0 if subtotal >= 999 else 99
        total = subtotal + shipping

    return {
        "items": items,
        "cart_items": items,
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "total": total,
        "item_count": sum(i.quantity for i in items)
    }


def add_to_cart(db: Session, user_id: int, product_id: int,
                quantity: int = 1, color: str = None, size: str = None) -> CartItem:
    """Add product to cart or update quantity if already exists."""
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < quantity:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} items in stock")

    existing = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id,
        CartItem.color == color,
        CartItem.size == size
    ).first()

    if existing:
        new_qty = existing.quantity + quantity
        if product.stock < new_qty:
            raise HTTPException(status_code=400, detail=f"Only {product.stock} items in stock")
        existing.quantity = new_qty
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        color=color,
        size=size
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item(db: Session, user_id: int, item_id: int, quantity: int) -> CartItem:
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if quantity <= 0:
        db.delete(item)
        db.commit()
        return None
    if item.product.stock < quantity:
        raise HTTPException(status_code=400, detail=f"Only {item.product.stock} items available")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


def remove_from_cart(db: Session, user_id: int, item_id: int):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


def clear_cart(db: Session, user_id: int):
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()


def get_cart_count(db: Session, user_id: int) -> int:
    result = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    return sum(i.quantity for i in result)
