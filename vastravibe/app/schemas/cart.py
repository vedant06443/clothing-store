from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1
    color: Optional[str] = None
    size: Optional[str] = None


class CartItemUpdate(BaseModel):
    quantity: int


class CartProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    discount_price: Optional[float]
    primary_image: str


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    color: Optional[str]
    size: Optional[str]
    product: CartProductOut


class CartSummary(BaseModel):
    items: List[CartItemOut]
    subtotal: float
    discount: float
    shipping: float
    total: float
    item_count: int


class WishlistItemAdd(BaseModel):
    product_id: int


class AddressCreate(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None
    address_type: str = "Home"
    is_default: bool = False


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    pincode: str
    landmark: Optional[str]
    address_type: str
    is_default: bool


class OrderCreate(BaseModel):
    address_id: int
    payment_method: str = "Online"  # Online, COD
    coupon_code: Optional[str] = None


class ReviewCreate(BaseModel):
    product_id: int
    order_item_id: Optional[int] = None
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None


class CouponApply(BaseModel):
    code: str
    order_amount: float
