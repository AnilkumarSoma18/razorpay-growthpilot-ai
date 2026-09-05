
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes.observe import observe_node
from app.agents.nodes.analyze import analyze_node
from app.agents.nodes.opportunities import generate_opportunities_node
from app.agents.nodes.strategy import strategy_node
from sqlalchemy.orm import Session

def create_growth_agent(db: Session):
    def observe(state: AgentState):
        return observe_node(state, db)
    
    def analyze(state: AgentState):
        return analyze_node(state)
        
    def opportunities(state: AgentState):
        return generate_opportunities_node(state, db)
        
    def strategy(state: AgentState):
        return strategy_node(state, db)

    workflow = StateGraph(AgentState)
    workflow.add_node("observe", observe)
    workflow.add_node("analyze", analyze)
    workflow.add_node("opportunities", opportunities)
    workflow.add_node("strategy", strategy)
    
    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "analyze")
    workflow.add_edge("analyze", "opportunities")
    workflow.add_edge("opportunities", "strategy")
    workflow.add_edge("strategy", END)
    
    return workflow.compile()
