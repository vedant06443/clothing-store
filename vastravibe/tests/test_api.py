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
