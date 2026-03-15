"""Phase 4 graph: 7 nodes with conditional edges (analyze -> expand/retrieve -> grade -> generate/rewrite -> hallucination check)."""

from langgraph.graph import END, StateGraph

from app.agent.state import AgentState
from app.agent.llm import get_chat_llm
from app.agent.nodes import (
    analyze_query_node,
    expand_query_node,
    hybrid_retrieve_node,
    grade_documents_node,
    rewrite_query_node,
    retrieve_with_query_variant_node,
    generate_node,
    check_hallucination_node,
    increment_hallucination_retry_node,
    MIN_RELEVANT_DOCS,
    MAX_REWRITE_COUNT,
    MAX_HALLUCINATION_RETRY,
)


def _route_after_analyze(state: AgentState) -> str:
    """Route to expand_query (retrieval path) or generate (conversational)."""
    analysis = state.get("query_analysis") or {}
    if analysis.get("needs_retrieval"):
        return "expand_query"
    return "generate"


def _route_after_grade(state: AgentState) -> str:
    """Route to generate if enough relevant docs or already rewrote once; else rewrite_query."""
    graded = state.get("graded_docs") or []
    rewrite_count = state.get("rewrite_count") or 0
    if len(graded) >= MIN_RELEVANT_DOCS or rewrite_count >= MAX_REWRITE_COUNT:
        return "generate"
    return "rewrite_query"


def _route_after_hallucination_check(state: AgentState) -> str:
    """Route to END if grounded; else to increment_retry then generate (max 1 retry)."""
    verdict = (state.get("hallucination_verdict") or "grounded").strip().lower()
    retry = state.get("hallucination_retry_count") or 0
    if verdict == "grounded":
        return "__end__"
    if "not_grounded" in verdict and retry < MAX_HALLUCINATION_RETRY:
        return "increment_hallucination_retry"
    return "__end__"


def create_chat_graph():
    """
    Phase 4 graph:
    __start__ -> analyze_query -> (expand_query | generate)
    expand_query -> hybrid_retrieve -> grade_documents -> (generate | rewrite_query)
    rewrite_query -> retrieve_with_query_variant -> grade_documents -> ...
    generate -> check_hallucination -> (END | increment_hallucination_retry -> generate)
    """
    llm = get_chat_llm()

    def analyze(state: AgentState) -> dict:
        return analyze_query_node(state, llm)

    def expand(state: AgentState) -> dict:
        return expand_query_node(state, llm)

    def grade(state: AgentState) -> dict:
        return grade_documents_node(state, llm)

    def rewrite(state: AgentState) -> dict:
        return rewrite_query_node(state, llm)

    async def generate_async(state: AgentState) -> dict:
        return await generate_node(state, llm)

    def check_hallucination(state: AgentState) -> dict:
        return check_hallucination_node(state, llm)

    graph = StateGraph(AgentState)

    graph.add_node("analyze_query", analyze)
    graph.add_node("expand_query", expand)
    graph.add_node("hybrid_retrieve", hybrid_retrieve_node)
    graph.add_node("grade_documents", grade)
    graph.add_node("rewrite_query", rewrite)
    graph.add_node("retrieve_after_rewrite", retrieve_with_query_variant_node)
    graph.add_node("generate", generate_async)
    graph.add_node("check_hallucination", check_hallucination)
    graph.add_node("increment_hallucination_retry", increment_hallucination_retry_node)

    graph.add_edge("__start__", "analyze_query")
    graph.add_conditional_edges("analyze_query", _route_after_analyze, {"expand_query": "expand_query", "generate": "generate"})
    graph.add_edge("expand_query", "hybrid_retrieve")
    graph.add_edge("hybrid_retrieve", "grade_documents")
    graph.add_conditional_edges("grade_documents", _route_after_grade, {"generate": "generate", "rewrite_query": "rewrite_query"})
    graph.add_edge("rewrite_query", "retrieve_after_rewrite")
    graph.add_edge("retrieve_after_rewrite", "grade_documents")
    graph.add_edge("generate", "check_hallucination")
    graph.add_conditional_edges(
        "check_hallucination",
        _route_after_hallucination_check,
        {"__end__": END, "increment_hallucination_retry": "increment_hallucination_retry"},
    )
    graph.add_edge("increment_hallucination_retry", "generate")

    return graph.compile()
