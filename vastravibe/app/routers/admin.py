from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File, Query, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.category import Category
from app.models.order import Order, OrderStatus
from app.models.coupon import Coupon
from app.models.review import Review
from app.models.banner import Banner
from app.models.notification import Notification
from app.services.order_service import admin_get_all_orders, update_order_status
from app.services.notification_service import notification_manager
from app.utils.dependencies import get_current_admin
from app.utils.image_upload import upload_to_cloudinary, save_product_image, delete_product_image_file
from app.utils.helpers import slugify, calculate_discount
from app.utils.security import decode_token
import json

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ──────────────── Dashboard ────────────────

@router.get("/dashboard/stats")
async def dashboard_stats(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_orders = db.query(Order).count()
    total_customers = db.query(User).filter(User.is_admin == False).count()
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.payment_status == "Paid"
    ).scalar() or 0
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    low_stock = db.query(Product).filter(Product.stock < 10, Product.stock > 0, Product.is_active == True).count()
    out_of_stock = db.query(Product).filter(Product.stock == 0, Product.is_active == True).count()

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_revenue": round(total_revenue, 2),
        "pending_orders": pending_orders,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
    }


# ──────────────── Products ────────────────

@router.get("/products")
async def admin_products(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Product).options(joinedload(Product.images), joinedload(Product.category))
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    total = query.count()
    products = query.order_by(Product.created_at.desc()).offset((page-1)*20).limit(20).all()
    return {
        "products": [
            {
                "id": p.id, "name": p.name, "price": p.price,
                "discount_price": p.discount_price, "stock": p.stock,
                "rating": p.rating, "is_active": p.is_active,
                "category": p.category.name if p.category else None,
                "primary_image": p.primary_image
            }
            for p in products
        ],
        "total": total
    }


@router.post("/products")
@router.post("/products/")
async def create_product(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    images = []
    uploaded_image: Optional[UploadFile] = None

    if "application/json" in content_type:
        data = await request.json()
        name = data.get("name")
        category_id = data.get("category_id")
        brand = data.get("brand") or "Suyog Textile"
        description = data.get("description")
        specifications = data.get("specifications")
        price = data.get("price")
        discount_price = data.get("discount_price")
        fabric = data.get("fabric")
        occasion = data.get("occasion")
        colors = data.get("colors")
        sizes = data.get("sizes")
        care_instructions = data.get("care_instructions")
        stock = data.get("stock", 0)
        is_featured = bool(data.get("is_featured", False))
        is_bestseller = bool(data.get("is_bestseller", False))
        is_new_arrival = bool(data.get("is_new_arrival", False))
        primary_image = data.get("primary_image")
    else:
        form = await request.form()
        name = form.get("name")
        category_id = form.get("category_id")
        brand = form.get("brand") or "Suyog Textile"
        description = form.get("description")
        specifications = form.get("specifications")
        price = form.get("price")
        discount_price = form.get("discount_price")
        fabric = form.get("fabric")
        occasion = form.get("occasion")
        colors = form.get("colors")
        sizes = form.get("sizes")
        care_instructions = form.get("care_instructions")
        stock = form.get("stock", 0)
        is_featured = str(form.get("is_featured", "")).lower() in ("true", "1", "on")
        is_bestseller = str(form.get("is_bestseller", "")).lower() in ("true", "1", "on")
        is_new_arrival = str(form.get("is_new_arrival", "")).lower() in ("true", "1", "on")
        primary_image = form.get("primary_image")
        
        # Check single primary image upload
        img_field = form.get("image")
        if hasattr(img_field, "filename") and img_field.filename:
            uploaded_image = img_field
            
        images = form.getlist("images")

    if not name or not str(name).strip():
        raise HTTPException(status_code=422, detail="Product name is required")
    if category_id is None:
        raise HTTPException(status_code=422, detail="Category is required")
    try:
        category_id = int(category_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Valid category ID is required")

    if price is None:
        raise HTTPException(status_code=422, detail="Price is required")
    try:
        price = float(price)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Valid price is required")

    if discount_price not in (None, "", "null"):
        try:
            discount_price = float(discount_price)
        except (ValueError, TypeError):
            discount_price = None
    else:
        discount_price = None

    try:
        stock = int(stock or 0)
    except (ValueError, TypeError):
        stock = 0

    # If an image file was uploaded, validate and save it BEFORE creating the DB record
    final_primary_image = None
    if uploaded_image:
        final_primary_image = save_product_image(uploaded_image, product_title=str(name))
    elif primary_image and str(primary_image).strip():
        final_primary_image = str(primary_image).strip()

    slug_base = slugify(str(name))
    slug = slug_base
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{slug_base}-{counter}"
        counter += 1

    discount_percent = 0
    if discount_price and price > 0:
        discount_percent = calculate_discount(price, discount_price)

    product = Product(
        name=name, slug=slug, category_id=category_id, brand=brand,
        description=description, specifications=specifications,
        price=price, discount_price=discount_price, discount_percent=discount_percent,
        fabric=fabric, occasion=occasion, colors=colors, sizes=sizes,
        care_instructions=care_instructions, stock=stock,
        is_featured=is_featured, is_bestseller=is_bestseller, is_new_arrival=is_new_arrival
    )
    db.add(product)
    db.flush()

    # Add primary image if available
    if final_primary_image:
        db.add(ProductImage(product_id=product.id, image_url=final_primary_image, is_primary=True, sort_order=0))

    # Upload additional file images if provided
    for i, img_file in enumerate(images):
        if hasattr(img_file, "filename") and img_file.filename:
            url = upload_to_cloudinary(img_file, "products")
            is_prim = (i == 0 and not final_primary_image)
            db.add(ProductImage(product_id=product.id, image_url=url, is_primary=is_prim, sort_order=i if not final_primary_image else i + 1))

    db.commit()
    return {"message": "Product created", "product_id": product.id, "primary_image": product.primary_image}


@router.put("/products/{product_id}")
@router.post("/products/{product_id}")
async def update_product(
    product_id: int,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    content_type = request.headers.get("content-type", "")
    uploaded_image: Optional[UploadFile] = None

    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)
        img_field = form.get("image")
        if hasattr(img_field, "filename") and img_field.filename:
            uploaded_image = img_field

    if "name" in data and data["name"] is not None and str(data["name"]).strip():
        product.name = str(data["name"]).strip()
    if "category_id" in data and data["category_id"] not in (None, "", "null"):
        try:
            product.category_id = int(data["category_id"])
        except (ValueError, TypeError):
            pass
    if "brand" in data and data["brand"] is not None:
        product.brand = str(data["brand"]).strip()
    if "price" in data and data["price"] is not None:
        try:
            product.price = float(data["price"])
        except (ValueError, TypeError):
            pass
    if "discount_price" in data:
        dp = data["discount_price"]
        if dp not in (None, "", "null"):
            try:
                product.discount_price = float(dp)
                product.discount_percent = calculate_discount(product.price, product.discount_price)
            except (ValueError, TypeError):
                pass
        else:
            product.discount_price = None
            product.discount_percent = 0
    if "stock" in data and data["stock"] is not None:
        try:
            product.stock = int(data["stock"])
        except (ValueError, TypeError):
            pass
    if "fabric" in data and data["fabric"] is not None:
        product.fabric = str(data["fabric"]).strip()
    if "occasion" in data and data["occasion"] is not None:
        product.occasion = str(data["occasion"]).strip()
    if "colors" in data and data["colors"] is not None:
        product.colors = str(data["colors"]).strip()
    if "sizes" in data and data["sizes"] is not None:
        product.sizes = str(data["sizes"]).strip()
    if "care_instructions" in data and data["care_instructions"] is not None:
        product.care_instructions = str(data["care_instructions"]).strip()
    if "specifications" in data and data["specifications"] is not None:
        product.specifications = str(data["specifications"]).strip()
    if "is_featured" in data and data["is_featured"] is not None:
        product.is_featured = str(data["is_featured"]).lower() in ("true", "1", "on")
    if "is_bestseller" in data and data["is_bestseller"] is not None:
        product.is_bestseller = str(data["is_bestseller"]).lower() in ("true", "1", "on")
    if "is_new_arrival" in data and data["is_new_arrival"] is not None:
        product.is_new_arrival = str(data["is_new_arrival"]).lower() in ("true", "1", "on")
    if "is_active" in data and data["is_active"] is not None:
        product.is_active = str(data["is_active"]).lower() in ("true", "1", "on")
    if "description" in data and data["description"] is not None:
        product.description = str(data["description"]).strip()

    # Image Handling:
    # 1. If admin selected a new image file, validate & save it, update DB, and optionally delete old file
    if uploaded_image:
        new_image_url = save_product_image(uploaded_image, product_title=product.name)
        primary_img = db.query(ProductImage).filter(ProductImage.product_id == product.id, ProductImage.is_primary == True).first()
        if not primary_img:
            primary_img = db.query(ProductImage).filter(ProductImage.product_id == product.id).first()

        if primary_img:
            old_url = primary_img.image_url
            primary_img.image_url = new_image_url
            delete_product_image_file(old_url, db)
        else:
            db.add(ProductImage(product_id=product.id, image_url=new_image_url, is_primary=True, sort_order=0))

    # 2. If no new file uploaded, but admin changed the optional image URL field
    elif "primary_image" in data and data["primary_image"] is not None:
        url_val = str(data["primary_image"]).strip()
        if url_val:
            primary_img = db.query(ProductImage).filter(ProductImage.product_id == product.id, ProductImage.is_primary == True).first()
            if not primary_img:
                primary_img = db.query(ProductImage).filter(ProductImage.product_id == product.id).first()

            if primary_img:
                if primary_img.image_url != url_val:
                    old_url = primary_img.image_url
                    primary_img.image_url = url_val
                    delete_product_image_file(old_url, db)
            else:
                db.add(ProductImage(product_id=product.id, image_url=url_val, is_primary=True, sort_order=0))

    db.commit()
    db.refresh(product)
    return {"message": "Product updated", "product_id": product.id, "primary_image": product.primary_image}


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    return {"message": "Product deactivated"}


# ──────────────── Orders ────────────────

@router.get("/orders")
async def admin_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    orders, total = admin_get_all_orders(db, status, page)
    return {
        "orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer": o.user.full_name if o.user else "Unknown",
                "total": o.total_amount,
                "status": o.status,
                "payment_status": o.payment_status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
        "total": total
    }


@router.put("/orders/{order_id}/status")
async def change_order_status(
    order_id: int,
    payload: dict,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status required")
    order = update_order_status(db, order_id, new_status)
    return {"message": "Status updated", "status": order.status}


# ──────────────── Categories ────────────────

@router.get("/categories")
async def admin_categories(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    return {"categories": [{"id": c.id, "name": c.name, "slug": c.slug, "is_active": c.is_active} for c in cats]}


@router.post("/categories")
async def create_category(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    slug = slugify(name)
    image_url = None
    if image and image.filename:
        image_url = upload_to_cloudinary(image, "categories")
    cat = Category(name=name, slug=slug, description=description, image_url=image_url)
    db.add(cat)
    db.commit()
    return {"message": "Category created", "id": cat.id}


# ──────────────── Coupons ────────────────

@router.get("/coupons")
async def admin_coupons(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    coupons = db.query(Coupon).all()
    return {
        "coupons": [
            {
                "id": c.id, "code": c.code, "discount_type": c.discount_type,
                "discount_value": c.discount_value, "minimum_order": c.minimum_order,
                "usage_count": c.usage_count, "is_active": c.is_active
            }
            for c in coupons
        ]
    }


@router.post("/coupons")
async def create_coupon(payload: dict, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    coupon = Coupon(
        code=payload["code"].upper(),
        description=payload.get("description"),
        discount_type=payload.get("discount_type", "percent"),
        discount_value=payload["discount_value"],
        minimum_order=payload.get("minimum_order", 0),
        maximum_discount=payload.get("maximum_discount"),
        usage_limit=payload.get("usage_limit"),
        is_active=payload.get("is_active", True)
    )
    db.add(coupon)
    db.commit()
    return {"message": "Coupon created", "id": coupon.id}


@router.put("/coupons/{coupon_id}")
async def toggle_coupon(coupon_id: int, payload: dict, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    coupon.is_active = payload.get("is_active", coupon.is_active)
    db.commit()
    return {"message": "Coupon updated"}


# ──────────────── Reviews ────────────────

@router.get("/reviews")
async def admin_reviews(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    reviews = db.query(Review).options(joinedload(Review.user), joinedload(Review.product)).order_by(Review.created_at.desc()).limit(50).all()
    return {
        "reviews": [
            {
                "id": r.id, "user": r.user.full_name, "product": r.product.name,
                "rating": r.rating, "body": r.body, "is_approved": r.is_approved,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reviews
        ]
    }


@router.put("/reviews/{review_id}/approve")
async def approve_review(review_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_approved = not review.is_approved
    db.commit()
    from app.services.product_service import update_product_rating
    update_product_rating(db, review.product_id)
    return {"message": "Review updated", "is_approved": review.is_approved}


# ──────────────── Customers ────────────────

@router.get("/customers")
async def admin_customers(
    page: int = Query(1, ge=1),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(User).filter(User.is_admin == False)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page-1)*20).limit(20).all()
    return {
        "customers": [
            {
                "id": u.id, "name": u.full_name, "email": u.email,
                "phone": u.phone, "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ],
        "total": total
    }


# ──────────────── Notifications ────────────────

@router.get("/notifications")
async def get_admin_notifications(
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    is_read: Optional[bool] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).options(
        joinedload(Notification.order).joinedload(Order.user),
        joinedload(Notification.order).joinedload(Order.items)
    )
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    total = query.count()
    unread_count = db.query(Notification).filter(Notification.is_read == False).count()
    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for n in notifications:
        order = n.order
        if order and order.items:
            first_item = order.items[0]
            prod_name = first_item.product_name or (first_item.product.name if first_item.product else "Saree")
            qty = sum(i.quantity for i in order.items)
        else:
            prod_name = "Product"
            qty = 1

        customer_name = (order.shipping_name if order else None) or (order.user.full_name if order and order.user else "Customer")
        amount = order.total_amount if order else 0
        status = order.status if order else "Confirmed"
        payment_status = order.payment_status if order else "Paid"

        items.append({
            "id": n.id,
            "order_id": n.order_id,
            "order_number": order.order_number if order else f"ORD-{n.order_id}",
            "customer_name": customer_name,
            "product_name": prod_name,
            "quantity": qty,
            "amount": amount,
            "formatted_amount": f"₹{amount:,.0f}",
            "status": status if isinstance(status, str) else getattr(status, "value", str(status)),
            "payment_status": payment_status if isinstance(payment_status, str) else getattr(payment_status, "value", str(payment_status)),
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None
        })

    return {
        "notifications": items,
        "unread_count": unread_count,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/notifications/unread-count")
async def get_unread_notification_count(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    unread_count = db.query(Notification).filter(Notification.is_read == False).count()
    return {"unread_count": unread_count}


@router.patch("/notifications/{notification_id}/read")
@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    unread_count = db.query(Notification).filter(Notification.is_read == False).count()
    return {"success": True, "message": "Notification marked as read", "unread_count": unread_count}


@router.patch("/notifications/read-all")
@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"success": True, "message": "All notifications marked as read", "unread_count": 0}


@router.websocket("/ws/notifications")
async def admin_notifications_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.cookies.get("access_token")
    if not token:
        token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=1008)
        return

    user_id = payload.get("sub")
    user = None
    try:
        user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    except (ValueError, TypeError):
        user = db.query(User).filter(User.email == str(user_id), User.is_active == True).first()

    if not user or not user.is_admin:
        await websocket.close(code=1008)
        return

    await notification_manager.connect(websocket)
    try:
        unread_count = db.query(Notification).filter(Notification.is_read == False).count()
        await websocket.send_json({"type": "init", "unread_count": unread_count})

        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
    except Exception:
        notification_manager.disconnect(websocket)

