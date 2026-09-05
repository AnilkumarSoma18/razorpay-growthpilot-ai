import pytest
import uuid
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.api.shopping import chat, shopping_action, get_cart_view, ChatRequest, ActionRequest
from app.models.product import Product

def test_chat_extracts_intent_and_searches():
    mock_db = MagicMock()
    
    # Mock search_products behavior via the function that gets called. But since search_products is imported inside api, we mock db.execute.
    mock_product = Product(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        name="Wireless Headphones",
        price=2999.00,
        description="Noise cancelling"
    )
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_product]

    req = ChatRequest(merchant_id=uuid.uuid4(), session_id="test_session", message="I need headphones under 3000")
    
    # The actual chat uses the ShoppingAgent which we defined locally.
    res = chat(req, mock_db)
    
    assert res["intent"] == "SEARCH"
    assert len(res["products"]) == 1
    assert res["products"][0]["name"] == "Wireless Headphones"

def test_shopping_action_add_to_cart():
    mock_db = MagicMock()
    mock_cart = MagicMock()
    mock_cart.id = uuid.uuid4()
    
    # Mocking get_or_create_cart query
    mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_cart, None]
    
    req = ActionRequest(merchant_id=uuid.uuid4(), session_id="test_session", product_id=uuid.uuid4(), action="add_to_cart")
    res = shopping_action(req, mock_db)
    
    assert res["status"] == "success"

def test_shopping_action_invalid():
    mock_db = MagicMock()
    req = ActionRequest(merchant_id=uuid.uuid4(), session_id="test_session", product_id=uuid.uuid4(), action="invalid")
    
    with pytest.raises(HTTPException) as exc:
        shopping_action(req, mock_db)
        
    assert exc.value.status_code == 400
