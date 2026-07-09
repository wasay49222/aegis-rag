from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Tuple, List, Dict

class PIIGuardrail:
    def __init__(self):
        """
        Initialize the Presidio Analyzer (detects PII) and Anonymizer (masks PII).
        These engines are heavy, so we initialize them once globally.
        """
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Define how we want to mask different types of PII
        self.operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
            "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})
        }

    def redact(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Scans text for PII, replaces it with tags, and returns the clean text 
        along with an audit log of what was found.
        
        Returns:
            Tuple of (redacted_text, list_of_detected_pii_types)
        """
        if not text.strip():
            return text, []

        # 1. Analyze the text to find PII entities
        analyzer_results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN"]
        )
        
        # If no PII is found, return the original text immediately to save compute
        if not analyzer_results:
            return text, []

        # 2. Anonymize (mask) the detected PII
        anonymizer_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=self.operators
        )
        
        # 3. Build an audit log for compliance (SOC2/HIPAA)
        audit_log = []
        for entity in analyzer_results:
            audit_log.append({
                "entity_type": entity.entity_type,
                "start_index": entity.start,
                "end_index": entity.end
            })
            
        return anonymizer_result.text, audit_log