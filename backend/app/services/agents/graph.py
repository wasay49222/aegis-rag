import httpx
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.services.rag import RAGPipeline

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
        """The Critic Agent: Checks if the answer is actually supported by the context."""
        print("[CRITIC] Reviewing the Researcher's answer for hallucinations...")
        
        # Combine context into a single string for the prompt
        context_text = "\n".join([c.get("text", "") for c in state["context_chunks"]])
        
        # The Critic's Prompt
        critique_prompt = f"""You are a strict fact-checker. 
Given the Context and the Answer, does the Answer contain any information NOT found in the Context?
If it is perfectly factual, reply with exactly: APPROVED
If it contains hallucinations or outside info, reply with exactly: REJECTED

Context: {context_text}
Answer: {state["answer"]}

Verdict:"""

        # Call the local Ollama API to act as the Critic
        payload = {
            "model": "llama3.2:1b",
            "prompt": critique_prompt,
            "stream": False,
            "options": {"num_predict": 10} # We only need a single word response
        }
        response = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=60.0)
        verdict = response.json().get("response", "").strip().upper()
        
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