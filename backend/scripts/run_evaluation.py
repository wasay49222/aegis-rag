import json
import os
import sys

# Add the backend directory to the path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rag import RAGPipeline
from app.services.evaluation import RAGEvaluator

def run_evaluation():
    print("[MLOPS] Starting automated evaluation pipeline...")
    
    # 1. Load the test dataset
    dataset_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'eval_dataset.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
        
    print(f"[MLOPS] Loaded {len(dataset)} test cases.")
    
    # 2. Initialize services
    pipeline = RAGPipeline()
    evaluator = RAGEvaluator()
    
    results = []
    faithfulness_scores = []
    relevancy_scores = []
    
    # We use a dummy user_id for local evaluation
    dummy_user_id = "00000000-0000-0000-0000-000000000000"
    
    for i, item in enumerate(dataset):
        query = item['query']
        print(f"[MLOPS] Evaluating query {i+1}/{len(dataset)}: {query[:50]}...")
        
        # 3. Run the RAG pipeline (Retrieval + Generation)
        # Note: We bypass the injection guardrail for evaluation to ensure test queries aren't blocked
        chunks, _ = pipeline.retrieve(query=query, user_id=dummy_user_id, top_k=3)
        contexts = [c.get("text", "") for c in chunks]
        answer, _ = pipeline.generate_answer(query, chunks)
        
        # 4. Compute Ragas metrics
        scores = evaluator.evaluate(query=query, answer=answer, contexts=contexts)
        faithfulness = scores.get("faithfulness", 0.0)
        relevancy = scores.get("answer_relevancy", 0.0)
        
        faithfulness_scores.append(faithfulness)
        relevancy_scores.append(relevancy)
        
        results.append({
            "query": query,
            "answer": answer,
            "faithfulness": faithfulness,
            "answer_relevancy": relevancy
        })
        
    # 5. Aggregate metrics
    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0
    avg_relevancy = sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0
    
    report = {
        "total_queries": len(dataset),
        "average_faithfulness": avg_faithfulness,
        "average_answer_relevancy": avg_relevancy,
        "results": results
    }
    
    # 6. Save report
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, 'eval_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    print(f"[MLOPS] Evaluation complete. Report saved to {report_path}")
    print(f"[MLOPS] Average Faithfulness: {avg_faithfulness:.2f}")
    print(f"[MLOPS] Average Answer Relevancy: {avg_relevancy:.2f}")
    
    # 7. Check thresholds (The CI/CD Quality Gate)
    FAITHFULNESS_THRESHOLD = 0.8
    RELEVANCY_THRESHOLD = 0.7
    
    if avg_faithfulness < FAITHFULNESS_THRESHOLD or avg_relevancy < RELEVANCY_THRESHOLD:
        print("[MLOPS] ALERT: Metrics below threshold! Failing CI/CD pipeline.")
        sys.exit(1) # Exit with error code 1
    else:
        print("[MLOPS] All metrics passed thresholds. Deployment approved.")
        sys.exit(0) # Exit with success code 0

if __name__ == "__main__":
    run_evaluation()