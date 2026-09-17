from sqlalchemy import Column, Integer, String, Boolean, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(220), nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    brand = Column(String(100), default="Suyog Collection")
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    specifications = Column(Text, nullable=True)

    # Pricing
    price = Column(Float, nullable=False)               # original price
    discount_price = Column(Float, nullable=True)       # discounted price
    discount_percent = Column(Integer, default=0)

    # Attributes
    fabric = Column(String(100), nullable=True)
    occasion = Column(String(100), nullable=True)
    colors = Column(String(300), nullable=True)         # comma-separated
    sizes = Column(String(100), nullable=True)          # comma-separated
    care_instructions = Column(Text, nullable=True)

    # Flags
    is_featured = Column(Boolean, default=False)
    is_bestseller = Column(Boolean, default=False)
    is_new_arrival = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Stats
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    @property
    def primary_image(self) -> str:
        from app.utils.helpers import get_image_url
        if self.images:
            for img in self.images:
                if img.is_primary and img.image_url and str(img.image_url).strip():
                    return img.display_url
            for img in self.images:
                if img.image_url and str(img.image_url).strip():
                    return img.display_url
        return get_image_url(None)

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price
