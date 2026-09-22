"""LangGraph workflow for the agentic RAG assistant."""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.nodes import AgentNodes
from app.agent.state import AgentState


def build_agent_graph(nodes: AgentNodes) -> CompiledStateGraph:
    """Build the agentic RAG workflow."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", nodes.planner)
    graph.add_node("retriever", nodes.retrieve)
    graph.add_node("generator", nodes.generate)
    graph.add_node("verifier", nodes.verify)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "generator")
    graph.add_edge("generator", "verifier")

    graph.add_conditional_edges(
        "verifier",
        _verification_route,
        {
            "retriever": "retriever",
            "end": END,
        },
    )

    return graph.compile()


def _verification_route(state: AgentState) -> str:
    """Choose whether to finish or retry retrieval."""
    if state.verification_passed:
        return "end"

    if state.retrieval_attempts >= 2:
        return "end"

    return "retriever"
