import httpx
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.services.rag import RAGPipeline
from app.services.evaluation import RAGEvaluator

# 1. Define the "Memory" (State) of our Graph
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
        # We reuse our existing, secure RAG pipeline for the heavy lifting
        self.pipeline = RAGPipeline()
        self.evaluator = RAGEvaluator() # The mathematical judge
        self.max_retries = 2
        
    def research_node(self, state: AgentState):
        """The Researcher Agent: Retrieves context and generates an answer."""
        print("[RESEARCHER] Retrieving context and generating initial answer...")
        
        # Use the existing pipeline (which includes PII and Injection guardrails)
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
        """The Critic Agent: Uses Ragas metrics to objectively verify faithfulness."""
        print("[CRITIC] Evaluating answer using Ragas metrics...")
        
        # Extract the raw text from the context chunks
        contexts = [c.get("text", "") for c in state["context_chunks"]]
        
        # Run the mathematical evaluation
        scores = self.evaluator.evaluate(
            query=state["query"],
            answer=state["answer"],
            contexts=contexts
        )
        
        faithfulness_score = scores.get("faithfulness", 0.0)
        relevancy_score = scores.get("answer_relevancy", 0.0)
        
        print(f"[CRITIC] Ragas Scores -> Faithfulness: {faithfulness_score:.2f}, Relevancy: {relevancy_score:.2f}")
        
        # Enterprise Thresholds
        # Faithfulness must be > 0.8 (80% of the answer must be grounded in context)
        # Relevancy must be > 0.7 (The answer must actually address the prompt)
        if faithfulness_score >= 0.8 and relevancy_score >= 0.7:
            verdict = "APPROVED"
        else:
            verdict = "REJECTED"
            
        print(f"[CRITIC] Verdict: {verdict}")
        
        return {"critique": verdict}

    def should_continue(self, state: AgentState):
        """Decides whether to loop back to the Researcher or end the graph."""
        if "APPROVED" in state["critique"]:
            print("[GRAPH] Answer approved! Ending workflow.")
            return "end"
        if state["retries"] >= self.max_retries:
            print("[GRAPH] Max retries reached. Accepting answer to prevent infinite loop.")
            return "end"
        
        print("[GRAPH] Answer rejected! Looping back to Researcher.")
        return "research"

    def build_graph(self):
        """Compiles the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add the nodes (the agents)
        workflow.add_node("research", self.research_node)
        workflow.add_node("critic", self.critic_node)
        
        # Set the entry point
        workflow.set_entry_point("research")
        
        # Add the edges (the flow)
        workflow.add_edge("research", "critic")
        workflow.add_conditional_edges(
            "critic",
            self.should_continue,
            {
                "research": "research", # Loop back if rejected
                "end": END              # Finish if approved or max retries
            }
        )
        
        return workflow.compile()