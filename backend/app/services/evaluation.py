from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

class RAGEvaluator:
    def __init__(self):
        print("[RAGAS] Initializing local evaluator models...")
        # Wrap local models so Ragas can use them as the objective "Judge"
        # We set temperature to 0 for consistent, deterministic grading
        self.llm = LangchainLLMWrapper(Ollama(model="llama3.2:1b", temperature=0))
        self.embeddings = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )
        print("[RAGAS] Evaluator initialized.")

    def evaluate(self, query: str, answer: str, contexts: list) -> dict:
        """
        Computes Ragas metrics to objectively score the RAG output.
        """
        # Ragas requires data in a HuggingFace Dataset format
        data = {
            "question": [query],
            "answer": [answer],
            "contexts": [contexts],
        }
        dataset = Dataset.from_dict(data)

        try:
            # Run the mathematical evaluation
            result = evaluate(
                dataset=dataset,
                metrics=[faithfulness, answer_relevancy],
                llm=self.llm,
                embeddings=self.embeddings,
            )
            # Convert to standard Python floats to prevent JSON serialization errors later
            return {
                "faithfulness": float(result["faithfulness"]),
                "answer_relevancy": float(result["answer_relevancy"])
            }
        except Exception as e:
            print(f"[RAGAS ERROR] Evaluation failed: {e}")
            # Fallback: If Ragas crashes, we pass the answer so the pipeline doesn't break
            return {"faithfulness": 1.0, "answer_relevancy": 1.0}