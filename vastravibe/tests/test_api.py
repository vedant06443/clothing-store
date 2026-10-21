from app.models import User, Category, Product, ProductImage, Coupon, Address
from app.utils.security import hash_password, create_access_token


def test_homepage(client):
    """Test homepage loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Suyog" in response.text


def test_register_and_login(client):
    """Test user registration and authentication flow."""
    reg_data = {
        "full_name": "Ananya Roy",
        "email": "tester@example.com",
        "phone": "9876543210",
        "password": "strongpassword123",
        "confirm_password": "strongpassword123"
    }
    # Register via API
    res = client.post("/api/auth/register", json=reg_data)
    assert res.status_code == 200
    json_data = res.json()
    assert "token" in json_data

    # Login via API
    login_res = client.post("/api/auth/login", json={
        "email": "tester@example.com",
        "password": "strongpassword123"
    })
    assert login_res.status_code == 200
    assert "Login successful" in login_res.json()["message"]


def test_category_and_product_listing(client, db_session):
    """Test category creation and product querying."""
    category = Category(
        name="Silk Sarees",
        slug="silk-sarees",
        description="Traditional Silk Sarees",
        sort_order=1
    )
    db_session.add(category)
    db_session.commit()

    product = Product(
        category_id=category.id,
        name="Zari Banarasi Silk Saree",
        slug="zari-banarasi-silk-saree",
        brand="VastraVibe",
        sku="TEST-SKU-001",
        price=5999.0,
        discount_price=2999.0,
        stock=15,
        fabric="Silk"
    )
    db_session.add(product)
    db_session.commit()

    image = ProductImage(
        product_id=product.id,
        image_url="https://example.com/saree.jpg",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image)
    db_session.commit()

    # Query products endpoint
    res = client.get("/api/products/")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["products"][0]["name"] == "Zari Banarasi Silk Saree"

    # Query product detail by slug
    detail_res = client.get(f"/product/{product.slug}")
    assert detail_res.status_code == 200
    assert "Zari Banarasi Silk Saree" in detail_res.text


def test_cart_operations(client, db_session):
    """Test adding items to cart with user authentication."""
    user = User(
        full_name="Pooja Sharma",
        email="pooja@example.com",
        phone="9876501234",
        hashed_password=hash_password("password123"),
        is_active=True
    )
    db_session.add(user)

    category = Category(name="Kurtis", slug="kurtis-test")
    db_session.add(category)
    db_session.commit()

    product = Product(
        category_id=category.id,
        name="Chikankari Cotton Kurti",
        slug="chikankari-cotton-kurti",
        brand="VastraVibe",
        sku="TEST-KUR-001",
        price=1999.0,
        discount_price=999.0,
        stock=20
    )
    db_session.add(product)
    db_session.commit()

    image = ProductImage(
        product_id=product.id,
        image_url="https://example.com/kurti.jpg",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image)
    db_session.commit()

    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Add to cart
    res = client.post("/api/cart/add", json={
        "product_id": product.id,
        "quantity": 2,
        "color": "White",
        "size": "M"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["cart_count"] == 2

    # View cart API
    cart_res = client.get("/api/cart/", headers=headers)
    assert cart_res.status_code == 200
    cart_data = cart_res.json()
    assert cart_data["item_count"] == 2
    assert cart_data["subtotal"] == 1998.0


def test_coupon_validation(client, db_session):
    """Test coupon validation and discount calculation."""
    coupon = Coupon(
        code="TESTDISC10",
        discount_type="percent",
        discount_value=10.0,
        minimum_order=500.0,
        maximum_discount=200.0,
        is_active=True
    )
    db_session.add(coupon)
    db_session.commit()

    res = client.post("/api/orders/coupon/apply", json={
        "code": "TESTDISC10",
        "order_amount": 1000.0
    })
    assert res.status_code == 200
    assert res.json()["discount"] == 100.0


def test_search_suggestions(client, db_session):
    """Test search suggestion API."""
    category = Category(name="Lehengas", slug="lehengas-test")
    db_session.add(category)
    db_session.commit()

    product = Product(
        category_id=category.id,
        name="Royal Maroon Velvet Lehenga",
        slug="royal-maroon-velvet-lehenga",
        brand="VastraVibe",
        price=15000.0,
        stock=5
    )
    db_session.add(product)
    db_session.commit()

    res = client.get("/api/products/search/suggestions?q=Maroon")
    assert res.status_code == 200
    suggestions = res.json()["suggestions"]
    assert any("Maroon" in s for s in suggestions)


def test_phone_normalization_and_registration(client):
    """Test registration accepts 0-prefixed, +91-prefixed, and standard phone numbers."""
    from app.schemas.user import UserRegister
    import pytest

    # Leading 0 (the user's error case: '09405611628')
    u1 = UserRegister(
        full_name="Test User 1",
        email="test0@example.com",
        phone="09405611628",
        password="password123",
        confirm_password="password123"
    )
    assert u1.phone == "9405611628"

    # +91 with spaces
    u2 = UserRegister(
        full_name="Test User 2",
        email="test91@example.com",
        phone="+91 94056 11628",
        password="password123",
        confirm_password="password123"
    )
    assert u2.phone == "9405611628"

    # None / Optional phone
    u3 = UserRegister(
        full_name="Test User 3",
        email="testopt@example.com",
        phone=None,
        password="password123",
        confirm_password="password123"
    )
    assert u3.phone is None

    # Invalid phone should still raise ValueError
    with pytest.raises(ValueError):
        UserRegister(
            full_name="Test Bad",
            email="testbad@example.com",
            phone="1234567890",
            password="password123",
            confirm_password="password123"
        )


def test_payment_config(client):
    """Test public payment configuration endpoint does not leak secrets."""
    res = client.get("/api/payments/config")
    assert res.status_code == 200
    data = res.json()
    assert "key_id" in data
    assert "currency" in data
    assert data["currency"] == "INR"
    assert "secret" not in data
    assert "RAZORPAY_KEY_SECRET" not in data
    assert "RAZORPAY_WEBHOOK_SECRET" not in data


def test_signed_webhook_and_idempotency(client, db_session):
    """Test Razorpay signed webhook processing and idempotent fulfillment."""
    import hmac
    import hashlib
    import json
    from app.models.order import Order, OrderStatus, PaymentStatus
    from app.config import settings

    # Create a test order
    test_order = Order(
        order_number="ORD-TEST-9999",
        user_id=1,
        subtotal=1999.0,
        total_amount=1999.0,
        payment_method="Online",
        payment_status=PaymentStatus.PENDING,
        status=OrderStatus.PENDING,
        razorpay_order_id="order_rzp_test_12345"
    )
    db_session.add(test_order)
    db_session.commit()
    db_session.refresh(test_order)

    # 1. Invalid signature should be rejected with 400
    fake_body = json.dumps({"event": "order.paid"}).encode("utf-8")
    res_invalid = client.post(
        "/api/payments/webhook",
        content=fake_body,
        headers={"X-Razorpay-Signature": "invalid_signature", "Content-Type": "application/json"}
    )
    assert res_invalid.status_code == 400

    # 2. Valid signed webhook for order.paid
    secret = settings.RAZORPAY_WEBHOOK_SECRET or "mock_webhook_secret_12345"
    webhook_payload = {
        "event": "order.paid",
        "payload": {
            "order": {
                "entity": {
                    "id": "order_rzp_test_12345",
                    "amount": 199900,
                    "status": "paid",
                    "notes": {"order_id": str(test_order.id)}
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_987654",
                    "order_id": "order_rzp_test_12345",
                    "amount": 199900,
                    "status": "captured",
                    "method": "upi"
                }
            }
        }
    }
    body_bytes = json.dumps(webhook_payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    res_valid = client.post(
        "/api/payments/webhook",
        content=body_bytes,
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "success"

    # Verify order is marked PAID
    db_session.refresh(test_order)
    assert test_order.payment_status == PaymentStatus.PAID
    assert test_order.status == OrderStatus.CONFIRMED

    # 3. Idempotent Retry: Send the same webhook again
    res_retry = client.post(
        "/api/payments/webhook",
        content=body_bytes,
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
    )
    assert res_retry.status_code == 200
    # Order remains PAID without errors
    db_session.refresh(test_order)
    assert test_order.payment_status == PaymentStatus.PAID
