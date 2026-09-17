from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    discount_type = Column(String(20), default="percent")   # percent, fixed
    discount_value = Column(Float, nullable=False)          # percent or ₹ amount
    minimum_order = Column(Float, default=0)
    maximum_discount = Column(Float, nullable=True)         # cap on percent discounts
    usage_limit = Column(Integer, nullable=True)            # total uses allowed
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usages = relationship("CouponUsage", back_populates="coupon")


class CouponUsage(Base):
    __tablename__ = "coupon_usage"

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, nullable=True)
    used_at = Column(DateTime(timezone=True), server_default=func.now())

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User", back_populates="coupon_usages")
