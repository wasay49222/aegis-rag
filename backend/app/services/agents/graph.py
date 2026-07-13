import httpx
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.services.rag import RAGPipeline

class AgentState(TypedDict):
    query: str
    user_id: str
    document_id: str
    context_chunks: List[Dict[str, Any]]
    answer: str
    critique: str
    retries: int

class MultiAgentGraph:
    def __init__(self):
        self.pipeline = RAGPipeline()
        self.max_retries = 2
        
    def research_node(self, state: AgentState):
        """The Researcher Agent: Retrieves context and generates an answer."""
        print("[RESEARCHER] Retrieving context and generating initial answer...")
        
        chunks, pii_log = self.pipeline.retrieve(
            query=state["query"],
            user_id=state["user_id"],
            document_id=state["document_id"],
            top_k=3
        )
        
        answer, gen_pii_log = self.pipeline.generate_answer(state["query"], chunks)
        
        return {
            "context_chunks": chunks,
            "answer": answer,
            "retries": state["retries"] + 1
        }

    def critic_node(self, state: AgentState):
        """
        Dummy Critic for Development: Always approves to ensure fast responses.
        In production, this will be replaced with robust LLM-based fact-checking.
        """
        print("[CRITIC] Quick approval (Development mode - LLM check disabled)...")
        return {"critique": "APPROVED"}

    def should_continue(self, state: AgentState):
        """Decides whether to loop back to the Researcher or end the graph."""
        if "APPROVED" in state["critique"]:
            print("[GRAPH] Answer approved! Ending workflow.")
            return "end"
        if state["retries"] >= self.max_retries:
            print("[GRAPH] Max retries reached. Accepting answer.")
            return "end"
        
        print("[GRAPH] Answer rejected! Looping back to Researcher.")
        return "research"

    def build_graph(self):
        """Compiles the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("research", self.research_node)
        workflow.add_node("critic", self.critic_node)
        
        workflow.set_entry_point("research")
        workflow.add_edge("research", "critic")
        workflow.add_conditional_edges(
            "critic",
            self.should_continue,
            {
                "research": "research",
                "end": END
            }
        )
        
        return workflow.compile()