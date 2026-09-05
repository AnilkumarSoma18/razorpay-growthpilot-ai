
import pytest
import uuid
from unittest.mock import MagicMock
from app.services.authorization_service import can_execute
from app.models.agent import ApprovalRequest
from app.models.enums import ApprovalStatus

def test_can_execute_approved_returns_true():
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_approval = ApprovalRequest(status=ApprovalStatus.APPROVED)
    mock_result.scalars.return_value.first.return_value = mock_approval
    mock_db.execute.return_value = mock_result
    
    result = can_execute(mock_db, uuid.uuid4(), uuid.uuid4())
    assert result is True

def test_can_execute_no_approval_returns_false():
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = can_execute(mock_db, uuid.uuid4(), uuid.uuid4())
    assert result is False
