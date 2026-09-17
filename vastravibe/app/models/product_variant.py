from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    color = Column(String(50), nullable=True)
    size = Column(String(20), nullable=True)
    stock = Column(Integer, default=0)
    additional_price = Column(Integer, default=0)  # extra price for this variant

    product = relationship("Product", back_populates="variants")
