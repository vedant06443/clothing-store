from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PROCESSING = "Processing"
    PACKED = "Packed"
    SHIPPED = "Shipped"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    RETURNED = "Returned"


class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"
    COD = "COD"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)

    # Pricing
    subtotal = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0)
    shipping_amount = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)

    # Coupon
    coupon_code = Column(String(50), nullable=True)

    # Payment
    payment_method = Column(String(50), default="Online")  # Online, COD
    payment_status = Column(String(30), default=PaymentStatus.PENDING)
    razorpay_order_id = Column(String(100), nullable=True)

    # Status
    status = Column(String(30), default=OrderStatus.PENDING)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Snapshot of address at time of order
    shipping_name = Column(String(100), nullable=True)
    shipping_phone = Column(String(15), nullable=True)
    shipping_address = Column(Text, nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_pincode = Column(String(10), nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    address = relationship("Address", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    color = Column(String(50), nullable=True)
    size = Column(String(20), nullable=True)
    price = Column(Float, nullable=False)       # price at time of order
    total = Column(Float, nullable=False)

    # Product snapshot
    product_name = Column(String(200), nullable=True)
    product_image = Column(String(500), nullable=True)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    review = relationship("Review", back_populates="order_item", uselist=False)
