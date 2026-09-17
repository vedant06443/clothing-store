from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.product_service import (
    get_products, get_product_by_slug, get_recommendations, search_suggestions
)
from app.models.category import Category

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/")
async def list_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    colors: Optional[str] = Query(None),
    fabrics: Optional[str] = Query(None),
    occasions: Optional[str] = Query(None),
    sizes: Optional[str] = Query(None),
    sort_by: str = Query("featured"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, le=100),
    featured: Optional[bool] = Query(None),
    bestseller: Optional[bool] = Query(None),
    new_arrival: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    color_list = colors.split(",") if colors else None
    fabric_list = fabrics.split(",") if fabrics else None
    occasion_list = occasions.split(",") if occasions else None
    size_list = sizes.split(",") if sizes else None

    products, total = get_products(
        db=db,
        category_slug=category,
        search=search,
        min_price=min_price,
        max_price=max_price,
        colors=color_list,
        fabrics=fabric_list,
        occasions=occasion_list,
        sizes=size_list,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
        is_featured=featured,
        is_bestseller=bestseller,
        is_new_arrival=new_arrival,
    )

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "brand": p.brand,
                "price": p.price,
                "discount_price": p.discount_price,
                "discount_percent": p.discount_percent,
                "rating": p.rating,
                "review_count": p.review_count,
                "stock": p.stock,
                "primary_image": p.primary_image,
                "is_featured": p.is_featured,
                "is_bestseller": p.is_bestseller,
                "is_new_arrival": p.is_new_arrival,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/search/suggestions")
async def get_suggestions(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    suggestions = search_suggestions(db, q)
    return {"suggestions": suggestions}


@router.get("/pincode/check")
async def check_pincode(pincode: str = Query(..., min_length=6, max_length=6)):
    from app.services.pincode_service import check_pincode_delivery
    return check_pincode_delivery(pincode)


@router.get("/{slug}")
async def get_product(slug: str, db: Session = Depends(get_db)):
    product = get_product_by_slug(db, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    recommendations = get_recommendations(db, product)

    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "brand": product.brand,
            "description": product.description,
            "specifications": product.specifications,
            "price": product.price,
            "discount_price": product.discount_price,
            "discount_percent": product.discount_percent,
            "fabric": product.fabric,
            "occasion": product.occasion,
            "colors": product.colors,
            "sizes": product.sizes,
            "care_instructions": product.care_instructions,
            "stock": product.stock,
            "rating": product.rating,
            "review_count": product.review_count,
            "images": [{"url": img.image_url, "is_primary": img.is_primary} for img in product.images],
            "variants": [{"color": v.color, "size": v.size, "stock": v.stock} for v in product.variants],
        },
        "recommendations": [
            {"id": r.id, "name": r.name, "slug": r.slug, "price": r.price,
             "discount_price": r.discount_price, "primary_image": r.primary_image}
            for r in recommendations
        ]
    }
