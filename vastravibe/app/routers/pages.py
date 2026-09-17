"""
Page router: serves all HTML pages using Jinja2 templates.
All protected pages redirect to /login if not authenticated.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.banner import Banner
from app.models.order import Order, OrderItem
from app.models.address import Address
from app.models.wishlist import WishlistItem
from app.models.newsletter import NewsletterSubscriber
from app.utils.dependencies import get_current_user_optional, get_current_user, get_current_admin
from app.services.product_service import (
    get_products, get_product_by_slug, get_recommendations, search_suggestions
)
from app.services.cart_service import get_cart, get_cart_count
from app.services.auth_service import register_user, authenticate_user, create_user_token
from app.services.order_service import get_user_orders, get_order, create_order, apply_coupon
from app.schemas.user import UserRegister
from app.config import settings
from app.utils.helpers import get_image_url

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["image_url"] = get_image_url
templates.env.globals["get_image_url"] = get_image_url


def get_template_context(request: Request, db: Session, user=None, extra: dict = None):
    """Build base context for all templates."""
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()
    cart_count = 0
    wishlist_count = 0
    if user:
        cart_count = get_cart_count(db, user.id)
        wishlist_count = db.query(WishlistItem).filter(WishlistItem.user_id == user.id).count()

    ctx = {
        "request": request,
        "user": user,
        "categories": categories,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
        "site_name": "Suyog Collection",
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }
    if extra:
        ctx.update(extra)
    return ctx


# ──────────────── Homepage ────────────────

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)

    banners = db.query(Banner).filter(Banner.is_active == True, Banner.position == "hero").order_by(Banner.sort_order).all()
    new_arrivals, _ = get_products(db, is_new_arrival=True, per_page=8)
    bestsellers, _ = get_products(db, is_bestseller=True, per_page=8)
    featured, _ = get_products(db, is_featured=True, per_page=8)
    offers, _ = get_products(db, sort_by="discount", per_page=8)

    ctx = get_template_context(request, db, user, {
        "banners": banners,
        "new_arrivals": new_arrivals,
        "bestsellers": bestsellers,
        "featured": featured,
        "offers": offers,
    })
    return templates.TemplateResponse(request=request, name="home.html", context=ctx)


# ──────────────── Product Listing ────────────────

@router.get("/products", response_class=HTMLResponse)
@router.get("/shop", response_class=HTMLResponse)
@router.get("/catalog", response_class=HTMLResponse)
async def all_products(request: Request, db: Session = Depends(get_db)):
    category = request.query_params.get("category")
    title = category.replace("-", " ").title() if category else "All Collections"
    return await collection_page(request, db, category, title)

@router.get("/sarees", response_class=HTMLResponse)
async def sarees(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "sarees", "Sarees")

@router.get("/kurtis", response_class=HTMLResponse)
async def kurtis(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "kurtis", "Kurtis")

@router.get("/lehengas", response_class=HTMLResponse)
async def lehengas(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "lehengas", "Lehengas")

@router.get("/salwar-suits", response_class=HTMLResponse)
async def salwar_suits(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "salwar-suits", "Salwar Suits")

@router.get("/dresses", response_class=HTMLResponse)
async def dresses(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "dresses", "Dresses")

@router.get("/gents", response_class=HTMLResponse)
async def gents(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "mens-wear", "Gents Collection")

@router.get("/mens-wear", response_class=HTMLResponse)
async def mens_wear(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "mens-wear", "Gents Collection")

@router.get("/men", response_class=HTMLResponse)
async def men(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, "mens-wear", "Gents Collection")

@router.get("/new-arrivals", response_class=HTMLResponse)
async def new_arrivals(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, None, "New Arrivals", is_new_arrival=True)

@router.get("/offers", response_class=HTMLResponse)
async def offers(request: Request, db: Session = Depends(get_db)):
    return await collection_page(request, db, None, "Special Offers", sort_by="discount")

@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = "", db: Session = Depends(get_db)):
    return await collection_page(request, db, None, f'Search: "{q}"', search=q)


@router.get("/studio", response_class=HTMLResponse)
async def style_studio(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    sarees, _ = get_products(db, category_slug="sarees", per_page=12)
    blouses, _ = get_products(db, category_slug="kurtis", per_page=12)
    ctx = get_template_context(request, db, user, {
        "sarees": sarees,
        "blouses": blouses
    })
    return templates.TemplateResponse(request=request, name="studio.html", context=ctx)


async def collection_page(
    request: Request, db: Session, category_slug: Optional[str], title: str,
    search: str = None, sort_by: str = "featured",
    is_featured: bool = None, is_bestseller: bool = None, is_new_arrival: bool = None
):
    user = get_current_user_optional(request, db)
    page = int(request.query_params.get("page", 1))
    sort = request.query_params.get("sort", sort_by)
    min_price = request.query_params.get("min_price")
    max_price = request.query_params.get("max_price")
    colors = request.query_params.get("colors", "").split(",") if request.query_params.get("colors") else None
    fabrics = request.query_params.get("fabrics", "").split(",") if request.query_params.get("fabrics") else None
    occasions = request.query_params.get("occasions", "").split(",") if request.query_params.get("occasions") else None
    search_q = request.query_params.get("q", search)

    products, total = get_products(
        db=db,
        category_slug=category_slug,
        search=search_q,
        min_price=float(min_price) if min_price else None,
        max_price=float(max_price) if max_price else None,
        colors=colors,
        fabrics=fabrics,
        occasions=occasions,
        sort_by=sort,
        page=page,
        per_page=24,
        is_new_arrival=is_new_arrival,
    )

    ctx = get_template_context(request, db, user, {
        "title": title,
        "category_slug": category_slug,
        "products": products,
        "total": total,
        "page": page,
        "pages": (total + 23) // 24,
        "sort": sort,
        "search_q": search_q or "",
    })
    return templates.TemplateResponse(request=request, name="products.html", context=ctx)


# ──────────────── Product Detail ────────────────

@router.get("/product/{slug}", response_class=HTMLResponse)
async def product_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    product = get_product_by_slug(db, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    recommendations = get_recommendations(db, product, limit=8)
    in_wishlist = False
    if user:
        in_wishlist = bool(db.query(WishlistItem).filter(
            WishlistItem.user_id == user.id,
            WishlistItem.product_id == product.id
        ).first())

    ctx = get_template_context(request, db, user, {
        "product": product,
        "recommendations": recommendations,
        "in_wishlist": in_wishlist,
        "colors": [c.strip() for c in (product.colors or "").split(",") if c.strip()],
        "sizes": [s.strip() for s in (product.sizes or "").split(",") if s.strip()],
    })
    return templates.TemplateResponse(request=request, name="product_detail.html", context=ctx)


# ──────────────── Auth Pages ────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/", db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)
    ctx = get_template_context(request, db, None, {"next": next})
    return templates.TemplateResponse(request=request, name="auth/login.html", context=ctx)


@router.post("/login")
async def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = "/",
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)
    if not user:
        ctx = get_template_context(request, db, None, {
            "error": "Invalid email or password",
            "email": email,
            "next": next
        })
        return templates.TemplateResponse(request=request, name="auth/login.html", context=ctx, status_code=400)

    token = create_user_token(user)
    redirect_url = next if next and not next.startswith("/login") else "/"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="auth/register.html", context=get_template_context(request, db, None))


@router.post("/register")
async def handle_register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: Optional[str] = Form(None),
    next: str = "/",
    db: Session = Depends(get_db)
):
    try:
        data = UserRegister(
            full_name=full_name,
            email=email,
            password=password,
            confirm_password=password,
            phone=phone or "9876543210"
        )
        user = register_user(db, data)
        token = create_user_token(user)
        redirect_url = next if next and not next.startswith("/register") else "/"
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        return response
    except ValueError as e:
        ctx = get_template_context(request, db, None, {
            "error": str(e),
            "full_name": full_name,
            "email": email,
            "phone": phone
        })
        return templates.TemplateResponse(request=request, name="auth/register.html", context=ctx, status_code=400)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response


# ──────────────── Cart & Checkout ────────────────

@router.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    cart = get_cart(db, user.id if user else None)
    ctx = get_template_context(request, db, user, {"cart": cart})
    return templates.TemplateResponse(request=request, name="cart.html", context=ctx)


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/checkout", status_code=302)

    cart = get_cart(db, user.id)
    if not cart["items"]:
        return RedirectResponse(url="/cart", status_code=302)

    addresses = db.query(Address).filter(Address.user_id == user.id).all()
    ctx = get_template_context(request, db, user, {
        "cart": cart,
        "addresses": addresses,
    })
    return templates.TemplateResponse(request=request, name="checkout.html", context=ctx)


# ──────────────── Account & Orders ────────────────

@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/account", status_code=302)
    addresses = db.query(Address).filter(Address.user_id == user.id).all()
    orders = get_user_orders(db, user.id)
    ctx = get_template_context(request, db, user, {
        "addresses": addresses,
        "orders": orders
    })
    return templates.TemplateResponse(request=request, name="account.html", context=ctx)


@router.get("/orders", response_class=HTMLResponse)
@router.get("/account/orders", response_class=HTMLResponse)
async def my_orders_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/orders", status_code=302)
    orders = get_user_orders(db, user.id)
    ctx = get_template_context(request, db, user, {"orders": orders})
    return templates.TemplateResponse(request=request, name="orders.html", context=ctx)


@router.get("/orders/{order_id}", response_class=HTMLResponse)
@router.get("/orders/{order_id}/track", response_class=HTMLResponse)
@router.get("/account/orders/{order_id}", response_class=HTMLResponse)
async def order_detail_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    order = get_order(db, order_id, user.id if not user.is_admin else None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    ctx = get_template_context(request, db, user, {"order": order})
    return templates.TemplateResponse(request=request, name="order_detail.html", context=ctx)


@router.get("/orders/{order_id}/invoice", response_class=HTMLResponse)
async def order_invoice_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    order = get_order(db, order_id, user.id if not user.is_admin else None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    ctx = get_template_context(request, db, user, {"order": order})
    return templates.TemplateResponse(request=request, name="invoice.html", context=ctx)


@router.get("/wishlist", response_class=HTMLResponse)
@router.get("/account/wishlist", response_class=HTMLResponse)
async def wishlist_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/account/wishlist", status_code=302)
    items = db.query(WishlistItem).options(
        joinedload(WishlistItem.product).joinedload(Product.images)
    ).filter(WishlistItem.user_id == user.id).all()
    ctx = get_template_context(request, db, user, {"wishlist_items": items})
    return templates.TemplateResponse(request=request, name="wishlist.html", context=ctx)


@router.get("/order-confirmation/{order_id}", response_class=HTMLResponse)
async def order_confirmation(order_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    order = get_order(db, order_id, user.id if not user.is_admin else None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    ctx = get_template_context(request, db, user, {"order": order})
    return templates.TemplateResponse(request=request, name="order_confirmation.html", context=ctx)


# ──────────────── Newsletter ────────────────

@router.post("/newsletter/subscribe")
async def newsletter_subscribe(email: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == email).first()
    if not existing:
        subscriber = NewsletterSubscriber(email=email)
        db.add(subscriber)
        db.commit()
    return RedirectResponse(url="/?subscribed=1", status_code=302)


# ──────────────── Admin Pages ────────────────

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login?next=/admin", status_code=302)
    
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total_amount)).filter(Order.payment_status.in_(["Paid", "PAID"])).scalar() or 0.0
    pending_orders = db.query(Order).filter(Order.status.in_(["Pending", "PENDING"])).count()
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()

    stats = {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
    }
    ctx = get_template_context(request, db, user, {
        "stats": stats,
        "recent_orders": recent_orders
    })
    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context=ctx)


@router.get("/admin/products", response_class=HTMLResponse)
async def admin_products_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login?next=/admin/products", status_code=302)
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    categories = db.query(Category).all()
    ctx = get_template_context(request, db, user, {
        "products": products,
        "total": len(products),
        "categories": categories
    })
    return templates.TemplateResponse(request=request, name="admin/products.html", context=ctx)


@router.get("/admin/products/new", response_class=HTMLResponse)
async def admin_new_product_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login?next=/admin/products/new", status_code=302)
    categories = db.query(Category).all()
    ctx = get_template_context(request, db, user, {"categories": categories})
    return templates.TemplateResponse(request=request, name="admin/product_form.html", context=ctx)


@router.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login?next=/admin/orders", status_code=302)
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    ctx = get_template_context(request, db, user, {"orders": orders})
    return templates.TemplateResponse(request=request, name="admin/orders.html", context=ctx)
