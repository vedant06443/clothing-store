from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.category import Category


def get_products(
    db: Session,
    category_slug: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    colors: Optional[List[str]] = None,
    fabrics: Optional[List[str]] = None,
    occasions: Optional[List[str]] = None,
    sizes: Optional[List[str]] = None,
    sort_by: str = "featured",
    page: int = 1,
    per_page: int = 24,
    is_featured: Optional[bool] = None,
    is_bestseller: Optional[bool] = None,
    is_new_arrival: Optional[bool] = None,
) -> Tuple[List[Product], int]:
    """Get filtered, sorted, and paginated products."""
    query = db.query(Product).options(
        joinedload(Product.images),
        joinedload(Product.category)
    ).filter(Product.is_active == True)

    # Category filter
    if category_slug:
        if category_slug in ["gents", "mens-wear", "men"]:
            query = query.join(Category).filter(Category.slug.in_(["gents", "mens-wear", "men"]))
        else:
            query = query.join(Category).filter(Category.slug == category_slug)

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.fabric.ilike(search_term),
                Product.occasion.ilike(search_term),
                Product.brand.ilike(search_term),
            )
        )

    # Price filters
    if min_price is not None:
        query = query.filter(
            or_(
                and_(Product.discount_price != None, Product.discount_price >= min_price),
                and_(Product.discount_price == None, Product.price >= min_price)
            )
        )
    if max_price is not None:
        query = query.filter(
            or_(
                and_(Product.discount_price != None, Product.discount_price <= max_price),
                and_(Product.discount_price == None, Product.price <= max_price)
            )
        )

    # Color filter
    if colors:
        color_filters = [Product.colors.ilike(f"%{c}%") for c in colors]
        query = query.filter(or_(*color_filters))

    # Fabric filter
    if fabrics:
        fabric_filters = [Product.fabric.ilike(f"%{f}%") for f in fabrics]
        query = query.filter(or_(*fabric_filters))

    # Occasion filter
    if occasions:
        occ_filters = [Product.occasion.ilike(f"%{o}%") for o in occasions]
        query = query.filter(or_(*occ_filters))

    # Size filter
    if sizes:
        size_filters = [Product.sizes.ilike(f"%{s}%") for s in sizes]
        query = query.filter(or_(*size_filters))

    # Flags
    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)
    if is_bestseller is not None:
        query = query.filter(Product.is_bestseller == is_bestseller)
    if is_new_arrival is not None:
        query = query.filter(Product.is_new_arrival == is_new_arrival)

    # Sorting
    sort_map = {
        "featured": Product.is_featured.desc(),
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
        "bestselling": Product.sales_count.desc(),
        "discount": Product.discount_percent.desc(),
    }
    sort_col = sort_map.get(sort_by, Product.is_featured.desc())
    query = query.order_by(sort_col)

    total = query.count()
    products = query.offset((page - 1) * per_page).limit(per_page).all()
    return products, total


def get_product_by_slug(db: Session, slug: str) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.images),
        joinedload(Product.variants),
        joinedload(Product.reviews),
        joinedload(Product.category)
    ).filter(Product.slug == slug, Product.is_active == True).first()


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.images),
        joinedload(Product.variants),
    ).filter(Product.id == product_id, Product.is_active == True).first()


def get_recommendations(db: Session, product: Product, limit: int = 8) -> List[Product]:
    """Get related products by category and fabric."""
    return db.query(Product).options(
        joinedload(Product.images)
    ).filter(
        Product.is_active == True,
        Product.id != product.id,
        or_(
            Product.category_id == product.category_id,
            Product.fabric == product.fabric,
            Product.occasion == product.occasion
        )
    ).order_by(Product.rating.desc()).limit(limit).all()


def search_suggestions(db: Session, query: str, limit: int = 8) -> List[str]:
    """Return product name suggestions for autocomplete."""
    results = db.query(Product.name).filter(
        Product.name.ilike(f"%{query}%"),
        Product.is_active == True
    ).limit(limit).all()
    return [r[0] for r in results]


def update_product_rating(db: Session, product_id: int):
    """Recalculate and update product rating from reviews."""
    from app.models.review import Review
    result = db.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(
        Review.product_id == product_id,
        Review.is_approved == True
    ).first()
    avg_rating = round(float(result[0] or 0), 1)
    count = result[1] or 0
    db.query(Product).filter(Product.id == product_id).update({
        "rating": avg_rating,
        "review_count": count
    })
    db.commit()
