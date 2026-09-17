# 🪷 Suyog Collection — Real-Time Indian Clothing E-Commerce Website

An authentic, production-grade Indian ethnic wear e-commerce platform built with **FastAPI**, **SQLAlchemy**, **Jinja2**, and **Razorpay**. Inspired by modern premium Indian fashion shopping experiences with rich multi-filter cataloging, color/size variants, cart, wishlists, dynamic checkout, order tracking, and admin dashboard.

---

## ✨ Features

- 👗 **Rich Indian Clothing Catalog**: Sarees (Banarasi, Kanjivaram, Chanderi, Organza), Kurtis, Lehengas, Salwar Suits, and Men's Ethnic Wear.
- 🔍 **Real-Time Search & Autocomplete**: Instant search suggestions for categories, fabrics, and names.
- 🏷️ **Multi-Faceted Filtering & Sorting**: Filter by price range, color swatches, fabrics (Silk, Cotton, Georgette, etc.), and occasions (Wedding, Party, Festive).
- 🖼️ **Interactive Product Detail**: Multi-angle gallery zoom, real-time stock indicator, color and size selectors, customer reviews, and intelligent recommendations.
- 🛒 **Cart & Wishlist Engine**: Dynamic server-backed cart with guest session support and customer wishlist synchronization.
- 🎟️ **Coupon & Promotion Engine**: Percentage and fixed discount codes (e.g. `WELCOME10`, `FESTIVE20`, `SAVE70`, `FLAT500`).
- 💳 **Checkout & Payment**: Integrated with **Razorpay** checkout and **Cash on Delivery (COD)** fallback with address management.
- 📍 **Live Order Lifecycle Tracking**: Visual milestone tracker (Pending ➔ Confirmed ➔ Processing ➔ Shipped ➔ Delivered).
- 📊 **Comprehensive Admin Panel**: Real-time sales metrics, revenue analytics, catalog CRUD, and instant order status dispatch management.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2
- **Database / ORM**: PostgreSQL (production) / SQLite (development zero-config fallback), SQLAlchemy 2.0
- **Templating & Static**: Jinja2, Vanilla CSS3 (Custom Luxury Design System), Vanilla JS
- **Security**: Passlib (Bcrypt), PyJWT (JSON Web Tokens), Secure HTTP-only cookies
- **Payments**: Razorpay Python SDK

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- Virtual environment tool

### 2. Clone & Install Dependencies
```bash
git clone <repo-url>
cd vastravibe
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

*(By default, `DATABASE_URL` is configured to use `sqlite:///./vastravibe.db` for instant local execution without needing PostgreSQL)*

### 4. Seed the Database
Populate authentic sample products, categories, coupons, and test users:
```bash
python scripts/seed_products.py
```

### 5. Run the Server
```bash
python run.py
``` 
Open your browser and navigate to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 Demo Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin User** | `admin@vastravibe.com` | `admin123` |
| **Sample Customer** | `customer@example.com` | `customer123` |

---

## 🧪 Running Tests

Execute the automated test suite:
```bash
pytest
```

---

## 📂 Project Structure

```
vastravibe/
├── app/
│   ├── config.py              # Configuration & environment settings
│   ├── database.py            # Database engine and session management
│   ├── main.py                # FastAPI entry point & middleware
│   ├── models/                # SQLAlchemy database entities
│   ├── schemas/               # Pydantic validation schemas
│   ├── services/              # Business logic (Auth, Product, Cart, Order, Payment)
│   ├── routers/               # API & Page route handlers
│   ├── utils/                 # Security, JWT, helpers, image uploads
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS, JS, and media assets
├── scripts/
│   └── seed_products.py       # Comprehensive sample data seeder
├── tests/                     # Pytest automated test suites
├── requirements.txt           # Python package dependencies
├── Procfile                   # Deployment entry point
└── run.py                     # Development server runner
```
