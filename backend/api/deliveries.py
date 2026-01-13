"""
Delivery and order management endpoints.

Handles order creation, delivery tracking, and status updates.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Order, Delivery, Customer, Restaurant, OrderStatus, DeliveryStatus
from backend.schemas_delivery import (
    OrderCreate, OrderUpdate, OrderResponse, OrderWithDelivery,
    DeliveryCreate, DeliveryUpdate, DeliveryResponse
)
from backend.services.sms_service import sms_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new food order."""
    # Get or create customer
    customer = db.query(Customer).filter(Customer.phone == order_data.customer_phone).first()
    if not customer:
        if not order_data.customer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name required for new customers"
            )
        customer = Customer(
            phone=order_data.customer_phone,
            name=order_data.customer_name,
            email=order_data.customer_email
        )
        db.add(customer)
        db.flush()

    # Create order
    order_dict = order_data.model_dump(exclude={'customer_phone', 'customer_name', 'customer_email'})
    order = Order(
        **order_dict,
        customer_id=customer.id,
        status=OrderStatus.CONFIRMED
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Send SMS confirmation
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
        if restaurant and sms_service.enabled:
            # Get restaurant's Twilio phone number
            from_number = None
            if restaurant.account:
                from_number = restaurant.account.twilio_phone_number
            
            if from_number:
                # Parse order items for SMS
                try:
                    items = json.loads(order.order_items)
                    items_text = "\\n".join([f"- {item.get('quantity', 1)}x {item.get('name', 'Item')}" for item in items])
                except:
                    items_text = "Your order"

                message = f"""
📦 Order Confirmed!

Restaurant: {restaurant.name}
Order #{order.id}

{items_text}

Total: ${order.total / 100:.2f}
Delivery to: {order.delivery_address}

We'll notify you when your order is ready for delivery!
                """.strip()

                sms_service.send_sms(customer.phone, message, from_number=from_number)
            else:
                logger.warning(f"Cannot send order confirmation SMS - restaurant {restaurant.id} has no Twilio phone number configured")
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")

    return order


@router.get("/orders/{order_id}", response_model=OrderWithDelivery)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get an order by ID with delivery details."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    restaurant_id: Optional[int] = Query(None),
    customer_phone: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List orders with optional filters."""
    query = db.query(Order)

    if restaurant_id:
        query = query.filter(Order.restaurant_id == restaurant_id)

    if customer_phone:
        customer = db.query(Customer).filter(Customer.phone == customer_phone).first()
        if customer:
            query = query.filter(Order.customer_id == customer.id)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update an order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    update_dict = order_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)

    # Send status update SMS
    if 'status' in update_dict:
        try:
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()

            if customer and restaurant and sms_service.enabled:
                # Get restaurant's Twilio phone number
                from_number = None
                if restaurant.account:
                    from_number = restaurant.account.twilio_phone_number
                
                if from_number:
                    status_messages = {
                        "preparing": f"🍳 Your order #{order.id} from {restaurant.name} is being prepared!",
                        "ready": f"✅ Your order #{order.id} is ready for pickup/delivery!",
                        "out_for_delivery": f"🚗 Your order #{order.id} is out for delivery! It should arrive soon.",
                        "delivered": f"🎉 Your order #{order.id} has been delivered! Enjoy your meal!",
                        "cancelled": f"❌ Your order #{order.id} has been cancelled."
                    }

                    message = status_messages.get(order.status, f"Order #{order.id} status: {order.status}")
                    sms_service.send_sms(customer.phone, message, from_number=from_number)
                else:
                    logger.warning(f"Cannot send order status SMS - restaurant {restaurant.id} has no Twilio phone number configured")
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")

    return order


@router.post("/deliveries", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    delivery_data: DeliveryCreate,
    db: Session = Depends(get_db)
):
    """Create a delivery for an order."""
    # Verify order exists
    order = db.query(Order).filter(Order.id == delivery_data.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Check if delivery already exists
    existing_delivery = db.query(Delivery).filter(Delivery.order_id == delivery_data.order_id).first()
    if existing_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery already exists for this order"
        )

    # Create delivery
    delivery = Delivery(**delivery_data.model_dump())
    db.add(delivery)

    # Update order status
    order.status = OrderStatus.OUT_FOR_DELIVERY

    db.commit()
    db.refresh(delivery)

    return delivery


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """Get a delivery by ID."""
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery


@router.put("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def update_delivery(
    delivery_id: int,
    delivery_data: DeliveryUpdate,
    db: Session = Depends(get_db)
):
    """Update delivery status and tracking information."""
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    update_dict = delivery_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(delivery, field, value)

    # Update actual delivery time if status is delivered
    if delivery.status == DeliveryStatus.DELIVERED and not delivery.actual_delivery_time:
        delivery.actual_delivery_time = datetime.now()

    db.commit()
    db.refresh(delivery)

    # Update order status if delivery is completed
    if delivery.status == DeliveryStatus.DELIVERED:
        order = db.query(Order).filter(Order.id == delivery.order_id).first()
        if order:
            order.status = OrderStatus.DELIVERED
            db.commit()

    return delivery


@router.get("/deliveries", response_model=List[DeliveryResponse])
async def list_deliveries(
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List deliveries with optional status filter."""
    query = db.query(Delivery)

    if status_filter:
        query = query.filter(Delivery.status == status_filter)

    deliveries = query.order_by(Delivery.created_at.desc()).offset(skip).limit(limit).all()
    return deliveries
