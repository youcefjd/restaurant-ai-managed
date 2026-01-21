"""Customer endpoints with phone-based lookup."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.database import get_db, SupabaseDB
from backend.schemas import CustomerCreate, CustomerUpdate, Customer as CustomerResponse

router = APIRouter()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new customer."""
    # Check if customer with phone already exists
    existing = db.query_one("customers", {"phone": customer_data.phone})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this phone number already exists"
        )

    customer = db.insert("customers", customer_data.model_dump())
    return customer


@router.get("/phone/{phone}", response_model=CustomerResponse)
async def get_customer_by_phone(phone: str, db: SupabaseDB = Depends(get_db)):
    """Get a customer by phone number."""
    customer = db.query_one("customers", {"phone": phone})
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: SupabaseDB = Depends(get_db)):
    """Get a customer by ID."""
    customer = db.query_one("customers", {"id": customer_id})
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """List all customers."""
    customers = db.query_all("customers", offset=skip, limit=limit)
    return customers


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update a customer."""
    # Check if customer exists
    existing = db.query_one("customers", {"id": customer_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    update_data = customer_data.model_dump(exclude_unset=True)
    if update_data:
        customer = db.update("customers", customer_id, update_data)
    else:
        customer = existing

    return customer
