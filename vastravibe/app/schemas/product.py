from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    is_primary: bool
    alt_text: Optional[str]


class ProductVariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    color: Optional[str]
    size: Optional[str]
    stock: int


class ProductListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    brand: str
    price: float
    discount_price: Optional[float]
    discount_percent: int
    rating: float
    review_count: int
    stock: int
    is_featured: bool
    is_bestseller: bool
    is_new_arrival: bool
    primary_image: str
    category_id: int


class ProductDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    brand: str
    description: Optional[str]
    specifications: Optional[str]
    price: float
    discount_price: Optional[float]
    discount_percent: int
    fabric: Optional[str]
    occasion: Optional[str]
    colors: Optional[str]
    sizes: Optional[str]
    care_instructions: Optional[str]
    stock: int
    rating: float
    review_count: int
    is_featured: bool
    is_bestseller: bool
    is_new_arrival: bool
    category_id: int
    images: List[ProductImageOut] = []
    variants: List[ProductVariantOut] = []


class ProductCreate(BaseModel):
    name: str
    category_id: int
    brand: str = "Suyog Collection"
    description: Optional[str]
    specifications: Optional[str]
    price: float
    discount_price: Optional[float]
    fabric: Optional[str]
    occasion: Optional[str]
    colors: Optional[str]
    sizes: Optional[str]
    care_instructions: Optional[str]
    stock: int = 0
    is_featured: bool = False
    is_bestseller: bool = False
    is_new_arrival: bool = False


class ProductUpdate(ProductCreate):
    pass
