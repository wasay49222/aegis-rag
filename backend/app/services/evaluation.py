from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
import threading

class RAGEvaluator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RAGEvaluator, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def _initialize(self):
        if not self._initialized:
            print("[RAGAS] Initializing local evaluator models (this takes time, but only happens once)...")
            # Use host.docker.internal to reach Ollama on the host machine
            self.llm = LangchainLLMWrapper(Ollama(base_url="http://host.docker.internal:11434", model="llama3.2:1b", temperature=0))
            self.embeddings = LangchainEmbeddingsWrapper(
                HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            )
            self._initialized = True
            print("[RAGAS] Evaluator initialized and ready.")

    def evaluate(self, query: str, answer: str, contexts: list) -> dict:
        self._initialize()
        
        data = {
            "question": [query],
            "answer": [answer],
            "contexts": [contexts],
        }
        dataset = Dataset.from_dict(data)

        try:
            result = evaluate(
                dataset=dataset,
                metrics=[faithfulness, answer_relevancy],
                llm=self.llm,
                embeddings=self.embeddings,
            )
            return {
                "faithfulness": float(result["faithfulness"]),
                "answer_relevancy": float(result["answer_relevancy"])
            }
        except Exception as e:
            print(f"[RAGAS ERROR] Evaluation failed: {e}")
            return {"faithfulness": 0.0, "answer_relevancy": 0.0}
        