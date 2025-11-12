import re
from typing import Tuple

class EmailClassifier:
    """
    Classifies email intent with confidence score.
    Uses keyword-based classification with confidence calculation.
    Can be extended to use AI models (OpenAI, etc.) in production.
    """

    INTENT_KEYWORDS = {
        "billing": [
            "invoice", "payment", "charge", "bill", "refund", "subscription",
            "credit card", "account balance", "receipt", "pricing", "cost",
            "pay", "paid", "overcharge", "unauthorized charge"
        ],
        "support": [
            "help", "assistance", "how to", "can't", "cannot", "unable",
            "issue", "problem", "question", "confused", "don't understand",
            "need help", "support", "guide", "tutorial", "explain"
        ],
        "bug": [
            "error", "crash", "broken", "not working", "bug", "glitch",
            "fail", "failure", "incorrect", "wrong", "doesn't work",
            "stopped working", "exception", "malfunction", "defect"
        ],
        "feature": [
            "feature request", "enhancement", "suggestion", "would like",
            "wish", "could you add", "implement", "new feature", "improve",
            "add support for", "integration", "capability", "functionality"
        ]
    }

    LOW_CONFIDENCE_THRESHOLD = 0.4

    def classify(self, subject: str, content: str) -> Tuple[str, float, bool]:
        """
        Classify email intent and return (intent, confidence, needs_review).

        Args:
            subject: Email subject line
            content: Email body content

        Returns:
            Tuple of (intent, confidence_score, needs_review)
        """
        text = f"{subject} {content}".lower()

        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = 0
            matches = 0
            for keyword in keywords:
                if keyword in text:
                    matches += 1
                    # Weight matches in subject higher
                    if keyword in subject.lower():
                        score += 2
                    else:
                        score += 1

            # Normalize score
            if matches > 0:
                scores[intent] = min(score / (len(keywords) * 0.5), 1.0)
            else:
                scores[intent] = 0.0

        # Get highest scoring intent
        if not scores or max(scores.values()) == 0:
            # Default to support if no keywords match
            return "support", 0.3, True

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]
        needs_review = confidence < self.LOW_CONFIDENCE_THRESHOLD

        return best_intent, round(confidence, 2), needs_review

    def extract_info(self, content: str) -> dict:
        """
        Extract useful information from email content for placeholder resolution.

        Returns:
            Dictionary with extracted information (name, order_id, etc.)
        """
        info = {}

        # Extract name (simple pattern: looks for "My name is X" or "I'm X")
        name_patterns = [
            r"my name is ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            r"i'?m ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            r"this is ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                info['name'] = match.group(1)
                break

        # Extract order ID (patterns like: #12345, order 12345, ORDER-12345)
        order_patterns = [
            r"order[#:\s]+([A-Z0-9-]+)",
            r"#([0-9]{4,})",
            r"order\s+number[#:\s]+([A-Z0-9-]+)",
        ]
        for pattern in order_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                info['order_id'] = match.group(1)
                break

        # Extract email address (if different from sender)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, content)
        if email_match:
            info['email'] = email_match.group(0)

        return info
