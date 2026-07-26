# backend/app/services/pii_guardrail.py
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

class PIIGuardrail:
    def __init__(self):
        # Force Presidio to use the lightweight 'sm' Spacy model to save RAM
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=RecognizerRegistry())
        self.anonymizer = AnonymizerEngine()

    def redact(self, text: str) -> tuple:
        if not text:
            return text, []
            
        # Analyze for common PII
        results = self.analyzer.analyze(
            text=text, 
            language='en', 
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IP_ADDRESS"]
        )
        
        # Anonymize the text (replaces PII with <ENTITY_TYPE>)
        anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=results)
        
        # Extract what was redacted for audit logging using start/end indices
        redacted_entities = [
            {"entity": r.entity_type, "value": text[r.start:r.end]} 
            for r in results
        ]
        
        return anonymized_result.text, redacted_entities