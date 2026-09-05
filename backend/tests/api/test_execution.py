
import pytest
import uuid
from unittest.mock import MagicMock
# Instead of using TestClient which needs Postgres, we will test the unit function directly.
from app.api.execution import simulate_strategy, SimulateReq
from fastapi import HTTPException
from app.models.growth import GrowthOpportunity
from app.models.enums import OpportunityType

def test_simulation_fallback():
    mock_db = MagicMock()
    mock_opp = MagicMock()
    mock_opp.merchant_id = uuid.uuid4()
    mock_opp.type.value = "CROSS_SELL"
    mock_opp.evidence = {"co_purchase_count": 100}
    mock_db.get.return_value = mock_opp
    
    req = SimulateReq(merchant_id=mock_opp.merchant_id, opportunity_id=uuid.uuid4())
    result = simulate_strategy(req, mock_db)
    
    assert result["simulation_status"] == "SIMULATED"
    assert "historical_affected_population" in result["baseline_metrics"]
    assert "simulated_additional_exposures" in result["simulated_metrics"]

def test_simulation_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None
    
    req = SimulateReq(merchant_id=uuid.uuid4(), opportunity_id=uuid.uuid4())
    with pytest.raises(HTTPException):
        simulate_strategy(req, mock_db)
