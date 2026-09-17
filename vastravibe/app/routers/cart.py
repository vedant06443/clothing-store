from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.cart import CartItem
from app.schemas.cart import CartItemAdd, CartItemUpdate
from app.services.cart_service import (
    get_cart, add_to_cart, update_cart_item, remove_from_cart, get_cart_count
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.get("/")
async def view_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_cart(db, user.id)
    return {
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "product_image": item.product.primary_image,
                "product_price": item.product.price,
                "product_discount_price": item.product.discount_price,
                "quantity": item.quantity,
                "color": item.color,
                "size": item.size,
                "item_total": (item.product.discount_price or item.product.price) * item.quantity
            }
            for item in cart["items"]
        ],
        "subtotal": cart["subtotal"],
        "discount": cart["discount"],
        "shipping": cart["shipping"],
        "total": cart["total"],
        "item_count": cart["item_count"]
    }


@router.get("/count")
async def cart_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"count": get_cart_count(db, user.id)}


@router.post("/add")
async def add_item(data: CartItemAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    add_to_cart(db, user.id, data.product_id, data.quantity, data.color, data.size)
    count = get_cart_count(db, user.id)
    return {"message": "Added to cart", "cart_count": count}


@router.put("/item/{item_id}")
async def update_item(item_id: int, data: CartItemUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    update_cart_item(db, user.id, item_id, data.quantity)
    cart = get_cart(db, user.id)
    return {"message": "Cart updated", "total": cart["total"], "item_count": cart["item_count"]}


@router.delete("/item/{item_id}")
async def remove_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    remove_from_cart(db, user.id, item_id)
    cart = get_cart(db, user.id)
    return {"message": "Item removed", "total": cart["total"], "item_count": cart["item_count"]}
