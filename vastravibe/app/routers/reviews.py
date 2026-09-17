from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.user import User
from app.models.review import Review
from app.models.order import OrderItem
from app.schemas.cart import ReviewCreate
from app.services.product_service import update_product_rating
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("/")
async def add_review(
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user already reviewed this product
    existing = db.query(Review).filter(
        Review.user_id == user.id,
        Review.product_id == data.product_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You've already reviewed this product")

    # Check if user purchased this product
    purchased = db.query(OrderItem).join(OrderItem.order).filter(
        OrderItem.product_id == data.product_id,
        OrderItem.order.has(user_id=user.id)
    ).first()

    review = Review(
        user_id=user.id,
        product_id=data.product_id,
        order_item_id=data.order_item_id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        image_url=data.image_url,
        is_verified=bool(purchased),
        is_approved=True
    )
    db.add(review)
    db.commit()

    # Update product rating
    update_product_rating(db, data.product_id)

    return {"message": "Review submitted successfully"}


@router.get("/product/{product_id}")
async def get_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).options(
        joinedload(Review.user)
    ).filter(
        Review.product_id == product_id,
        Review.is_approved == True
    ).order_by(Review.created_at.desc()).all()

    return {
        "reviews": [
            {
                "id": r.id,
                "user_name": r.user.full_name,
                "rating": r.rating,
                "title": r.title,
                "body": r.body,
                "is_verified": r.is_verified,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "image_url": r.image_url
            }
            for r in reviews
        ],
        "count": len(reviews)
    }
