# backend/app/services/agents/graph.py
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
        
        # Use .get() with fallbacks to prevent KeyError crashes
        query = state.get("query", "")
        user_id = state.get("user_id", "")
        doc_id = state.get("document_id", "")
        
        chunks, pii_log = self.pipeline.retrieve(
            query=query,
            user_id=user_id,
            document_id=doc_id,
            top_k=3
        )
        
        answer, gen_pii_log = self.pipeline.generate_answer(query, chunks)
        
        return {
            "context_chunks": chunks,
            "answer": answer,
            "retries": state.get("retries", 0) + 1
        }

    def critic_node(self, state: AgentState):
        print("[CRITIC] Quick approval (Development mode - LLM check disabled)...")
        return {"critique": "APPROVED"}

    def should_continue(self, state: AgentState):
        if "APPROVED" in state.get("critique", ""):
            print("[GRAPH] Answer approved! Ending workflow.")
            return "end"
        if state.get("retries", 0) >= self.max_retries:
            print("[GRAPH] Max retries reached. Accepting answer.")
            return "end"
        
        print("[GRAPH] Answer rejected! Looping back to Researcher.")
        return "research"

    def build_graph(self):
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

# Module-level instantiation
_agent_instance = MultiAgentGraph()
compiled_graph = _agent_instance.build_graph()