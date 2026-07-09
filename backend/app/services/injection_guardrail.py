from transformers import pipeline

class InjectionGuardrail:
    def __init__(self):
        """
        Initialize the Prompt Injection Classifier.
        We use ProtectAI's DeBERTa model, which is the industry standard 
        for fast, local detection of jailbreaks and injections.
        """
        print("[SECURITY] Loading Prompt Injection Classifier...")
        self.classifier = pipeline(
            "text-classification", 
            model="protectai/deberta-v3-base-prompt-injection",
            truncation=True,
            max_length=512
        )
        print("[SECURITY] Injection Classifier loaded successfully.")

    def is_safe(self, text: str) -> bool:
        """
        Analyzes text and returns True if it is SAFE, False if it is an INJECTION.
        """
        if not text.strip():
            return True # Empty text is safe
            
        # Run the text through the classifier
        result = self.classifier(text)[0]
        
        # The model outputs labels: 'SAFE' or 'INJECTION' with a confidence score
        label = result['label']
        score = result['score']
        
        print(f"[GUARDRAIL] Injection Check -> Label: {label}, Confidence: {score:.4f}")
        
        # If it's classified as an injection with high confidence, block it
        if label == 'INJECTION' and score > 0.75:
            return False # It is an injection (BLOCKED)
            
        return True # It is safe