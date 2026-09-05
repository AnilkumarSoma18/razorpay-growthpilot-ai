import pytest
import uuid
from decimal import Decimal
from unittest.mock import MagicMock
from app.services.shopping_service import calculate_totals

def test_decimal_precision():
    mock_db = MagicMock()
    
    mock_item1 = MagicMock()
    mock_item1.quantity = 3
    mock_prod1 = MagicMock()
    mock_prod1.price = 100.10
    
    mock_item2 = MagicMock()
    mock_item2.quantity = 2
    mock_prod2 = MagicMock()
    mock_prod2.price = 999.99
    
    import app.services.shopping_service
    original_get = app.services.shopping_service.get_cart_items
    app.services.shopping_service.get_cart_items = lambda db, cid: [(mock_item1, mock_prod1), (mock_item2, mock_prod2)]
    
    totals = calculate_totals(mock_db, uuid.uuid4())
    
    assert totals["subtotal"] == Decimal('2300.28')
    assert totals["total_amount"] == Decimal('2300.28')
    
    app.services.shopping_service.get_cart_items = original_get
