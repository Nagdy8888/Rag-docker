"""Graph definition: retrieve -> generate. Composes state, nodes, and LLM."""

from langgraph.graph import END, StateGraph

from app.agent.state import AgentState
from app.agent.llm import get_chat_llm
from app.agent.nodes import retrieve_node, generate_node


def create_chat_graph():
    """
    Phase 2 graph: __start__ -> retrieve -> generate -> __end__
    Used for non-streaming or batch; for streaming use stream_chat_response.
    """
    llm = get_chat_llm()

    async def generate(state: AgentState) -> dict:
        return await generate_node(state, llm)

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate)
    graph.add_edge("__start__", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
