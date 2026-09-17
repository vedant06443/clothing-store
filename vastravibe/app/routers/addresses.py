from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.address import Address
from app.schemas.cart import AddressCreate, AddressOut
from app.utils.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/api/addresses", tags=["addresses"])


@router.get("/", response_model=List[AddressOut])
async def get_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == user.id).all()


@router.post("/", response_model=AddressOut)
async def add_address(data: AddressCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.is_default:
        # Unset other defaults
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})

    address = Address(user_id=user.id, **data.dict())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/{address_id}", response_model=AddressOut)
async def update_address(address_id: int, data: AddressCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id, Address.id != address_id).update({"is_default": False})

    for field, value in data.dict().items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}")
async def delete_address(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(address)
    db.commit()
    return {"message": "Address deleted"}


@router.put("/{address_id}/set-default")
async def set_default(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    address.is_default = True
    db.commit()
    return {"message": "Default address updated"}
