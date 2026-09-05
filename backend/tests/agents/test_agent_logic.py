import pytest
from app.agents.nodes.opportunities import calculate_normalized_score
from app.agents.state import Strategy
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError

def test_calculate_normalized_score():
    score = calculate_normalized_score(100.0, 80.0, 90.0, 95.0, 10.0)
    assert score["final_score"] == 83.0
    
    score_cap = calculate_normalized_score(150.0, 150.0, 150.0, 150.0, 0.0)
    assert score_cap["final_score"] == 100.0
    
    score_floor = calculate_normalized_score(0.0, 0.0, 0.0, 0.0, 50.0)
    assert score_floor["final_score"] == 0.0

def test_strategy_schema_validation():
    valid_data = {
        "strategy_id": uuid.uuid4(),
        "opportunity_id": uuid.uuid4(),
        "strategy_type": "BUNDLE",
        "title": "Test Title",
        "summary": "Test Summary",
        "rationale": "Reason",
        "target": "Customers",
        "recommended_action": "Do it",
        "constraints": ["No discounts"],
        "risk_level": "LOW",
        "approval_required": True,
        "expected_effect": "More revenue",
        "prediction_status": "UNAVAILABLE",
        "created_at": datetime.now(timezone.utc)
    }
    strategy = Strategy(**valid_data)
    assert strategy.title == "Test Title"
    
    invalid_data = valid_data.copy()
    del invalid_data["title"]
    with pytest.raises(ValidationError):
        Strategy(**invalid_data)
