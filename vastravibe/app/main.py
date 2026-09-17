import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import create_tables

# Import all routers
from app.routers import auth, products, cart, wishlist, addresses, orders, reviews, admin, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and run startup tasks."""
    create_tables()
    # Ensure static directories exist
    Path("app/static/uploads/products").mkdir(parents=True, exist_ok=True)
    Path("app/static/uploads/categories").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Suyog Collection API",
    description="Indian Clothing E-Commerce Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# ──────────────── Middleware ────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────── Static Files ────────────────

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ──────────────── Register Routers ────────────────

# API routes first
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(wishlist.router)
app.include_router(addresses.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(admin.router)

# HTML page routes last
app.include_router(pages.router)


# ──────────────── Error Handlers ────────────────

templates = Jinja2Templates(directory="app/templates")


def _error_context(request: Request):
    return {
        "request": request,
        "site_name": "Suyog Collection",
        "cart_count": 0,
        "wishlist_count": 0,
        "user": None,
        "categories": [],
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="errors/404.html",
        context=_error_context(request),
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="errors/500.html",
        context=_error_context(request),
        status_code=500
    )
