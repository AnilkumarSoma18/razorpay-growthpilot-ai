
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.services.shopping_service import search_products

class ShoppingState(TypedDict):
    merchant_id: str
    session_id: str
    message: str
    intent: Optional[str]
    constraints: Dict[str, Any]
    candidate_products: List[Dict[str, Any]]
    response: str

def parse_intent(state: ShoppingState):
    msg = state["message"].lower()
    constraints = {}
    intent = "CHAT"
    
    # Very basic rule-based parsing since LLM might be unavailable
    if "under" in msg:
        try:
            # Extract number
            parts = msg.split("under")
            num_str = ''.join(filter(str.isdigit, parts[1]))
            if num_str:
                constraints["max_price"] = float(num_str)
        except:
            pass
            
    if "headphone" in msg:
        constraints["query"] = "headphone"
        intent = "SEARCH"
    elif "laptop" in msg:
        constraints["query"] = "laptop"
        intent = "SEARCH"
    elif "add" in msg or "cart" in msg:
        intent = "CART_INTENT"
    elif "checkout" in msg:
        intent = "CHECKOUT_INTENT"
        
    return {"intent": intent, "constraints": constraints}

def search_catalog(state: ShoppingState):
    if state["intent"] != "SEARCH":
        return {"candidate_products": []}
        
    # In a real environment, this would call the DB.
    # To keep the agent pure function for LangGraph, we will pass DB session in or do it at the route layer.
    # Here, we will just set up the intent. The route will handle the DB.
    return {}

def generate_response(state: ShoppingState):
    if state["intent"] == "SEARCH":
        return {"response": "Here are the top matches from our catalog based on your request."}
    elif state["intent"] == "CHECKOUT_INTENT":
        return {"response": "I can help you checkout. Creating your order now."}
    else:
        return {"response": "I am your AI Shopping Assistant. How can I help you today?"}

# We define a basic graph
workflow = StateGraph(ShoppingState)
workflow.add_node("parse_intent", parse_intent)
workflow.add_node("search_catalog", search_catalog)
workflow.add_node("generate_response", generate_response)

workflow.set_entry_point("parse_intent")
workflow.add_edge("parse_intent", "search_catalog")
workflow.add_edge("search_catalog", "generate_response")
workflow.add_edge("generate_response", END)

shopping_app = workflow.compile()
