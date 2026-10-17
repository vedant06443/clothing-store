from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    color = Column(String(50), nullable=True)
    size = Column(String(20), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    @property
    def unit_price(self) -> float:
        if not self.product:
            return 0.0
        return float(self.product.discount_price if self.product.discount_price else self.product.price or 0.0)

    @property
    def total_price(self) -> float:
        return float(self.unit_price * (self.quantity or 1))

