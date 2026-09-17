from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    subtitle = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False)
    mobile_image_url = Column(String(500), nullable=True)
    link_url = Column(String(500), nullable=True)
    button_text = Column(String(100), nullable=True)
    position = Column(String(50), default="hero")  # hero, category, offer
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @property
    def display_image(self) -> str:
        from app.utils.helpers import get_image_url
        return get_image_url(self.image_url)

