"""
Utility functions for the AI engine.
OpenAI API helpers, text preprocessing, etc.
Will be implemented in Phase 8.
"""


def preprocess_text(text: str) -> str:
    """Clean and normalize complaint text for classification."""
    if not text:
        return ''
    # Basic preprocessing — will be enhanced with NLP in Phase 8
    text = text.strip().lower()
    return text
