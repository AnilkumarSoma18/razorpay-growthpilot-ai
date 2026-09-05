
from app.agents.state import AgentState

def analyze_node(state: AgentState) -> dict:
    metrics = state.get("observed_metrics", {})
    failed_rate = state.get("failed_payments", {}).get("failed_rate_percent", 0)
    abandon_rate = state.get("cart_abandonment", {}).get("abandonment_rate", 0)
    retention_rate = metrics.get("retention", {}).get("returning_customer_rate_percent", 0)
    
    analysis = f"Merchant shows {retention_rate}% retention. Failed payment rate is {failed_rate}%. Cart abandonment is {abandon_rate}%."
    return {"analysis_summary": analysis}
