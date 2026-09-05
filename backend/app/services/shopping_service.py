from decimal import Decimal

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.product import Product
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.enums import OrderStatus, OrderSource

def search_products(db: Session, merchant_id: uuid.UUID, query: str = "", max_price: float = None, category: str = None, limit: int = 5):
    stmt = select(Product).where(Product.merchant_id == merchant_id, Product.is_active == True)
    if query:
        stmt = stmt.where(Product.name.ilike(f"%{query}%"))
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    
    # We ignore category strict matching for mock demo unless it matches perfectly.
    
    stmt = stmt.order_by(Product.price.asc()).limit(limit)
    return db.execute(stmt).scalars().all()

def get_or_create_cart(db: Session, merchant_id: uuid.UUID, session_id: str):
    stmt = select(Cart).where(Cart.merchant_id == merchant_id, Cart.session_id == session_id)
    cart = db.execute(stmt).scalars().first()
    if not cart:
        cart = Cart(id=uuid.uuid4(), merchant_id=merchant_id, session_id=session_id)
        db.add(cart)
        db.commit()
    return cart

def get_cart_items(db: Session, cart_id: uuid.UUID):
    stmt = select(CartItem, Product).join(Product).where(CartItem.cart_id == cart_id)
    return db.execute(stmt).all()

def add_to_cart(db: Session, cart_id: uuid.UUID, product_id: uuid.UUID, quantity: int = 1):
    stmt = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
    item = db.execute(stmt).scalars().first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(id=uuid.uuid4(), cart_id=cart_id, product_id=product_id, quantity=quantity)
        db.add(item)
    db.commit()
    return item

def clear_cart(db: Session, cart_id: uuid.UUID):
    db.execute(CartItem.__table__.delete().where(CartItem.cart_id == cart_id))
    db.commit()

def calculate_totals(db: Session, cart_id: uuid.UUID):
    items = get_cart_items(db, cart_id)
    subtotal = sum(round(Decimal(str(product.price)) * Decimal(item.quantity), 2) for item, product in items)
    return {"subtotal": subtotal, "total_amount": subtotal}

def create_order_from_cart(db: Session, cart: Cart, customer_id: uuid.UUID):
    items = get_cart_items(db, cart.id)
    if not items:
        raise ValueError("Cart is empty")
        
    totals = calculate_totals(db, cart.id)
    order = Order(
        id=uuid.uuid4(),
        merchant_id=cart.merchant_id,
        customer_id=customer_id,
        status=OrderStatus.PENDING,
        subtotal=totals["subtotal"],
        total_amount=totals["total_amount"],
        source=OrderSource.AI_SHOPPING_AGENT
    )
    db.add(order)
    
    for item, product in items:
        oi = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price,
            total_price=round(Decimal(str(product.price)) * Decimal(item.quantity), 2)
        )
        db.add(oi)
        
    clear_cart(db, cart.id)
    db.commit()
    return order
