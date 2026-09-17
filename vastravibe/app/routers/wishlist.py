from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.user import User
from app.models.wishlist import WishlistItem
from app.models.product import Product
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("/")
async def get_wishlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(WishlistItem).options(
        joinedload(WishlistItem.product).joinedload(Product.images)
    ).filter(WishlistItem.user_id == user.id).all()

    return {
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "product_slug": item.product.slug,
                "product_image": item.product.primary_image,
                "price": item.product.price,
                "discount_price": item.product.discount_price,
                "stock": item.product.stock
            }
            for item in items
        ],
        "count": len(items)
    }


@router.post("/toggle/{product_id}")
async def toggle_wishlist(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(WishlistItem).filter(
        WishlistItem.user_id == user.id,
        WishlistItem.product_id == product_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Removed from wishlist", "in_wishlist": False}

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    item = WishlistItem(user_id=user.id, product_id=product_id)
    db.add(item)
    db.commit()
    return {"message": "Added to wishlist", "in_wishlist": True}


@router.get("/check/{product_id}")
async def check_wishlist(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exists = db.query(WishlistItem).filter(
        WishlistItem.user_id == user.id,
        WishlistItem.product_id == product_id
    ).first()
    return {"in_wishlist": bool(exists)}
