from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import List, Tuple, Dict

class PIIGuardrail:
    def __init__(self):
        # Initialize the Presidio engines
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Technical terms that should NOT be flagged as PII
        self.tech_whitelist = {
            "Ragas", "LangGraph", "Qdrant", "NeMo", "FastAPI", 
            "Next.js", "PostgreSQL", "Redis", "LangChain", "PyMuPDF",
            "Presidio", "Ollama", "Llama", "Docker", "GitHub"
        }
        
        print("[SECURITY] PII Guardrail initialized with tech whitelist.")

    def redact(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Analyzes text for PII, redacts it, and returns an audit log.
        """
        if not text or not text.strip():
            return text, []

        # Step 1: Analyze the text for PII entities
        analyzer_results = self.analyzer.analyze(
            text=text,
            language='en',
            score_threshold=0.5
        )

        # Step 2: Filter out false positives (tech terms in the whitelist)
        filtered_results = []
        for result in analyzer_results:
            entity_text = text[result.start:result.end]
            
            # Skip if this entity is a known technical term
            if entity_text in self.tech_whitelist:
                print(f"[GUARDRAIL] Whitelisted tech term ignored: {entity_text}")
                continue
            
            # Otherwise, keep it for redaction
            filtered_results.append(result)

        # Step 3: If no PII found after filtering, return original text
        if not filtered_results:
            return text, []

        # Step 4: Anonymize the text
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=filtered_results
        )

        # Step 5: Build the audit log
        audit_log = []
        for result in filtered_results:
            entity_text = text[result.start:result.end]
            audit_log.append({
                "entity_type": result.entity_type,
                "original_text": entity_text,
                "start": result.start,
                "end": result.end,
                "score": result.score
            })

        return anonymized_result.text, audit_log