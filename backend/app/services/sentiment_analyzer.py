from typing import Dict, Any
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from app.core.config import settings

class SentimentAnalyzer:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        
        # Initialize VADER
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize FinBERT
        self.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        
    def analyze_vader(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using VADER."""
        scores = self.vader.polarity_scores(text)
        return {
            "compound": scores["compound"],
            "confidence": abs(scores["compound"]),
            "model": "vader"
        }
    
    def analyze_finbert(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using FinBERT."""
        inputs = self.finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.finbert_model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # FinBERT labels: positive, negative, neutral
        labels = ["positive", "negative", "neutral"]
        scores = predictions[0].tolist()
        
        # Get the highest scoring sentiment
        max_score = max(scores)
        sentiment = labels[scores.index(max_score)]
        
        # Convert to compound score (-1 to 1)
        compound_score = {
            "positive": 1.0,
            "negative": -1.0,
            "neutral": 0.0
        }[sentiment]
        
        return {
            "compound": compound_score,
            "confidence": float(max_score),
            "model": "finbert",
            "sentiment": sentiment
        }
    
    def analyze(self, text: str, model: str = "vader") -> Dict[str, Any]:
        """Analyze sentiment using specified model."""
        if model.lower() == "vader":
            return self.analyze_vader(text)
        elif model.lower() == "finbert":
            return self.analyze_finbert(text)
        else:
            raise ValueError(f"Unsupported model: {model}")

# Create singleton instance
sentiment_analyzer = SentimentAnalyzer() 